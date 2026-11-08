"""Actual MV3 shared layout and honest outage/recovery behavior."""

import json
import shutil
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_shared_position_and_stable_connection_status(server, tmp_path):
    key = httpx.get(server + "/api/extension/pairing").json()["pairing_code"]
    extension = tmp_path / "extension"
    shutil.copytree(ROOT / "extension", extension)
    manifest = json.loads((extension / "manifest.json").read_text())
    # Automated test copy pregrants the same optional origins; production uses a toolbar gesture.
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
            viewport={"width": 1200, "height": 900},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            worker.evaluate("key=>pair(key)", key)
            context.route(
                "**/layout-test",
                lambda route: route.fulfill(
                    content_type="text/html",
                    body='<h1>Synthetic layout test</h1><p id="change">Plain content.</p>',
                ),
            )
            first = context.new_page()
            first.goto(server + "/layout-test")
            worker.evaluate("()=>enableEverywhere()")
            ui = first.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-status", "checked", timeout=15000)
            second = context.new_page()
            second.goto("https://layout-peer.example/layout-test")
            peer = second.locator("#tdefense-page-guard")
            expect(peer).to_have_attribute("data-status", "checked", timeout=15000)
            # Move one actual handle; already-open cross-origin tab updates without reload/check.
            first.bring_to_front()
            handle = ui.locator("#move").bounding_box()
            first.mouse.move(
                handle["x"] + handle["width"] / 2, handle["y"] + handle["height"] / 2
            )
            first.mouse.down()
            first.mouse.move(210, 240, steps=5)
            first.mouse.up()

            def position(page):
                return page.evaluate(
                    """()=>{const r=document.querySelector('#tdefense-page-guard').shadowRoot.querySelector('.shell').getBoundingClientRect();return {x:r.x,y:r.y};}"""
                )

            moved = position(first)
            second.wait_for_function(
                'expected=>{const r=document.querySelector("#tdefense-page-guard").shadowRoot.querySelector(".shell").getBoundingClientRect();return Math.abs(r.x-expected.x)<2 && Math.abs(r.y-expected.y)<2;}',
                arg=moved,
            )
            third = context.new_page()
            third.goto("https://layout-new.example/layout-test")
            expect(third.locator("#tdefense-page-guard")).to_have_attribute(
                "data-status", "checked", timeout=15000
            )
            assert (
                abs(position(third)["x"] - moved["x"]) < 2
                and abs(position(third)["y"] - moved["y"]) < 2
            )
            # Reset is global too, and survives reload.
            worker.evaluate(
                "()=>handle({type:'RESET_POSITION'},{id:chrome.runtime.id,url:chrome.runtime.getURL('popup.html')})"
            )
            for page in [first, second, third]:
                page.wait_for_function(
                    '()=>document.querySelector("#tdefense-page-guard").style.left==="auto"'
                )
            second.reload()
            expect(peer).to_have_attribute("data-status", "checked", timeout=15000)
            assert abs(position(first)["x"] - position(second)["x"]) < 2
            third.close()
            second.close()
            first.bring_to_front()
            tab = worker.evaluate(
                "async()=>(await chrome.tabs.query({})).find(t=>t.url?.includes('/layout-test')).id"
            )
            first.evaluate(
                """()=>{const count=document.querySelector('#tdefense-page-guard').shadowRoot.getElementById('count');window.headlines=[];new MutationObserver(()=>headlines.push(count.textContent)).observe(count,{childList:true,subtree:true,characterData:true});}"""
            )
            worker.evaluate(
                """()=>{globalThis.realBackend=requestBackend;globalThis.failuresLeft=1;requestBackend=async(...args)=>{if(args[0]==='/api/page/assess' && failuresLeft-->0){const e=new Error('Synthetic temporary network error');e.retryable=true;throw e;}return realBackend(...args);};}"""
            )
            old_id = ui.get_attribute("data-scan-id")
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})", tab
            )
            first.wait_for_function(
                'old=>{const h=document.querySelector("#tdefense-page-guard");return h.dataset.scanId && h.dataset.scanId!==old;}',
                arg=old_id,
            )
            assert not any(
                "unavailable" in text.lower() for text in first.evaluate("headlines")
            )
            # Persistent failures show an honest outage. DOM mutations and manual retry must not imply recovery.
            worker.evaluate(
                """()=>{requestBackend=async(...args)=>{if(args[0]==='/api/page/assess'){const e=new Error('Synthetic continuing outage');e.retryable=true;throw e;}return realBackend(...args);};}"""
            )
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})", tab
            )
            expect(ui).to_have_attribute("data-status", "unavailable", timeout=8000)
            expect(ui.locator("#count")).to_have_text(
                "Checks unavailable — use caution"
            )
            ui.locator("#toggle").click()
            first.evaluate("headlines=[]")
            ui.locator("#scan").click()
            expect(ui.locator("#count")).to_have_text(
                "Checks unavailable — use caution"
            )
            first.wait_for_timeout(1000)
            assert first.evaluate("headlines") == []
            first.locator("#change").evaluate(
                "n=>n.textContent='Changed plain content'"
            )
            first.wait_for_timeout(1800)
            assert ui.get_attribute("data-status") == "unavailable"
            assert first.evaluate("headlines") == []
            # A successful current result is the only recovery transition.
            worker.evaluate("()=>{requestBackend=realBackend;}")
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})", tab
            )
            expect(ui).to_have_attribute("data-status", "checked", timeout=10000)
            expect(ui.locator("#count")).to_have_text(
                "I'm running checks for you periodically"
            )
            # Authentication errors are not delayed/retried as transient faults.
            worker.evaluate(
                """()=>{globalThis.authAttempts=0;requestBackend=async(...args)=>{if(args[0]==='/api/page/assess'){authAttempts++;throw new Error('Pair again with the current backend session.');}return realBackend(...args);};}"""
            )
            worker.evaluate(
                "id=>chrome.tabs.sendMessage(id,{type:'TDEFENSE_RESTART_CHECK'})", tab
            )
            expect(ui).to_have_attribute("data-status", "unavailable", timeout=5000)
            first.wait_for_timeout(800)
            assert worker.evaluate("authAttempts") == 1
            worker.evaluate("()=>{requestBackend=realBackend;}")
        finally:
            context.close()
