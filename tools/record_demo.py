"""Record a silent 90-second replay walkthrough; no external network access.

Run from repository root with .venv/Scripts/python.exe tools/record_demo.py.
Port 8000 must be free. The helper starts and stops its own server.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright"))
BASE = "http://localhost:8000"


def main():
    try:
        httpx.get(BASE + "/api/health", timeout=0.3)
    except httpx.HTTPError:
        pass
    else:
        raise RuntimeError("Stop the server using port 8000 before recording.")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-access-log",
        ],
        cwd=ROOT,
        env=dict(os.environ, DEMO_MODE="replay"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            try:
                if httpx.get(BASE + "/api/health", timeout=0.3).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if process.poll() is not None:
                raise RuntimeError("Server exited before recording")
            time.sleep(0.1)
        else:
            raise RuntimeError("Server did not start")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                viewport={"width": 1280, "height": 1000},
                record_video_dir=str(ROOT / "work/video"),
                record_video_size={"width": 1280, "height": 1000},
            )
            context.route(
                "**/*",
                lambda route: (
                    route.continue_()
                    if urlsplit(route.request.url).hostname
                    in {"localhost", "127.0.0.1"}
                    else route.abort()
                ),
            )
            page = context.new_page()
            start = time.monotonic()

            def hold(seconds):
                page.wait_for_timeout(seconds * 1000)

            def home():
                page.goto(BASE + "/sms-demo")
                expect(page.locator(".message")).to_have_count(12)

            def card(scenario, title):
                home()
                page.locator(f'.message[data-message-id="{scenario}"] a').click()
                expect(page.locator("#verdict")).to_have_text(title)
                print(title, flush=True)

            home()
            print("Recording replay phone", flush=True)
            hold(8)
            card("team-001", "Likely scam")
            hold(9)
            page.locator("#next-steps").scroll_into_view_if_needed()
            hold(7)
            page.locator("#recovery-toggle").click()
            page.locator("#recovery").scroll_into_view_if_needed()
            hold(6)
            card("team-002", "Likely scam")
            hold(10)
            page.locator("#next-steps").scroll_into_view_if_needed()
            hold(6)
            card("team-003", "No warning signs found")
            hold(9)
            page.locator("#next-steps").scroll_into_view_if_needed()
            hold(6)
            card("team-006", "Suspicious")
            hold(7)
            card("team-012", "Suspicious")
            hold(6)
            card("team-007", "We couldn’t check this")
            hold(7)
            home()
            while time.monotonic() - start < 90:
                hold(min(5, 90 - (time.monotonic() - start)))
            video = page.video
            context.close()
            video.save_as(str(ROOT / "demo_backup/gate-walkthrough.webm"))
            browser.close()
            print(
                "Saved demo_backup/gate-walkthrough.webm (approximately90seconds, silent)",
                flush=True,
            )
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
