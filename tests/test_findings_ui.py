import html
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from tests.test_social_engineering import NITRO

ROOT = Path(__file__).resolve().parent.parent


def test_all_markers_list_navigation_stable_count_and_manual_refresh(server, tmp_path):
    key = httpx.get(server + "/api/extension/pairing").json()["pairing_code"]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "findings-profile"),
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
            cards = "".join(
                f'<article data-tdefense-message="true" id="risk-{i}" style="margin:30px 0;padding:20px;border:1px solid #555"><h2>Quoted synthetic example {i + 1}</h2>'
                + "".join(
                    "<p>" + html.escape(line) + "</p>" for line in NITRO.splitlines()
                )
                + f'<p><a href="https://discord-nitro-gift.example/claim?private=PRIVATE-LINK-{i}">Claim the reward</a></p></article>'
                for i in range(7)
            )
            page.route(
                "**/social-fixture",
                lambda route: route.fulfill(
                    content_type="text/html",
                    body='<html><head><meta charset="utf-8"></head><body style="margin:20px;font:18px Arial"><main style="max-width:750px"><h1>User-provided scam example · synthetic test only</h1>'
                    + cards
                    + "</main></body></html>",
                ),
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
            page.goto(server + "/social-fixture")
            tab = worker.evaluate(
                "async()=> (await chrome.tabs.query({})).find(tab=>tab.url?.includes('/social-fixture')).id"
            )
            worker.evaluate("id=>startMonitoring(id)", tab)
            guard = page.locator("#tdefense-page-guard")
            expect(guard).to_have_attribute("data-warning-count", "14", timeout=12000)
            expect(guard.locator("#count")).to_have_text(
                "! 14"
            )
            expect(guard.locator("#risk-indicator")).to_be_visible()
            expect(guard.locator("#risk-indicator")).to_have_class("risk attention")
            page.emulate_media(reduced_motion="reduce")
            assert (
                guard.locator("#risk-indicator").evaluate(
                    "node=>getComputedStyle(node).animationName"
                )
                == "none"
            )
            page.emulate_media(reduced_motion="no-preference")
            expect(guard.locator("#body")).to_be_hidden()
            guard.locator("#risk-indicator").click()
            expect(guard.locator(".finding-row")).to_have_count(14)
            assert guard.locator("#findings").evaluate(
                "node=>node.scrollHeight>node.clientHeight"
            )
            assert (
                guard.locator("#findings").evaluate(
                    "node=>getComputedStyle(node).overflowY"
                )
                == "auto"
            )
            assert guard.locator("#locate,#next,#clear-review").count() == 0
            # Every listed live node gets a real matching marker when located, including offscreen nodes.
            for index in range(14):
                row = guard.locator(".finding-row").nth(index)
                element_id = row.get_attribute("data-element-id")
                row.click()
                marker = guard.locator(
                    '.highlight[data-element-id="' + element_id + '"]'
                ).first
                expect(marker).to_be_visible()
                # Measure both in one renderer task; scroll/RAF may replace marker nodes.
                for _ in range(40):
                    geometry = worker.evaluate(
                        """async args=>(await chrome.scripting.executeScript({target:{tabId:args.tab},func:id=>{const node=TDefenseSnapshot.collect('manual').nodes.get(id);const r=node.getClientRects()[0];const m=document.querySelector('#tdefense-page-guard').shadowRoot.querySelector('.highlight[data-element-id="'+id+'"]');const b=m?.getBoundingClientRect();return {target:{left:r.left,top:r.top},box:b?{x:b.x,y:b.y}:null};},args:[args.id]}))[0].result""",
                        {"tab": tab, "id": element_id},
                    )
                    if (
                        geometry["box"]
                        and abs(
                            geometry["box"]["x"] - max(0, geometry["target"]["left"])
                        )
                        < 2
                        and abs(
                            geometry["box"]["y"] - max(0, geometry["target"]["top"])
                        )
                        < 2
                    ):
                        break
                    page.wait_for_timeout(50)
                else:
                    raise AssertionError((index, element_id, geometry))
                assert (
                    marker.evaluate("node=>getComputedStyle(node).backgroundColor")
                    != "rgba(0, 0, 0, 0)"
                )
                assert marker.locator("b").inner_text().startswith("! ")
            # Mutations and a periodic scan do not replace the warning headline with checking text.
            page.evaluate(
                """()=>{const root=document.querySelector('#tdefense-page-guard').shadowRoot;window.headlineChanges=[];new MutationObserver(()=>headlineChanges.push(root.querySelector('#count').textContent)).observe(root.querySelector('#count'),{childList:true,subtree:true,characterData:true});}"""
            )
            for _ in range(3):
                page.evaluate("document.body.append(document.createElement('aside'))")
                page.wait_for_timeout(120)
                expect(guard.locator("#count")).to_have_text(
                    "! 14"
                )
            page.wait_for_timeout(9000)
            assert page.evaluate("headlineChanges") == [], (
                "Unchanged warning headline must not be rewritten by background checks"
            )
            page.screenshot(path="/tmp/browser/social-all-findings.png", full_page=False)
            page.set_viewport_size({"width": 390, "height": 844})
            panel = guard.bounding_box()
            assert panel["x"] >= 0 and panel["x"] + panel["width"] <= 391
            assert (
                guard.locator("#body").evaluate("node=>node.clientHeight")
                <= 844 * 0.57 + 1
            )
            page.screenshot(
                path="/tmp/browser/social-mobile-findings.png", full_page=False
            )
            page.set_viewport_size({"width": 1400, "height": 1000})
            assert posted and all(
                NITRO not in body and "PRIVATE-LINK" not in body for body in posted
            )
            # Move a previously marked node outside a truncated batch; manual checking cannot silently discard it.
            page.evaluate(
                """()=>{const fragment=document.createDocumentFragment();for(let i=0;i<250;i++){const p=document.createElement('p');p.textContent='Ordinary document paragraph '+i;fragment.append(p);}document.querySelector('main').prepend(fragment);}"""
            )
            page.evaluate("scrollTo(0,0)")
            guard.locator("#scan").click()
            expect(guard).to_have_attribute("data-status", "partial", timeout=12000)
            expect(guard.locator("#findings")).to_contain_text(
                "Outside this scan", timeout=12000
            )
            assert int(guard.get_attribute("data-finding-count")) >= 14
            # Automatic removals retain previous evidence; a requested recheck can clear removed nodes.
            page.locator("article").evaluate_all(
                "nodes=>nodes.forEach(node=>node.remove())"
            )
            expect(guard.locator(".finding-row")).to_have_count(0, timeout=12000)
            guard.locator("#scan").click()
            expect(guard.locator(".finding-row")).to_have_count(0, timeout=12000)
            expect(guard.locator(".highlight")).to_have_count(0)
            expect(guard.locator("#count")).to_have_text(
                "! 0"
            )
            expect(guard.locator("#count")).to_have_text("! 0")
            worker.evaluate("id=>stopMonitoring(id)", tab)
            expect(guard).to_have_count(0)
        finally:
            context.close()
