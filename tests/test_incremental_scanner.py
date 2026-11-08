"""Synthetic regressions for filename warnings and bounded incremental work."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from app.page_guard import Snapshot, assess_snapshot

ROOT = Path(__file__).resolve().parent.parent


def test_repository_filenames_are_not_addresses_but_deception_still_warns():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        names = [
            "AGENTS.md",
            "README.md",
            "requirements.txt",
            "pyproject.toml",
            ".env.example",
            "scanner.js",
        ]
        html = (
            "<html><body>"
            + "".join(
                f'<p><a href="/truncations/T-Defense/blob/main/{name}">{name}</a></p>'
                for name in names
            )
            + '<p><a href="https://other.example.test/">https://bank.example.test/</a></p><p><a href="https://raw.githubusercontent.com/truncations/T-Defense/main/scanner.js">Source download</a></p></body></html>'
        )
        page.route(
            "https://github.com/**",
            lambda route: route.fulfill(body=html, content_type="text/html"),
        )
        page.goto("https://github.com/truncations/T-Defense")
        page.add_script_tag(content=(ROOT / "extension/scanner.js").read_text())
        snapshot = page.evaluate("TDefenseSnapshot.collect().snapshot")
        links = [item for item in snapshot["elements"] if item["kind"] == "link"]
        assert all(
            item["displayed_origin"] is None and not item["download"]
            for item in links[:6]
        )
        result = assess_snapshot(Snapshot.model_validate(snapshot))
        assert "misleading-link-address" in result["warnings"][0]["rules"]
        assert "download-js" in result["warnings"][1]["rules"]
        browser.close()


def test_benign_listings_do_not_imply_security_risks():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        page.route(
            "https://market.example.test/**",
            lambda route: route.fulfill(
                body='<html><body><h1>See what is selling</h1><article><a href="/item/1">SOLD Vintage bag $140.00 $175.00</a></article><article><a href="/item/2">RESERVED!!! Pokémon lot $40.00</a></article><article><a href="/item/3">Tops and t-shirts · discount · shop now</a></article></body></html>',
                content_type="text/html",
            ),
        )
        page.goto("https://market.example.test/")
        page.add_script_tag(content=(ROOT / "extension/scanner.js").read_text())
        result = assess_snapshot(
            Snapshot.model_validate(
                page.evaluate("TDefenseSnapshot.collect().snapshot")
            )
        )
        assert result["warning_count"] == 0
        page.evaluate(
            "document.querySelector('article').innerHTML='<a href=\"/pay\">Send gift card code and PIN immediately to claim your prize</a>';TDefenseSnapshot.invalidate([{target:document.querySelector('article'),type:'childList',addedNodes:[]}])"
        )
        result = assess_snapshot(
            Snapshot.model_validate(
                page.evaluate("TDefenseSnapshot.collect().snapshot")
            )
        )
        assert any(
            "gift-card-code-request" in row["rules"] for row in result["warnings"]
        )
        browser.close()


def test_changed_nodes_are_coalesced_and_interactions_skip_background_backlog():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        page.route(
            "http://localhost:8080/**",
            lambda route: route.fulfill(
                status=200, content_type="text/html", body="<html></html>"
            ),
        )
        page.goto("http://localhost:8080")
        page.set_content(
            '<html><body><a id="focus" href="/safe">Normal</a>'
            + "".join(
                f'<article data-tdefense-message="true">Chat {i}</article>'
                for i in range(10000)
            )
            + "</body></html>"
        )
        page.add_script_tag(content=(ROOT / "extension/scanner.js").read_text())
        state = page.evaluate(
            """()=>{const rows=[...document.querySelectorAll('article')];for(let i=0;i<2000;i++)TDefenseSnapshot.invalidate([{target:rows[i],type:'characterData'}]);return {pending:TDefenseSnapshot.pendingCount,coverage:TDefenseSnapshot.collect().snapshot.coverage};}"""
        )
        assert state["pending"] <= 600
        assert state["coverage"]["elements_scanned"] <= 200
        assert state["coverage"]["truncated"] is True
        result = page.evaluate(
            """async()=>{const link=document.querySelector('#focus');link.textContent='Provide gift card code and PIN';TDefenseSnapshot.invalidate([{target:link,type:'characterData'}]);return (await TDefenseSnapshot.collectAsync('interaction',link)).snapshot;}"""
        )
        assert result["elements"][0]["gift_code_request"] is True
        assert result["elements"][0]["target_origin"] == "http://localhost:8080"
        assert len(result["elements"]) <= 3
        page.evaluate(
            "document.querySelector('#focus').innerHTML='<span>Normal again</span>';TDefenseSnapshot.invalidate([{target:document.querySelector('#focus span'),type:'characterData'}])"
        )
        snapshot = page.evaluate(
            "TDefenseSnapshot.collect('interaction',document.querySelector('#focus')).snapshot"
        )
        assert snapshot["elements"][0]["gift_code_request"] is False
        browser.close()


def test_open_shadow_content_is_eventually_checked_across_batches():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        page.route(
            "http://localhost:8080/**",
            lambda route: route.fulfill(
                status=200, content_type="text/html", body="<html></html>"
            ),
        )
        page.goto("http://localhost:8080")
        page.set_content("<html><body><div id='root'></div></body></html>")
        page.evaluate(
            "const shadow=document.querySelector('#root').attachShadow({mode:'open'});shadow.innerHTML=Array.from({length:400},(_,i)=>`<a href='/item/${i}'>Item ${i}</a>`).join('')"
        )
        page.add_script_tag(content=(ROOT / "extension/scanner.js").read_text())
        targets = page.evaluate(
            """()=>{let targets=new Set();for(let i=0;i<8;i++){const data=TDefenseSnapshot.collect();for(const node of data.nodes.values())if(node.tagName==='A')targets.add(node.getAttribute('href'));}return [...targets];}"""
        )
        assert "/item/399" in targets
        assert len(targets) == 400
        browser.close()
