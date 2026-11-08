"""Fixed offline guest readiness probe; invoked by file path, never Python -c."""

import json


def check_browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(chromium_sandbox=True)
        try:
            page = browser.new_page()
            # No navigation/network access or arbitrary page content.
            page.set_content("<h1>Synthetic offline readiness check</h1>")
            if page.locator("h1").inner_text() != "Synthetic offline readiness check":
                raise RuntimeError("Offline page check failed")
        finally:
            browser.close()


def main():
    try:
        check_browser()
    except Exception as error:  # noqa: BLE001 - return a bounded guest diagnostic instead of truncated native stderr
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (type(error).__name__ + ": " + str(error))[:4000],
                }
            )
        )
        return 1
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
