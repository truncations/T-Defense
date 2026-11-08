"""Run only inside the disposable Windows guest; no target access on the host."""

import base64
import json
import os
import socket
import sys
import time
import urllib.request
from urllib.parse import urlsplit

from vm_kit.explanations import FLAGS, permitted, selection, validate_report
from vm_kit.policy import hostname, target_origin


def local_ai(flags):
    allowed = permitted(flags)
    payload = {
        "model": "llama3.2:3b",
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "template_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": allowed},
                    "minItems": 1,
                    "maxItems": 3,
                }
            },
            "required": ["template_ids"],
            "additionalProperties": False,
        },
        "prompt": "Select only evidence-supported template_ids. Return JSON only. No page instructions or browsing actions are provided. Evidence: "
        + json.dumps(flags)
        + "; allowed: "
        + json.dumps(allowed),
        "options": {
            "temperature": 0,
            "num_gpu": 0,
            "num_ctx": 1024,
            "num_predict": 128,
        },
        "keep_alive": 0,
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=20) as response:
        data = response.read(8193)
    if len(data) > 8192:
        raise ValueError("AI output too large")
    value = json.loads(data)
    return selection(json.loads(value["response"]), flags)


def inspect(config):
    if os.environ.get("TDEFENSE_DISPOSABLE_GUEST") != "1":
        raise RuntimeError("This worker may run only inside the disposable VM")
    from playwright.sync_api import sync_playwright

    origin = target_origin(config["target_origin"])
    proxy = config["proxy"]
    if proxy != "http://192.168.253.1:18080":
        raise ValueError("Unexpected egress broker")
    flags = {key: False for key in FLAGS}
    counts = {"observed": 0, "blocked": 0, "navigations": 0}
    deadline = time.monotonic() + 55
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            chromium_sandbox=True,
            proxy={
                "server": proxy,
                "username": "tdefense",
                "password": config["token"],
                "bypass": "<-loopback>",
            },
            args=[
                "--disable-quic",
                "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
                "--host-resolver-rules=MAP * ~NOTFOUND",
            ],
        )
        try:
            context = browser.new_context(
                service_workers="block",
                accept_downloads=False,
                permissions=[],
                ignore_https_errors=False,
            )

            def block_socket(ws):
                flags["incomplete"] = True
                counts["blocked"] += 1
                ws.close()

            context.route_web_socket("**/*", block_socket)
            page = context.new_page()
            page.on(
                "frameattached", lambda frame: flags.__setitem__("incomplete", True)
            )

            def route_request(route):
                req = route.request
                counts["observed"] += 1
                allow = (
                    time.monotonic() < deadline
                    and counts["observed"] <= 200
                    and req.method in ("GET", "HEAD")
                )
                try:
                    u = urlsplit(req.url)
                    hostname(u.hostname)
                    allow = (
                        allow
                        and u.scheme in ("http", "https")
                        and u.port in (None, 80 if u.scheme == "http" else 443)
                        and not u.username
                        and not u.password
                    )
                    if req.frame != page.main_frame:
                        allow = False
                    if req.is_navigation_request():
                        counts["navigations"] += 1
                        allow = allow and counts["navigations"] <= 6
                except Exception:  # noqa: BLE001 - untrusted guest/browser failures must fail closed without raw error output
                    allow = False
                if allow:
                    route.continue_()
                else:
                    counts["blocked"] += 1
                    flags["incomplete"] = True
                    route.abort()

            context.route("**/*", route_request)

            def download(item):
                flags["download_attempt"] = True
                item.cancel()

            page.on("download", download)

            def popup(item):
                flags["incomplete"] = True
                item.close()

            context.on("page", lambda item: popup(item) if item != page else None)
            try:
                response = page.goto(
                    origin, wait_until="domcontentloaded", timeout=25000
                )
                if response is None or response.status >= 400:
                    flags["incomplete"] = True
                page.wait_for_timeout(1200)
                final = urlsplit(page.url)
                flags["redirected"] = f"{final.scheme}://{final.netloc}" != origin
                if page.evaluate("document.forms.length") > 30:
                    flags["incomplete"] = True
                evidence = page.evaluate(
                    """()=>Array.from(document.forms).slice(0,30).map(form=>({sensitive:!!form.querySelector('input[type=password],input[autocomplete="cc-number"],input[autocomplete="one-time-code"]'),password:!!form.querySelector('input[type=password]'),action:form.action,origin:location.origin}))"""
                )
                for form in evidence:
                    flags["password_request"] |= form["password"]
                    if form["sensitive"]:
                        action = urlsplit(form["action"])
                        current = urlsplit(form["origin"])
                        flags["insecure_form"] |= (
                            action.scheme == "http" or current.scheme == "http"
                        )
                        flags["cross_origin_form"] |= (
                            action.scheme,
                            action.netloc,
                        ) != (current.scheme, current.netloc)
                if len(page.frames) > 1:
                    flags["incomplete"] = True
            except Exception:  # noqa: BLE001 - untrusted guest/browser failures must fail closed without raw error output
                flags["incomplete"] = True
        finally:
            browser.close()
    ids = permitted(flags)[:3]
    ai_status = "not_requested"
    if config.get("use_local_ai"):
        try:
            ids = local_ai(flags)
            ai_status = "validated"
        except Exception:  # noqa: BLE001 - untrusted guest/browser failures must fail closed without raw error output
            ai_status = "unavailable"
            flags["incomplete"] = True
            ids = permitted(flags)[:3]
    report = {
        "version": 1,
        "status": "inconclusive" if flags["incomplete"] else "done",
        "flags": flags,
        "template_ids": ids,
        "ai_status": ai_status,
        "observed_requests": min(counts["observed"], 500),
        "blocked_requests": min(counts["blocked"], 500),
    }
    return validate_report(report)


