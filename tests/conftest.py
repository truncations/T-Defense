import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright"))


@pytest.fixture
def server(request):
    try:
        httpx.get("http://localhost:8000/api/health", timeout=0.3)
    except httpx.HTTPError:
        pass
    else:
        pytest.fail("Port 8000 is already in use; stop that server first.")
    env = dict(os.environ, DEMO_MODE=getattr(request, "param", "replay"))
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
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            try:
                response = httpx.get("http://localhost:8000/api/health", timeout=0.3)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if process.poll() is not None:
                pytest.fail("Demo server exited before becoming ready")
            time.sleep(0.1)
        else:
            pytest.fail("Demo server did not become ready")
        yield "http://localhost:8000"
    finally:
        process.terminate()
        process.wait(timeout=10)
