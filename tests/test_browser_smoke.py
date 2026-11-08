from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def test_browser_smoke(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 380, "height": 850})
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto(server + "/mock/lumora/index.html")
        expect(page).to_have_title("Lumora Wireless DEMO · Demo pages")
        page.goto(server + "/sms-demo")
        expect(page.locator("#health")).to_have_text("Backend OK")
        expect(page.locator(".message")).to_have_count(12)
        expect(page.locator(".message").first.locator(".badge")).to_have_text(
            "Likely scam"
        )
        expect(page.locator(".message").nth(1).locator(".badge")).to_have_text(
            "No warning signs"
        )
        assert all(
            urlsplit(url).hostname in {"localhost", "127.0.0.1"} for url in requests
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(Path("demo_backup/stage2-phone.png")), full_page=True)
        browser.close()
