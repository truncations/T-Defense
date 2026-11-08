"""Hostname-only lookalike checks; all browser pages are intercepted fixtures."""

import html
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.page_guard import Snapshot, assess_snapshot

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def collector():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        page.route(
            "https://chat.example.test/**",
            lambda route: route.fulfill(body="<html><body></body></html>"),
        )
        page.goto("https://chat.example.test/")
        page.add_script_tag(content=(ROOT / "extension/scanner.js").read_text())
        yield page
        browser.close()


def collect_link(collector, url, label=None):
    collector.set_content(
        '<div id="message-content-fixture"><a id="test-link" href="'
        + html.escape(url, quote=True)
        + '">'
        + html.escape(label or url)
        + "</a></div>"
    )
    return collector.evaluate(
        "TDefenseSnapshot.collect('interaction',document.querySelector('#test-link')).snapshot"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://www.paypal.ai/scam",
        "https://paypal.ai/scam",
        "https://paypal.com.evil.example/",
        "https://paypal-login.example/",
    ],
)
def test_brand_lookalike_link_warns_without_pressure_or_address_mismatch(
    collector, url
):
    snapshot = collect_link(collector, url)
    result = assess_snapshot(Snapshot.model_validate(snapshot))
    assert (
        collector.evaluate(
            "TDefenseSnapshot.brandLookalike", snapshot["elements"][0]["target_origin"]
        )
        is True
    )
    assert result["verdict"] == "warning"
    assert any(
        row["severity"] == "medium" and "brand-lookalike-host" in row["rules"]
        for row in result["warnings"]
    )
    assert all(
        "misleading-link-address" not in row["rules"] for row in result["warnings"]
    )
    assert "/scam" not in str(snapshot)


@pytest.mark.parametrize(
    "url,label",
    [
        ("https://www.paypal.com/", None),
        ("https://www.paypal.com./", None),
        ("https://www.paypal.me/example", None),
        ("https://www.paypalobjects.com/", None),
        ("https://developer.paypal.com/docs/", None),
        ("https://www.mercari.com/us/item/m123/", "SOLD PayPal gift card $140.00"),
        ("https://www.mercari.com/us/item/m456/", "SOLD OUT Pokémon lot $40.00"),
        ("https://github.com/example/repo/blob/main/paypal.js", "paypal.js"),
        ("https://docs.example.test/paypal.ai/scam", "PayPal discussion"),
        ("https://notpaypal.example/", None),
        ("https://ordinary.ai/scam", None),
    ],
)
def test_benign_domains_listings_and_mentions_do_not_trigger_brand_rule(
    collector, url, label
):
    snapshot = collect_link(collector, url, label)
    assert (
        collector.evaluate(
            "TDefenseSnapshot.brandLookalike", snapshot["elements"][0]["target_origin"]
        )
        is False
    )
    assert assess_snapshot(Snapshot.model_validate(snapshot))["warning_count"] == 0


def test_recognized_paypal_domain_does_not_bypass_other_evidence(collector):
    snapshot = collect_link(
        collector, "https://paypal.com/", "https://different.example/"
    )
    result = assess_snapshot(Snapshot.model_validate(snapshot))
    assert result["warning_count"] == 1
    assert result["warnings"][0]["rules"] == ["misleading-link-address"]


def test_native_extension_lists_and_guards_missed_link(server, tmp_path):
    import httpx
    from playwright.sync_api import expect

    key = httpx.get(server + "/api/extension/pairing").json()["pairing_code"]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(tmp_path / "brand-profile"),
            channel="chromium",
            headless=True,
            args=[
                f"--disable-extensions-except={ROOT / 'extension'}",
                f"--load-extension={ROOT / 'extension'}",
            ],
            viewport={"width": 1280, "height": 1800},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            worker.evaluate("key=>pair(key)", key)
            page = context.new_page()
            # Intercept all fixture/destination traffic. Never visit the reported site.
            page.route("https://www.paypal.ai/**", lambda route: route.abort())
            page.route(
                "**/brand-fixture",
                lambda route: route.fulfill(
                    content_type="text/html",
                    body='<html><body><div id="message-content-fixture"><a id="example" href="https://www.paypal.ai/scam">https://www.paypal.ai/scam</a></div></body></html>',
                ),
            )
            page.goto(server + "/brand-fixture")
            tab = worker.evaluate(
                "async()=> (await chrome.tabs.query({})).find(tab=>tab.url?.includes('/brand-fixture')).id"
            )
            worker.evaluate("id=>startMonitoring(id)", tab)
            guard = page.locator("#tdefense-page-guard")
            expect(guard).to_have_attribute("data-warning-count", "1", timeout=12000)
            expect(guard.locator("#count")).to_have_text("! 1")
            # DOM click bypasses hover so it tests the click guard directly.
            page.locator("#example").evaluate("node=>node.click()")
            expect(guard.locator("#guard-note")).to_be_visible()
            expect(guard.locator(".finding-row")).to_have_count(1)
            assert page.url == server + "/brand-fixture"
            page.screenshot(path=str(tmp_path / "brand-link-warning.png"))
            worker.evaluate("id=>stopMonitoring(id)", tab)
            expect(guard).to_have_count(0)
        finally:
            context.close()
