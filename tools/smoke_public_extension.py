"""Read-only public-page smoke test for the actual extension and local backend.

The temporary test copy grants only example.com to permit automated injection.
The shipped manifest requests optional all-site access through Start everywhere.
No forms are filled or submitted and no destination links are opened.
"""

import hashlib
import json
import shutil
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    import os

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright"))
    copy = ROOT / "work/public-extension"
    shutil.copytree(ROOT / "extension", copy, dirs_exist_ok=True)
    manifest = json.loads((copy / "manifest.json").read_text())
    manifest["host_permissions"].append("https://example.com/*")
    (copy / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name in (
        "background.js",
        "bootstrap.js",
        "trust.js",
        "scanner.js",
        "content.js",
        "popup.js",
    ):
        assert (
            hashlib.sha256((copy / name).read_bytes()).digest()
            == hashlib.sha256((ROOT / "extension" / name).read_bytes()).digest()
        )
    with httpx.Client(base_url="http://127.0.0.1:8000", trust_env=False) as client:
        key = client.get("/api/extension/pairing").json()["pairing_code"]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(ROOT / "work/public-browser-profile"),
            channel="chromium",
            headless=True,
            args=[f"--disable-extensions-except={copy}", f"--load-extension={copy}"],
            viewport={"width": 1280, "height": 900},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            worker.evaluate("key => pair(key)", key)
            page = context.new_page()
            page.goto(
                "https://example.com", wait_until="domcontentloaded", timeout=30000
            )
            tab_id = worker.evaluate(
                "async () => (await chrome.tabs.query({})).find(tab => tab.url?.startsWith('https://example.com')).id"
            )
            worker.evaluate("id => startMonitoring(id)", tab_id)
            host = page.locator("#tdefense-page-guard")
            expect(host).to_have_attribute("data-status", "checked", timeout=12000)
            expect(host).to_have_attribute("data-warning-count", "0")
            state = worker.evaluate("id => tabState(id)", tab_id)
            assert state["scanId"].startswith("pg_") and state["scanCount"] >= 1
            page.screenshot(
                path=str(ROOT / "demo_backup/extension-public-page.png"), full_page=True
            )
            report = {
                "site": "https://example.com",
                "read_only": True,
                "forms_submitted": False,
                "backend_scan_id": state["scanId"],
                "completed_checks": state["scanCount"],
                "warnings": state["warningCount"],
                "test_permission": "Temporary test copy grants example.com only; production all-site access is optional",
            }
            (ROOT / "work/public-smoke-result.json").write_text(
                json.dumps(report, indent=2)
            )
            print(json.dumps(report))
        finally:
            context.close()


if __name__ == "__main__":
    main()