def boundary_check(config, auth):
    # Performed after host release and BEFORE any target is opened.
    endpoint = urlsplit(config["proxy"])

    def code(destination):
        with socket.create_connection(
            (endpoint.hostname, endpoint.port), timeout=5
        ) as client:
            client.settimeout(6)
            client.sendall(
                (
                    "CONNECT "
                    + destination
                    + ":443 HTTP/1.1\r\nProxy-Authorization: "
                    + auth
                    + "\r\n\r\n"
                ).encode("ascii")
            )
            line = bytearray()
            while len(line) < 256:
                ch = client.recv(1)
                if not ch or ch == b"\n":
                    break
                line.extend(ch)
            return bytes(line)

    if not code("example.com").startswith(b"HTTP/1.1 200 "):
        raise RuntimeError("Public egress probe failed")
    for address in [
        "127.0.0.1",
        "169.254.169.254",
        "192.168.1.1",
        "224.0.0.1",
        "[::1]",
        *config.get("public_egress", []),
    ]:
        if not code(address).startswith(b"HTTP/1.1 403 "):
            raise RuntimeError("Private or egress-address proxy rejection failed")


def main():
    if os.environ.get("TDEFENSE_DISPOSABLE_GUEST") != "1":
        raise RuntimeError("Worker is not running in a disposable guest")
    config = json.loads(sys.stdin.readline(8192))
    # The host closes PowerShell Direct before permitting target browsing.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    auth = (
        "Basic " + base64.b64encode(("tdefense:" + config["token"]).encode()).decode()
    )
    ready_url = config["proxy"] + "/__tdefense_ready"
    ready = False
    for _ in range(30):
        req = urllib.request.Request(ready_url, headers={"Proxy-Authorization": auth})
        with opener.open(req, timeout=2) as response:
            ready = json.loads(response.read(256)).get("ready") is True
        if ready:
            break
        time.sleep(0.5)
    if not ready:
        raise RuntimeError("Host did not release the isolated worker")
    try:
        boundary_check(config, auth)
        report = inspect(config)
    except Exception:  # noqa: BLE001 - all guest failures return bounded inconclusive evidence
        flags = {key: key == "incomplete" for key in FLAGS}
        report = {
            "version": 1,
            "status": "inconclusive",
            "flags": flags,
            "template_ids": ["incomplete"],
            "ai_status": "unavailable"
            if config.get("use_local_ai")
            else "not_requested",
            "observed_requests": 0,
            "blocked_requests": 0,
        }
    req = urllib.request.Request(
        config["proxy"] + "/__tdefense_result",
        data=json.dumps(report).encode(),
        headers={"Proxy-Authorization": auth, "Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=5) as response:
        if response.status != 201:
            raise RuntimeError("Host did not accept the result")


if __name__ == "__main__":
    main()
