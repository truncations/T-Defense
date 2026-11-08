"""Continue anyway must still deliver a file whose temporary link was already removed."""

import json
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def test_continue_anyway_downloads_removed_blob_link(server, tmp_path):
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
            accept_downloads=True,
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
            page = context.new_page()
            page.goto(server + "/mock/lab/temporary-download.html")
            worker.evaluate("()=>enableEverywhere()")
            ui = page.locator("#tdefense-page-guard")
            expect(ui).to_have_attribute("data-status", "checked", timeout=15000)
            page.get_by_role("button", name="Download report").click()
            expect(ui.locator("#guard-note")).to_be_visible(timeout=10000)
            expect(ui.locator("#continue")).to_be_enabled(timeout=15000)
            with page.expect_download(timeout=10000) as caught:
                ui.locator("#continue").click()
            download = caught.value
            assert download.suggested_filename == "report.txt"
            assert Path(download.path()).read_text() == "synthetic report"
        finally:
            context.close()
