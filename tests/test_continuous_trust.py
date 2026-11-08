"""Real MV3 persistence, site transitions, current findings, and local IndexedDB trust."""

import hashlib
import json
import shutil
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from tests.test_social_engineering import CRYPTO

ROOT = Path(__file__).resolve().parent.parent


def test_continuous_monitoring_trust_revocation_and_quiet_ui(server, tmp_path):
    key = httpx.get(server + "/api/extension/pairing").json()["pairing_code"]
    extension = tmp_path / "extension"
    shutil.copytree(ROOT / "extension", extension)
    manifest = json.loads((extension / "manifest.json").read_text(encoding="utf8"))
    assert manifest["optional_host_permissions"] == ["http://*/*", "https://*/*"]
    # Headless automation cannot approve Chrome's native optional-host permission prompt.
    manifest["host_permissions"] += manifest.pop("optional_host_permissions")
    (extension / "manifest.json").write_text(json.dumps(manifest), encoding="utf8")
    for name in [
        "background.js",
        "bootstrap.js",
        "trust.js",
        "scanner.js",
        "content.js",
        "popup.js",
    ]:
        assert (
            hashlib.sha256((extension / name).read_bytes()).digest()
            == hashlib.sha256((ROOT / "extension" / name).read_bytes()).digest()
        )
    html = (
        """<!doctype html><meta charset="utf-8"><style>body{font:18px Arial;margin:30px}article{width:650px;max-width:90%;padding:20px;border:1px solid gray}</style><button id="avatar" style="position:fixed;right:15px;top:15px">Profile</button><h1>Synthetic email fixture</h1><article data-tdefense-message="true"><p>"""
        + CRYPTO
        + """</p><a id="risk" href="https://ethereum-bonus.example/rewards?token=PRIVATE-QUERY">Participate here</a></article><p id="status"></p><script>risk.addEventListener('click',e=>{e.preventDefault();document.querySelector('#status').textContent='Synthetic link action reached';});</script>"""
    )
    profile = tmp_path / "profile"
    with sync_playwright() as p:

        def launch():
            return p.chromium.launch_persistent_context(
                str(profile),
                channel="chromium",
                headless=True,
                args=[
                    f"--disable-extensions-except={extension}",
                    f"--load-extension={extension}",
                ],
                viewport={"width": 1400, "height": 1000},
            )

        context = launch()
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            worker.evaluate("key=>pair(key)", key)
            context.route(
                "**/continuous-email",
                lambda route: route.fulfill(content_type="text/html", body=html),
            )
            page = context.new_page()
            page.goto(server + "/continuous-email")
            tab = worker.evaluate(
                "async()=>(await chrome.tabs.query({})).find(tab=>tab.url?.includes('/continuous-email')).id"
            )
            posted = []
            context.on(
                "request",
                lambda req: (
                    posted.append(json.loads(req.post_data))
                    if req.url.endswith("/api/page/assess") and req.post_data
                    else None
                ),
            )
            worker.evaluate("()=>enableEverywhere()")
            ui = page.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-warning-count", "2", timeout=15000)
            page.locator(
                "#avatar"
            ).click()  # compact bottom-right dock leaves Gmail-like profile controls usable
            assert ui.locator(".shell").bounding_box()["y"] > 100
            ui.locator("#risk-indicator").click()
            icon = ui.locator("#risk-indicator").bounding_box()
            glyph = ui.locator("#risk-indicator svg").bounding_box()
            assert (
                abs(icon["x"] + icon["width"] / 2 - glyph["x"] - glyph["width"] / 2) < 1
            )
            assert (
                abs(icon["y"] + icon["height"] / 2 - glyph["y"] - glyph["height"] / 2)
                < 1
            )
            before = ui.locator(".shell").bounding_box()
            ui.locator("#move").focus()
            page.keyboard.press("ArrowLeft")
            page.keyboard.press("ArrowUp")
            moved = ui.locator(".shell").bounding_box()
            assert moved["x"] < before["x"] - 10 and moved["y"] < before["y"] - 10
            handle = ui.locator("#move").bounding_box()
            page.mouse.move(
                handle["x"] + handle["width"] / 2, handle["y"] + handle["height"] / 2
            )
            page.mouse.down()
            page.mouse.move(handle["x"] - 70, handle["y"] - 40, steps=8)
            page.mouse.up()
            dragged = ui.locator(".shell").bounding_box()
            assert dragged["x"] < moved["x"] - 50
            assert worker.evaluate(
                "async()=>!!(await chrome.storage.local.get('panelPosition')).panelPosition"
            )
            ui.locator(".finding-row").first.click()
            # Unchanged checks must not rewrite the list, facts, or visible monitoring footer, or reannounce risks.
            page.evaluate(
                """()=>{const s=document.querySelector('#tdefense-page-guard').shadowRoot;window.quietChanges=[];for(const id of ['findings','facts','activity','announce'])new MutationObserver(()=>quietChanges.push(id)).observe(s.getElementById(id),{subtree:true,childList:true,characterData:true});}"""
            )
            for _ in range(2):
                worker.evaluate(
                    "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})",
                    tab,
                )
                page.wait_for_timeout(800)
            assert page.evaluate("quietChanges") == []
            expect(ui.locator("#risk-indicator")).to_have_class("risk")
            # Trust can only be committed through genuine-toolbar control routes.
            candidate = worker.evaluate(
                "id=>handle({type:'TRUST_PREVIEW',tabId:id},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
                tab,
            )["candidate"]
            assert candidate["kind"] == "message"
            pending = worker.evaluate(
                "async id=>(await chrome.storage.session.get('trustCandidate:'+id))['trustCandidate:'+id]",
                tab,
            )
            assert "preview" not in pending and "EXCLUSIVE" not in json.dumps(pending)
            worker.evaluate(
                "args=>handle({type:'TRUST_SELECTED',tabId:args.id,token:args.token},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
                {"id": tab, "token": candidate["token"]},
            )
            expect(ui).to_have_attribute("data-warning-count", "0", timeout=12000)
            expect(ui.locator(".finding-row")).to_have_count(0)
            assert any(body["coverage"].get("trusted_skipped") == 2 for body in posted)
            saved = worker.evaluate("()=>TrustStore.read()")
            assert len(saved) == 1 and set(saved[0]) == {
                "fingerprint",
                "origin",
                "kind",
                "createdAt",
            }
            assert "PRIVATE-QUERY" not in json.dumps(
                saved
            ) and "EXCLUSIVE" not in json.dumps(saved)
            page.locator("#risk").click()
            expect(page.locator("#status")).to_have_text(
                "Synthetic link action reached"
            )
            expect(ui.locator("#guard-note")).to_be_hidden()
            page.locator("#risk").evaluate(
                "node=>node.href='https://ethereum-bonus.example/changed'"
            )
            expect(ui).to_have_attribute("data-warning-count", "2", timeout=12000)
            page.locator("#risk").evaluate(
                "node=>node.href='https://ethereum-bonus.example/rewards?token=PRIVATE-QUERY'"
            )
            expect(ui).to_have_attribute("data-warning-count", "0", timeout=12000)
            # Another site/new tab is monitored automatically, without pressing Start again.
            context.route(
                "https://second-site.example/**",
                lambda route: route.fulfill(content_type="text/html", body=html),
            )
            second = context.new_page()
            second.goto("https://second-site.example/continuous-email")
            second_ui = second.locator("#tdefense-page-guard")
            expect(second_ui).to_have_attribute(
                "data-warning-count", "2", timeout=15000
            )
            # Same text on another origin is not trusted by a previous site's decision.
            second.goto("https://second-site.example/another")
            expect(second_ui).to_have_attribute(
                "data-warning-count", "2", timeout=15000
            )
            # Closing/hiding a message clears its rows automatically, without Check again.
            second.locator("article").evaluate("node=>node.style.display='none'")
            expect(second_ui.locator(".finding-row")).to_have_count(0, timeout=5000)
            second.locator("article").evaluate("node=>node.style.display='' ")
            expect(second_ui.locator(".finding-row")).to_have_count(2, timeout=12000)
            second.evaluate("location.hash='inbox'")
            second.locator("article").evaluate("node=>node.remove()")
            expect(second_ui.locator(".finding-row")).to_have_count(0, timeout=5000)
            # Supported Gmail Spam-folder context is local; no OCR or account API is used.
            context.route(
                "https://mail.google.com/**",
                lambda route: route.fulfill(
                    content_type="text/html",
                    body='<html><div class="a3s"><img src="data:image/png,synthetic" width="350" height="500"></div></html>',
                ),
            )
            mail = context.new_page()
            mail.goto("https://mail.google.com/mail/u/0/#spam/synthetic-thread")
            mail_ui = mail.locator("#tdefense-page-guard")
            expect(mail_ui).to_have_attribute("data-warning-count", "1", timeout=15000)
            expect(mail_ui.locator("#title")).to_have_text("Possible promotional spam")
            mail.evaluate("location.hash='inbox'")
            expect(mail_ui.locator(".finding-row")).to_have_count(0, timeout=5000)
            # Persistent database survives a page reload and a browser profile restart.
            page.bring_to_front()
            page.reload()
            expect(ui).to_have_attribute("data-warning-count", "0", timeout=15000)
        finally:
            context.close()
        context = launch()
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            assert worker.evaluate("async()=>(await globalSettings()).enabled") is True
            assert len(worker.evaluate("()=>TrustStore.read()")) == 1
            worker.evaluate("key=>pair(key)", key)
            context.route(
                "**/continuous-email",
                lambda route: route.fulfill(content_type="text/html", body=html),
            )
            page = context.new_page()
            page.goto(server + "/continuous-email")
            ui = page.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-warning-count", "0", timeout=15000)
            tab = worker.evaluate(
                "async()=>(await chrome.tabs.query({})).filter(tab=>tab.url?.includes('/continuous-email')).at(-1).id"
            )
            fingerprint = worker.evaluate(
                "async()=>(await TrustStore.read())[0].fingerprint"
            )
            # Revocation cannot be undone by a previously started asynchronous filter.
            worker.evaluate(
                """async id=>chrome.scripting.executeScript({target:{tabId:id},func:()=>{globalThis.filterBeforeRevoke=TDefenseSnapshot.filterTrusted;TDefenseSnapshot.filterTrusted=async(...args)=>{const value=await filterBeforeRevoke(...args);globalThis.filterPending=true;await new Promise(resolve=>setTimeout(resolve,900));return value;};}})""",
                tab,
            )
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})", tab
            )
            for _ in range(50):
                pending = worker.evaluate(
                    """async id=>(await chrome.scripting.executeScript({target:{tabId:id},func:()=>!!globalThis.filterPending}))[0].result""",
                    tab,
                )
                if pending:
                    break
                page.wait_for_timeout(40)
            assert pending
            worker.evaluate(
                "args=>handle({type:'TRUST_DELETE',tabId:args.id,fingerprint:args.fp},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
                {"id": tab, "fp": fingerprint},
            )
            page.locator("#status").evaluate(
                "node=>node.textContent='Waiting for revoked action'"
            )
            page.locator("#risk").click()
            expect(ui.locator("#guard-note")).to_be_visible()
            expect(page.locator("#status")).to_have_text("Waiting for revoked action")
            expect(ui).to_have_attribute("data-warning-count", "2", timeout=15000)
            assert worker.evaluate("()=>TrustStore.read()") == []
            worker.evaluate("()=>stopEverywhere()")
            expect(ui).to_have_count(0)
            assert (
                worker.evaluate(
                    "()=>chrome.scripting.getRegisteredContentScripts({ids:['t-defense-always']})"
                )
                == []
            )
            page.reload()
            expect(page.locator("#tdefense-page-guard")).to_have_count(0)
            assert all(
                "PRIVATE-QUERY" not in json.dumps(body)
                and "EXCLUSIVE CRYPTO" not in json.dumps(body)
                for body in posted
            )
        finally:
            context.close()
