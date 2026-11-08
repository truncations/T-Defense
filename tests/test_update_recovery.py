"""Native regressions for valid pairing reuse and replacing old page monitors."""

import json
import shutil
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_existing_pairing_and_old_monitor_replacement(server, tmp_path):
    extension = tmp_path / "extension"
    shutil.copytree(ROOT / "extension", extension)
    manifest = json.loads((extension / "manifest.json").read_text())
    manifest["host_permissions"] += manifest.pop("optional_host_permissions")
    (extension / "manifest.json").write_text(json.dumps(manifest))
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "profile"),
            channel="chromium",
            headless=True,
            args=[
                f"--disable-extensions-except={extension}",
                f"--load-extension={extension}",
            ],
            viewport={"width": 1280, "height": 1800},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            key = httpx.get(server + "/api/extension/pairing").json()["pairing_code"]
            worker.evaluate("key=>pair(key)", key)
            reused = worker.evaluate(
                "async()=>{try{return await handle({type:'AUTO_PAIR'},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})}catch{return {ok:false}}}"
            )
            assert reused["ok"] is True and not reused.get("approvalRequired")
            page = context.new_page()
            page.goto(server + "/extension-lab")
            worker.evaluate("()=>enableEverywhere()")
            ui = page.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-status", "checked", timeout=15000)
            tab = worker.evaluate(
                "async()=>(await chrome.tabs.query({})).find(t=>t.url?.includes('/extension-lab')).id"
            )
            worker.evaluate(
                "id=>chrome.scripting.executeScript({target:{tabId:id},func:()=>{const current=TDefenseGuard;window.legacyStopped=false;TDefenseGuard={version:'0.0.0',scan(){},stop(){window.legacyStopped=true;current.stop()}};}})",
                tab,
            )
            worker.evaluate('id=>armGlobal(id,"http://localhost:8000")', tab)
            assert (
                worker.evaluate(
                    "async id=>(await chrome.scripting.executeScript({target:{tabId:id},func:()=>window.legacyStopped}))[0].result",
                    tab,
                )
                is True
            )
            expect(ui).to_have_attribute("data-status", "checked", timeout=15000)
            assert ui.count() == 1
            page.get_by_role("button", name="Add suspicious message").click()
            expect(ui).to_have_attribute("data-warning-count", "2", timeout=15000)
            ui.locator("#risk-indicator").click()
            ui.locator(".finding-row").first.click()
            ui.locator(".actions .finding-trust").click()
            assert worker.evaluate("()=>TrustStore.read()") == []
            page.screenshot(path=str(tmp_path / "updated-risk-drawer.png"))
            ui.locator("#close").click()
            expect(ui.locator("#body")).to_be_hidden()
            page.wait_for_timeout(300)
            page.screenshot(path=str(tmp_path / "updated-risk-tab.png"))
        finally:
            context.close()
