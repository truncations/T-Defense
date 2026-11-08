"""Real extension pairing, independent controls, and genuine fallback findings."""

import json
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_automatic_pairing_and_popup_backup_with_missing_panel(server, tmp_path):
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
            extension_id = worker.evaluate("chrome.runtime.id")
            popup_sender = {
                "id": extension_id,
                "url": worker.evaluate("chrome.runtime.getURL('popup.html')"),
            }
            page = context.new_page()
            page.goto(server + "/extension-lab")
            tab_id = worker.evaluate(
                "async()=>(await chrome.tabs.query({})).find(t=>t.url?.includes('/extension-lab')).id"
            )
            with context.expect_page() as opened:
                result = worker.evaluate(
                    "()=>handle({type:'AUTO_PAIR'},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})"
                )
            setup = opened.value
            setup.wait_for_url("http://127.0.0.1:8000/")
            assert result["ok"] is True and result["approvalRequired"] is True
            assert worker.evaluate("()=>globalSettings()")["enabled"] is False
            setup.get_by_role("button", name="Approve installation", exact=True).click(
                timeout=15000
            )
            # One local approval; no copying or entry of a pairing code.
            assert worker.evaluate("()=>automaticPair()")["ok"] is True
            assert worker.evaluate("()=>globalSettings()")["enabled"] is False
            assert (
                worker.evaluate(
                    "async()=>Object.keys(await chrome.storage.local.get(null)).includes('backendKey')"
                )
                is False
            )
            page.bring_to_front()
            worker.evaluate("()=>enableEverywhere()")
            ui = page.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-status", "checked", timeout=15000)
            page.get_by_role("button", name="Add suspicious message").click()
            expect(ui).to_have_attribute("data-warning-count", "2", timeout=15000)
            ui.locator("#toggle").click()
            expect(ui.locator("#body")).to_be_visible()
            page.screenshot(path="/tmp/browser/drawer-desktop.png")
            page.set_viewport_size({"width": 390, "height": 844})
            panel = ui.locator(".shell").bounding_box()
            assert panel["x"] >= 0 and panel["x"] + panel["width"] <= 391
            page.screenshot(path="/tmp/browser/drawer-mobile.png")
            page.set_viewport_size({"width": 1280, "height": 1800})
            ui.locator("#close").click()
            page.locator(".lab-message a").first.click()
            expect(ui.locator("#guard-note")).to_be_visible()
            expect(ui.locator("#continue")).to_be_enabled(timeout=15000)
            page.screenshot(path="/tmp/browser/action-paused.png")
            page.evaluate("document.querySelector('#tdefense-page-guard').remove()")
            popup = context.new_page()
            popup.goto(popup_sender["url"])
            page.bring_to_front()
            popup.reload()
            expect(popup.locator("#popup-findings li")).to_have_count(2)
            expect(popup.locator("#popup-findings")).to_contain_text("gift")
            expect(popup.locator("#page")).to_contain_text("localhost:8000")
            popup.locator("body").screenshot(path="/tmp/browser/popup-backup.png")
            assert worker.evaluate("()=>TrustStore.read()") == []
            worker.evaluate("()=>stopEverywhere()")
            assert worker.evaluate("id=>tabState(id)", tab_id).get("findings", []) == []
            worker.evaluate("()=>automaticPair()")
            assert worker.evaluate("()=>globalSettings()")["enabled"] is False
        finally:
            context.close()


def test_stop_and_superseded_start_during_pairing(server, tmp_path):
    extension = tmp_path / "extension-races"
    shutil.copytree(ROOT / "extension", extension)
    manifest = json.loads((extension / "manifest.json").read_text())
    manifest["host_permissions"] += manifest.pop("optional_host_permissions")
    (extension / "manifest.json").write_text(json.dumps(manifest))
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "races-profile"),
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
            result = worker.evaluate("""async()=>{
              const real=connectedKey;let release;connectedKey=()=>new Promise(resolve=>{release=resolve});
              const starting=enableEverywhere().then(()=>true,()=>false);
              while(!release)await new Promise(resolve=>setTimeout(resolve,10));
              await stopEverywhere();release();const started=await starting;
              connectedKey=real;return {started,settings:await globalSettings()};
            }""")
            assert result["started"] is False and result["settings"]["enabled"] is False
            assert "startIntent" not in result["settings"]
            failed = worker.evaluate(
                """async()=>{const real=connectedKey;connectedKey=async()=>{throw new Error('Synthetic unavailable')};try{await enableEverywhere()}catch{}connectedKey=real;return globalSettings();}"""
            )
            assert failed["enabled"] is False and "startIntent" not in failed
        finally:
            context.close()
