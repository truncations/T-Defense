from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def test_replay_demo(server):
    """Full flow on a fresh server; GATE reruns this test three times."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 380, "height": 900}, reduced_motion="reduce"
        )
        external = []

        def route(request_route):
            if urlsplit(request_route.request.url).hostname not in {
                "localhost",
                "127.0.0.1",
            }:
                external.append(request_route.request.url)
                request_route.abort()
            else:
                request_route.continue_()

        context.route("**/*", route)
        page = context.new_page()
        page.goto(server + "/sms-demo")
        expect(page.locator(".message")).to_have_count(12)
        expect(page).to_have_title("T-Defense · Interactive scam-text demo")
        expect(page.get_by_role("heading", name="Start the demo")).to_be_visible()
        expect(page.locator(".lead")).to_contain_text("simulated text inbox")
        expect(page.locator(".demo-explainer")).to_contain_text("local demo pages")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        expect(
            page.locator('.message[data-message-id="team-001"] .badge')
        ).to_have_text("Likely scam")
        expect(
            page.locator('.message[data-message-id="team-002"] .badge')
        ).to_have_text("No warning signs")
        assert page.locator('a[href^="http"]').count() == 0
        notice = page.locator("#risk-notification")
        expect(notice).to_be_visible()
        expect(page.locator("#notification-text")).to_have_text(
            "2 sample messages triggered a warning."
        )
        assert (
            notice.evaluate("element => getComputedStyle(element).animationName")
            == "none"
        )
        page.screenshot(path="demo_backup/notification-mobile.png", full_page=True)
        page.locator("#review-notification").click()
        expect(notice).to_be_hidden()
        first_badge = page.locator('.message[data-message-id="team-001"] .badge')
        first_details = page.locator(
            '.message[data-message-id="team-001"] .risk-details'
        )
        expect(first_badge).to_be_focused()
        expect(first_details).to_be_visible()
        first_badge.press("Escape")
        expect(first_details).to_be_hidden()
        first_badge.click()
        expect(first_details).to_be_visible()
        expect(first_badge).to_have_attribute("aria-expanded", "true")
        first_badge.click()
        expect(first_details).to_be_hidden()
        page.screenshot(path="demo_backup/gate-phone-mobile.png", full_page=True)
        for scenario, verdict, filename in [
            ("team-001", "Likely scam", "scam"),
            ("team-002", "Likely scam", "tracking"),
            ("team-003", "No warning signs found", "bill"),
            ("team-006", "Suspicious", "suspicious"),
            ("team-007", "We couldn’t check this", "blocked"),
            ("team-009", "We couldn’t check this", "timeout"),
            ("team-012", "Suspicious", "attachment"),
        ]:
            if scenario in {"team-001", "team-002", "team-003"}:
                page.locator(f'[data-demo-scenario="{scenario}"]').click()
            else:
                page.locator(f'.message[data-message-id="{scenario}"] a').click()
            expect(page.locator("#verdict")).to_have_text(verdict)
            assert (
                "/check/" in page.url
                and "mock/" not in page.url
                and "?" not in page.url
            )
            expect(page.locator("#mode")).to_contain_text("REPLAY")
            expect(page.locator("#unknowns")).to_be_visible()
            assert page.locator("#evidence li").count() <= 3
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if (
                verdict in {"Likely scam", "We couldn’t check this"}
                or scenario == "team-012"
            ):
                expect(page.locator("#open-anyway")).to_be_hidden()
            else:
                expect(page.locator("#open-anyway")).to_be_visible()
            if verdict != "No warning signs found":
                expect(page.locator("#action-warning")).to_be_visible()
            if scenario == "team-012":
                expect(page.locator("#warning-text")).to_contain_text(
                    "contents were not scanned"
                )
            if scenario == "team-001":
                page.locator("#recovery-toggle").click()
                expect(page.locator("#recovery")).to_contain_text("7726")
            page.screenshot(path=f"demo_backup/gate-{filename}.png", full_page=True)
            page.get_by_role("link", name="Go back (recommended)").click()
            expect(page.locator(".message")).to_have_count(12)
        page.goto(server + "/check/expired-token")
        expect(page.locator("#verdict")).to_have_text("We couldn’t check this")
        expect(page.locator("#confidence")).to_contain_text("expired")
        page.set_viewport_size({"width": 1440, "height": 1100})
        page.goto(server + "/sms-demo")
        expect(page.locator(".message")).to_have_count(12)
        expect(page.locator("#risk-notification")).to_be_visible()
        page.screenshot(path="demo_backup/gate-phone-desktop.png", full_page=True)
        page.locator("#dismiss-notification").click()
        expect(page.locator("#risk-notification")).to_be_hidden()
        first_badge.hover()
        expect(first_details).to_be_visible()
        page.screenshot(
            path="demo_backup/badge-explanation-desktop.png", full_page=True
        )
        page.locator(".brand").hover()
        expect(first_details).to_be_hidden()
        first_badge.focus()
        expect(first_details).to_be_visible()
        first_badge.press("Escape")
        expect(first_details).to_be_hidden()
        first_check = page.locator(
            '.message[data-message-id="team-001"] a'
        ).get_attribute("href")
        page.locator("#reset-demo").click()
        expect(page.locator(".message")).to_have_count(12)
        expect(
            page.locator('.message[data-message-id="team-001"] a')
        ).not_to_have_attribute("href", first_check)
        assert not external, external
        context.close()
        browser.close()
