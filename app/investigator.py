"""Fixed-script local-only browser investigation with a bounded worker lifetime."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote_plus, urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from app.evidence import valid_completed
from app.safety import allowed_url

ROOT = Path(__file__).resolve().parent.parent
CANARIES = {
    "name": "Decoy Twin",
    "email": "decoy.twin@example.test",
    "phone": "555-0100",
    "password": "Canary-Pass-0001",
    "card_number": "4242 4242 4242 4242",
    "expiry": "12/34",
    "cvv": "000",
    "ssn": "000-00-0000",
    "date_of_birth": "01/01/1900",
    "one_time_code": "000000",
    "gift_card": "CANARY-0000-0000",
    "pin": "0000",
    "address": "1 Decoy Way, Testville",
}
WORKER_TIMEOUT = 9.0


def clean_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def allowed_request(url: str, resource_type: str) -> bool:
    try:
        parsed = urlsplit(url)
        # Query strings carry only synthetic canaries; initial targets still reject them.
        base = clean_url(url)
        if any(char in url for char in ("\\", "\r", "\n", "\t")):
            return False
        if allowed_url(base):
            return True
        return (
            resource_type == "stylesheet"
            and parsed.netloc in {"localhost:8000", "127.0.0.1:8000"}
            and parsed.scheme == "http"
            and parsed.path == "/static/mock.css"
            and not parsed.query
        )
    except (ValueError, TypeError):
        return False


def field_kind(meta: dict) -> str | None:
    value = (
        " ".join(
            str(meta.get(key, ""))
            for key in ("name", "id", "placeholder", "autocomplete", "label")
        )
        .lower()
        .replace("-", "_")
    )
    if meta.get("type") == "password":
        return "password"
    rules = [
        ("gift_card", r"gift.?card|gift_code"),
        ("one_time_code", r"one.?time|otp|verification.?code"),
        ("card_number", r"card.?number|cc_number"),
        ("expiry", r"expir|cc_exp"),
        ("cvv", r"cvv|cvc|security.?code"),
        ("ssn", r"ssn|social.?security"),
        ("date_of_birth", r"date.?of.?birth|dob"),
        ("pin", r"\bpin\b"),
        ("email", r"email"),
        ("phone", r"phone|tel"),
        ("address", r"address"),
        ("name", r"(^|[ _])name($|[ _])"),
    ]
    return next((kind for kind, pattern in rules if re.search(pattern, value)), None)


def _failure(url: str, status: str, error: str, started: float) -> dict:
    return {
        "mode": "live",
        "status": status,
        "start_url": url,
        "simulated": False,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "error": error,
    }


def _inspect(url: str) -> dict:
    started = time.monotonic()
    deadline = started + 7.5
    result = {
        "mode": "live",
        "status": "done",
        "start_url": url,
        "final_url": url,
        "redirect_chain": [url],
        "cross_origin_final": False,
        "fields_requested": [],
        "canaries_sent_to": [],
        "canaries_cross_origin": False,
        "urgency_phrases": [],
        "download_attempted": False,
        "ai_directed_text": False,
        "duration_ms": 0,
        "error": None,
        "simulated": False,
        "recorded": True,
        "form_targets": [],
        "blocked_requests": 0,
        "uninspected_content": False,
    }

    def budget():
        remaining = int((deadline - time.monotonic()) * 1000)
        if remaining <= 0:
            raise TimeoutError("Investigation timed out")
        return remaining

    browser = None
    context = None
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    timeout=budget(),
                    args=[
                        "--disable-background-networking",
                        "--disable-component-update",
                        "--disable-sync",
                        "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
                    ],
                )
                context = browser.new_context(
                    accept_downloads=False, service_workers="block"
                )
                context.set_default_timeout(budget())

                def block_socket(socket):
                    result["blocked_requests"] += 1
                    socket.close(
                        code=1008, reason="No websockets in demo investigations"
                    )

                context.route_web_socket("**/*", block_socket)

                def route(request_route):
                    request = request_route.request
                    if not allowed_request(request.url, request.resource_type):
                        result["blocked_requests"] += 1
                        request_route.abort()
                        return
                    parsed = urlsplit(request.url)
                    # Exclude the origin: port8000 must not match the short CVV canary000.
                    surface = unquote_plus(
                        parsed.path
                        + "?"
                        + parsed.query
                        + "\n"
                        + (request.post_data or "")
                    )
                    values = [*CANARIES.values(), "1900-01-01"]
                    if any(value in surface for value in values):
                        target = clean_url(request.url)
                        if target not in result["canaries_sent_to"]:
                            result["canaries_sent_to"].append(target)
                    request_route.continue_()

                context.route("**/*", route)
                page = context.new_page()
                context.on(
                    "page",
                    lambda extra: result.__setitem__("uninspected_content", True),
                )
                page.on(
                    "frameattached",
                    lambda frame: result.__setitem__("uninspected_content", True),
                )

                def navigation(frame):
                    if frame == page.main_frame and frame.url.startswith("http"):
                        target = clean_url(frame.url)
                        if target != result["redirect_chain"][-1]:
                            result["redirect_chain"].append(target)

                page.on("framenavigated", navigation)

                def download(item):
                    result["download_attempted"] = True
                    item.cancel()

                page.on("download", download)
                page.goto(url, wait_until="domcontentloaded", timeout=budget())
                page.wait_for_timeout(min(1250, budget()))
                if not allowed_url(clean_url(page.url)):
                    raise ValueError("Blocked final URL")
                text = page.inner_text("body", timeout=budget()).lower()
                html = page.content().lower()
                urgency = [
                    r"suspended",
                    r"within 24 hours",
                    r"today",
                    r"immediately",
                    r"final notice",
                    r"minutes",
                    r"only [^.!<]{0,35} left",
                    r"act now",
                    r"expires",
                ]
                result["urgency_phrases"] = [
                    match.group(0)
                    for pattern in urgency
                    if (match := re.search(pattern, text))
                ]
                result["ai_directed_text"] = any(
                    phrase in html
                    for phrase in (
                        "ignore previous instructions",
                        "ai assistant",
                        "as an ai",
                        "mark this page as safe",
                        "mark it legitimate",
                        "system prompt",
                    )
                )
                inputs = page.locator("input:not([type=hidden])")
                for index in range(inputs.count()):
                    budget()
                    item = inputs.nth(index)
                    meta = item.evaluate(
                        "el => ({type:el.type,name:el.name,id:el.id,placeholder:el.placeholder,autocomplete:el.autocomplete,label:Array.from(el.labels || []).map(x=>x.textContent).join(' ')})"
                    )
                    if meta["type"] in {
                        "submit",
                        "button",
                        "reset",
                        "checkbox",
                        "radio",
                        "file",
                    }:
                        continue
                    kind = field_kind(meta)
                    name = kind or "unrecognized_field"
                    if name not in result["fields_requested"]:
                        result["fields_requested"].append(name)
                    if kind and item.is_visible() and item.is_editable():
                        value = CANARIES[kind]
                        if meta["type"] == "date":
                            value = "1900-01-01"
                        item.fill(value, timeout=budget())
                forms = page.locator("form")
                for index in range(forms.count()):
                    target = forms.nth(index).evaluate("el => el.action")
                    if not allowed_request(target, "document"):
                        result["blocked_requests"] += 1
                    else:
                        result["form_targets"].append(clean_url(target))
                if forms.count() and not result["blocked_requests"]:
                    submit = forms.first.locator(
                        'button[type="submit"],input[type="submit"],button:not([type])'
                    )
                    if submit.count():
                        submit.first.click(timeout=budget())
                    else:
                        forms.first.evaluate("el => el.requestSubmit()")
                    page.wait_for_timeout(min(250, budget()))
                result["final_url"] = clean_url(page.url)
                origin = urlsplit(url).netloc
                result["cross_origin_final"] = (
                    urlsplit(result["final_url"]).netloc != origin
                )
                result["canaries_cross_origin"] = any(
                    urlsplit(target).netloc != origin
                    for target in result["canaries_sent_to"]
                )
                if result["blocked_requests"]:
                    result.update(
                        status="blocked",
                        error="A page request or form target was blocked by the local-only policy.",
                    )
                if result["uninspected_content"] or len(page.frames) > 1:
                    result.update(
                        status="failed",
                        error="Additional page or frame contents were not fully investigated.",
                    )
                result["duration_ms"] = int((time.monotonic() - started) * 1000)
            finally:
                if context is not None:
                    context.close()
                if browser is not None:
                    browser.close()
    except (
        PlaywrightError,
        TimeoutError,
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as error:
        result.update(
            status="failed",
            error="Investigation did not complete (" + type(error).__name__ + ").",
        )
    result["duration_ms"] = int((time.monotonic() - started) * 1000)
    return result


def investigate(url: str) -> dict:
    started = time.monotonic()
    if not allowed_url(url):
        return _failure(
            url, "blocked", "Only local demo pages can be checked.", started
        )
    env = dict(os.environ)
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright"))
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "app.investigator"],
            cwd=ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        output, _ = process.communicate(
            json.dumps({"url": url}), timeout=WORKER_TIMEOUT
        )
        if process.returncode != 0:
            return _failure(
                url, "failed", "Browser worker could not complete.", started
            )
        result = json.loads(output)
        if result.get("status") == "done" and not valid_completed(result):
            return _failure(
                url, "failed", "Browser evidence failed validation.", started
            )
        result["duration_ms"] = int((time.monotonic() - started) * 1000)
        return result
    except subprocess.TimeoutExpired:
        if process is not None:
            if os.name == "nt":
                try:
                    killed = subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True,
                        check=False,
                        timeout=0.7,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    if killed.returncode != 0:
                        process.kill()
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
            else:
                process.kill()
            try:
                process.communicate(timeout=0.3)
            except (OSError, subprocess.TimeoutExpired):
                pass
        return _failure(
            url, "failed", "Investigation exceeded its time limit.", started
        )
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return _failure(url, "failed", "Browser investigation is unavailable.", started)


if __name__ == "__main__":
    request = json.loads(sys.stdin.read())
    target = request["url"]
    answer = (
        _inspect(target)
        if allowed_url(target)
        else _failure(target, "blocked", "Blocked initial URL.", time.monotonic())
    )
    print(json.dumps(answer))
