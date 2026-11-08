"""Actual MV3 -> FastAPI tests, with only the external VirusTotal transport mocked."""

import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import uvicorn
from playwright.sync_api import expect, sync_playwright

from app import page_guard, reputation
from app.main import app

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def reputation_server(monkeypatch):
    try:
        httpx.get("http://localhost:8000/api/health", timeout=0.3)
    except httpx.HTTPError:
        pass
    else:
        pytest.fail("Stop the manual backend before tests; port8000 is in use")
    state = {"mode": "reports", "requests": []}

    def handler(request):
        state["requests"].append(request)
        assert request.url.host == "www.virustotal.com" and request.method == "GET"
        if state["mode"] == "quota":
            return httpx.Response(429)
        if state["mode"] == "timeout":
            raise httpx.ReadTimeout("Synthetic provider timeout", request=request)
        domain = request.url.path.split("/")[-1]
        return httpx.Response(
            200,
            json={
                "data": {
                    "type": "domain",
                    "id": domain,
                    "attributes": {
                        "last_analysis_date": int(time.time()),
                        "last_analysis_stats": {
                            "malicious": 3 if domain == "public-risk.com" else 0,
                            "suspicious": 0,
                            "harmless": 40,
                            "undetected": 20,
                        },
                    },
                }
            },
        )

    client_class = httpx.AsyncClient
    monkeypatch.setattr(
        reputation,
        "httpx",
        SimpleNamespace(
            HTTPError=httpx.HTTPError,
            AsyncClient=lambda **kwargs: client_class(
                **kwargs, transport=httpx.MockTransport(handler)
            ),
        ),
    )
    monkeypatch.setattr(
        reputation,
        "api_key",
        lambda: "" if state["mode"] == "no_key" else "synthetic-test-key",
    )

    def reset(mode):
        state["mode"] = mode
        monkeypatch.setattr(page_guard, "REPUTATION", reputation.DomainReputation())

    reset("reports")
    server = uvicorn.Server(
        uvicorn.Config(
            app, host="127.0.0.1", port=8000, log_level="error", access_log=False
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        yield state, reset
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        assert not thread.is_alive()


def test_email_priority_live_reputation_and_persistent_review(
    reputation_server, tmp_path
):
    state, reset = reputation_server
    key = httpx.get("http://localhost:8000/api/extension/pairing").json()[
        "pairing_code"
    ]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "email-profile"),
            channel="chromium",
            headless=True,
            args=[
                f"--disable-extensions-except={ROOT / 'extension'}",
                f"--load-extension={ROOT / 'extension'}",
            ],
            viewport={"width": 1400, "height": 1000},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            worker.evaluate("key=>pair(key)", key)
            page = context.new_page()
            navigation = "".join(
                f'<a href="/navigation/{i}">Folder{i}</a> ' for i in range(260)
            )
            html = f"""<!doctype html><html><body><nav style="height:40px;overflow:auto">{navigation}</nav>
            <h1>Synthetic email/provider fixture · VirusTotal responses mocked</h1>
            <section data-message-id="synthetic-message"><div class="a3s" style="padding:30px">
            <p>EMAIL-TEXT-SENTINEL Please verify your account to continue.</p>
            <a id="email-link" href="https://www.google.com/url?q=https%3A%2F%2Fpublic-risk.com%2Fsession%3Ftoken%3DPRIVATE-PATH">Review account</a>
            </div></section></body></html>"""
            page.route(
                "**/email-fixture",
                lambda route: route.fulfill(content_type="text/html", body=html),
            )
            posted = []
            context.on(
                "request",
                lambda req: (
                    posted.append(req.post_data or "")
                    if req.url.endswith("/api/page/assess")
                    else None
                ),
            )
            page.goto("http://localhost:8000/email-fixture")
            tab = worker.evaluate(
                "async()=> (await chrome.tabs.query({})).find(tab=>tab.url?.includes('/email-fixture')).id"
            )
            worker.evaluate("id=>startMonitoring(id)", tab)
            overlay = page.locator("#tdefense-page-guard")
            expect(overlay).to_have_attribute("data-status", "partial", timeout=12000)
            assert not state["requests"], "No provider lookup without tab opt-in"
            expect(overlay.locator("#facts")).to_contain_text("account", timeout=12000)
            snapshot = worker.evaluate(
                """async id=>(await chrome.scripting.executeScript({target:{tabId:id},func:()=>TDefenseSnapshot.collect('manual').snapshot}))[0].result""",
                tab,
            )
            first_link = next(
                item for item in snapshot["elements"] if item["kind"] == "link"
            )
            assert (
                first_link["target_origin"] == "https://public-risk.com"
                and first_link["email_context"]
                and first_link["wrapped_destination"]
            )
            worker.evaluate(
                "id=>handle({type:'REPUTATION',tabId:id,enabled:true},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
                tab,
            )
            expect(overlay.locator("#facts")).to_contain_text(
                "VirusTotal reports 3 malicious", timeout=12000
            )
            expect(overlay.locator("#reputation")).to_contain_text("public-risk.com")
            page.locator("#email-link").dispatch_event("contextmenu")
            expect(overlay.locator("#review-note")).to_contain_text(
                "Reviewing this finding"
            )
            overlay.locator("#locate").click()
            expect(overlay.locator("#review-note")).to_contain_text(
                "Reviewing this finding"
            )
            page.evaluate("document.body.append(document.createElement('aside'))")
            expect(overlay).to_have_attribute("data-status", "pending")
            expect(overlay.locator("#locate")).to_be_enabled()
            overlay.locator("#locate").click()
            expect(overlay.locator("#facts")).to_contain_text("VirusTotal")
            page.locator("#email-link").evaluate("node=>node.remove()")
            expect(overlay.locator("#review-note")).to_contain_text(
                "no longer on the page", timeout=12000
            )
            expect(overlay.locator("#title")).to_have_text(
                "Previously observed warning"
            )
            overlay.locator("#clear-review").click()
            page.locator(".a3s").evaluate(
                'node=>node.innerHTML=\'<p>Hello, ordinary content.</p><a id="clean-link" href="https://public-clean.com/hello">Read more</a>\''
            )
            reset("no_key")
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab
            )
            expect(overlay.locator("#reputation")).to_contain_text(
                "key is not configured", timeout=12000
            )
            expect(overlay.locator("#count")).to_contain_text("Limited checks")
            for mode, text in [
                ("quota", "quota reached"),
                ("timeout", "unavailable"),
                ("reports", "No reported detections"),
            ]:
                reset(mode)
                page.locator("#clean-link").hover()
                worker.evaluate(
                    "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab
                )
                expect(overlay.locator("#reputation")).to_contain_text(
                    text, timeout=12000
                )
                if mode != "reports":
                    expect(overlay.locator("#count")).to_contain_text("Limited checks")
            # Opt-out during an in-flight check must stay off after its response.
            worker.evaluate("""()=>{globalThis.originalRequest=requestBackend;
              requestBackend=async(...args)=>{const value=await originalRequest(...args);
                if(args[0]==='/api/page/assess'){globalThis.testRequestPending=true;await new Promise(resolve=>setTimeout(resolve,1200));}return value;};}""")
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab
            )
            for _ in range(60):
                if worker.evaluate("()=>!!globalThis.testRequestPending"):
                    break
                page.wait_for_timeout(50)
            assert worker.evaluate("()=>!!globalThis.testRequestPending")
            worker.evaluate(
                "id=>handle({type:'REPUTATION',tabId:id,enabled:false},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
                tab,
            )
            expect(overlay.locator("#reputation")).to_contain_text(
                "checks are off", timeout=12000
            )
            assert (
                worker.evaluate("id=>tabState(id)", tab)["reputationEnabled"] is False
            )
            assert worker.evaluate("id=>tabState(id)", tab)["active"] is True
            worker.evaluate("()=>{requestBackend=originalRequest;}")
            assert posted and all(
                "PRIVATE-PATH" not in body
                and "EMAIL-TEXT-SENTINEL" not in body
                and "synthetic-test-key" not in body
                for body in posted
            )
            assert all(
                set(json.loads(body))
                == {"page_origin", "reason", "elements", "coverage"}
                for body in posted
            )
            assert all(
                request.url.host == "www.virustotal.com" and not request.url.query
                for request in state["requests"]
            )
            # Stop must also cancel a Start still awaiting its backend connection.
            worker.evaluate(
                """id=>{globalThis.connectOriginal=requestBackend;
              requestBackend=async(...args)=>{const value=await connectOriginal(...args);
                if(args[0]==='/api/extension/connect'){globalThis.connectPending=true;await new Promise(resolve=>setTimeout(resolve,1200));}return value;};
              globalThis.startAttempt=startMonitoring(id).then(()=>({started:true}),error=>({error:error.message}));}""",
                tab,
            )
            for _ in range(60):
                if worker.evaluate("()=>!!globalThis.connectPending"):
                    break
                page.wait_for_timeout(50)
            assert worker.evaluate("()=>!!globalThis.connectPending")
            worker.evaluate("id=>stopMonitoring(id)", tab)
            attempt = worker.evaluate("async()=>await startAttempt")
            assert "stopped" in attempt["error"]
            assert worker.evaluate("id=>tabState(id)", tab)["active"] is False
            expect(overlay).to_have_count(0)
            worker.evaluate("()=>{requestBackend=connectOriginal;}")
        finally:
            context.close()
