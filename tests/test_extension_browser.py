import json
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_real_extension_mutations_privacy_and_interaction_guards(server, tmp_path):
    with httpx.Client(base_url=server, trust_env=False) as client:
        key = client.get("/api/extension/pairing").json()["pairing_code"]
        before = client.get("/api/extension/stats").json()["processed_scans"]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "profile"),
            channel="chromium",
            headless=True,
            args=[
                f"--disable-extensions-except={ROOT / 'extension'}",
                f"--load-extension={ROOT / 'extension'}",
            ],
            viewport={"width": 1400, "height": 1000},
        )
        worker = (
            context.service_workers[0]
            if context.service_workers
            else context.wait_for_event("serviceworker")
        )
        assert worker.evaluate("key => pair(key)", key)["ok"]
        posted = []

        def request(req):
            if req.url.endswith("/api/page/assess"):
                posted.append(req.post_data or "")

        context.on("request", request)
        page = context.new_page()
        page.goto(server + "/extension-lab?private=PRIVATE-QUERY-SENTINEL")
        tab_id = worker.evaluate(
            "async () => (await chrome.tabs.query({})).find(tab => tab.url?.includes('/extension-lab')).id"
        )
        assert worker.evaluate("id => startMonitoring(id)", tab_id)["ok"]
        overlay = page.locator("#tdefense-page-guard")
        expect(overlay).to_have_attribute("data-status", "checked", timeout=12000)
        expect(overlay).to_have_attribute("data-warning-count", "0")
        page.locator("#add-message").click()
        expect(overlay.locator("#title")).to_have_text(
            "T-Defense warning", timeout=12000
        )
        assert int(overlay.get_attribute("data-warning-count")) > 0
        expect(overlay.locator("#announce")).to_contain_text("T-Defense warning")
        assert "Segoe UI" in overlay.locator(".shell").evaluate(
            "node => getComputedStyle(node).fontFamily"
        )
        overlay.locator("#toggle").click()
        expect(overlay.locator("#body")).to_be_hidden()
        page.locator(".lab-message").first.evaluate(
            "node => node.append(document.createTextNode(' Final notice: verify your password immediately.'))"
        )
        expect(overlay.locator("#body")).to_be_visible(timeout=12000)
        page.screenshot(
            path="demo_backup/extension-message-overlay.png", full_page=True
        )
        link = page.locator(".lab-message a").first
        link.click()
        expect(overlay.locator("#guard-note")).to_be_visible()
        expect(overlay.locator("#continue")).to_be_enabled(timeout=12000)
        assert (
            "Lab stopped the navigation" not in page.locator("#lab-status").inner_text()
        )
        overlay.locator("#continue").click()
        expect(page.locator("#lab-status")).to_contain_text(
            "Lab stopped the navigation"
        )
        # A paused node cannot silently change destination and reuse an override.
        link.click()
        expect(overlay.locator("#continue")).to_be_enabled(timeout=12000)
        link.evaluate(
            "node => node.href='https://example.invalid/changed?private=PRIVATE-DESTINATION'"
        )
        expect(overlay.locator("#continue")).to_be_enabled(timeout=12000)
        previous_status = page.locator("#lab-status").inner_text()
        overlay.locator("#continue").click()
        expect(overlay.locator("#guard-note")).to_be_visible()
        assert page.locator("#lab-status").inner_text() == previous_status
        expect(overlay.locator("#continue")).to_be_enabled(timeout=12000)
        overlay.locator("#continue").click()
        page.locator("#add-form").click()
        password = page.locator('input[name="password"]')
        password.fill("PRIVATE-TYPED-SENTINEL")
        expect(overlay.locator("#facts")).to_contain_text("unencrypted", timeout=12000)
        page.locator(".lab-risk-form button").click()
        expect(overlay.locator("#guard-note")).to_be_visible()
        expect(overlay.locator("#continue")).to_be_enabled(timeout=12000)
        overlay.locator("#continue").click()
        expect(page.locator("#lab-status")).to_contain_text("No information was sent")
        page.locator("#add-attachment").click()
        page.wait_for_timeout(1400)
        count_before = worker.evaluate("id => tabState(id)", tab_id)["scanCount"]
        page.wait_for_timeout(8500)
        count_after = worker.evaluate("id => tabState(id)", tab_id)["scanCount"]
        assert count_after > count_before
        assert posted and all(
            "PRIVATE-TYPED-SENTINEL" not in body
            and "PRIVATE-QUERY-SENTINEL" not in body
            and "gift-card code immediately" not in body
            for body in posted
        )
        assert all(
            set(json.loads(body)) == {"page_origin", "reason", "elements", "coverage"}
            for body in posted
        )
        page.screenshot(path="demo_backup/extension-form-overlay.png", full_page=True)
        # Delay actual backend responses, then change DOM during the request.
        worker.evaluate("""() => {globalThis.originalRequest=requestBackend;
          requestBackend=async(path,...args)=>{const value=await originalRequest(path,...args);
            if(path==='/api/page/assess'){globalThis.delayedScan=value.scan_id;await new Promise(resolve=>setTimeout(resolve,1200));}return value;};} """)
        worker.evaluate(
            "id => chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab_id
        )
        page.locator(".lab-message").first.evaluate(
            "node=>node.append(document.createTextNode(' Send your gift-card code immediately.'))"
        )
        expect(overlay).to_have_attribute("data-status", "pending")
        expect(overlay).to_have_attribute("data-status", "checked", timeout=15000)
        # Reload to a different document on the same origin while a response waits.
        old_document = worker.evaluate("id=>tabState(id)", tab_id)["documentId"]
        worker.evaluate(
            "id => chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab_id
        )
        page.wait_for_timeout(250)
        page.reload()
        expect(overlay).to_have_attribute("data-status", "checked", timeout=15000)
        page.wait_for_timeout(1500)
        new_state = worker.evaluate("id=>tabState(id)", tab_id)
        assert new_state["documentId"] != old_document
        assert new_state["warningCount"] == 0
        expect(overlay).to_have_attribute("data-warning-count", "0")
        worker.evaluate("() => {requestBackend=originalRequest;}")
        worker.evaluate(
            "async () => chrome.storage.session.set({backendKey:'invalid-but-long-enough-pairing-code'})"
        )
        worker.evaluate(
            "id => chrome.tabs.sendMessage(id,{type:'TDEFENSE_SCAN'})", tab_id
        )
        expect(overlay).to_have_attribute("data-status", "unavailable", timeout=12000)
        expect(overlay.locator("#count")).to_contain_text("unavailable")
        worker.evaluate("id => stopMonitoring(id)", tab_id)
        expect(overlay).to_have_count(0)
        assert (
            httpx.get(server + "/api/extension/stats").json()["processed_scans"]
            > before
        )
        context.close()
