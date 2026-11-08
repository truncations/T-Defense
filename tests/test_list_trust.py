"""A list action opens protected review without granting persistent trust."""

import json
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_findings_list_only_initiates_genuine_popup_confirmation(server, tmp_path):
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
        worker = (
            context.service_workers[0]
            if context.service_workers
            else context.wait_for_event("serviceworker")
        )
        page = context.new_page()
        page.route(
            "**/list-trust",
            lambda route: route.fulfill(
                body='<html><body><article data-tdefense-message="true"><a href="https://risk.example.test/">Provide gift card code and PIN immediately</a></article></body></html>',
                content_type="text/html",
            ),
        )
        page.goto(server + "/list-trust")
        worker.evaluate("()=>enableEverywhere()")
        ui = page.locator("#tdefense-page-guard")
        expect(ui).to_have_attribute("data-warning-count", "2", timeout=15000)
        ui.locator("#risk-indicator").click()
        ui.locator(".finding-row").first.click()
        ui.locator(".detail .finding-trust").click()
        assert worker.evaluate("()=>TrustStore.read()") == []
        tab = worker.evaluate(
            "async()=> (await chrome.tabs.query({})).find(t=>t.url?.endsWith('/list-trust')).id"
        )
        denied = worker.evaluate(
            "async id=>{try{await handle({type:'TRUST_SELECTED',tabId:id,token:'forged'},{id:chrome.runtime.id,tab:{id},frameId:0,url:'http://localhost:8000/list-trust'});return false}catch{return true}}",
            tab,
        )
        assert denied is True
        popup = context.new_page()
        await_url = worker.evaluate("()=>chrome.runtime.getURL('popup.html')")
        popup.goto(await_url)
        # Real toolbar message boundary, preview, and exact-content revalidation.
        candidate = worker.evaluate(
            "id=>handle({type:'TRUST_PREVIEW',tabId:id},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
            tab,
        )["candidate"]
        assert worker.evaluate("()=>TrustStore.read()") == []
        worker.evaluate(
            "args=>handle({type:'TRUST_SELECTED',tabId:args.id,token:args.token},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})",
            {"id": tab, "token": candidate["token"]},
        )
        expect(ui).to_have_attribute("data-warning-count", "0", timeout=12000)
        assert len(worker.evaluate("()=>TrustStore.read()")) == 1
        page.screenshot(path="/tmp/browser/t-defense/trust-confirmed.png")
        context.close()
