from pathlib import Path
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app import investigator, replay, store
from app.main import app
from app.safety import allowed_url

CLIENT = TestClient(app)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/",
        "http://localhost:8000.evil.test/mock/lumora/bill.html",
        "http://localhost:8000@evil.test/mock/lumora/bill.html",
        "http://user@localhost:8000/mock/lumora/bill.html",
        "http://localhost:9000/mock/lumora/bill.html",
        "http://localhost:8000/mock/../static/phone.js",
        "http://localhost:8000/mock/%2e%2e/static/phone.js",
        "http://localhost:8000/mock/lumora/bill.html?redirect=external",
        "http://localhost:8000/mock/lumora/bill.html#x",
        "http://localhost:8000/mock\\evil.test/bill.html",
        "file:///mock/lumora/bill.html",
        "http://[::1]:8000/mock/lumora/bill.html",
    ],
)
def test_url_policy_blocks_escape(url):
    assert not allowed_url(url)
    assert replay.investigate(url)["status"] == "blocked"
    assert investigator.investigate(url)["status"] == "blocked"


def assess(url):
    response = CLIENT.post(
        "/api/assess", json={"message_id": "test", "text": "Demo notice: " + url}
    )
    assert response.status_code == 200
    return response.json()["links"][0]


def test_random_links_and_no_raw_url_in_check_address():
    url = "http://localhost:8000/mock/lumora/bill.html"
    first, second = assess(url), assess(url)
    assert first["link_id"] != second["link_id"]
    assert len(first["link_id"]) >= 24
    assert url not in first["check_url"] and urlsplit(first["check_url"]).query == ""
    assert first["check_url"].startswith("/check/")
    assert store.links[first["link_id"]]["sha256"]


def test_external_url_cannot_borrow_local_fixture():
    link = assess("https://evil.example.test/mock/lumora/bill.html")
    CLIENT.post(f"/api/links/{link['link_id']}/investigate")
    card = CLIENT.get(f"/api/links/{link['link_id']}/verdict").json()
    assert card["status"] == "blocked" and card["verdict"] == "inconclusive"
    assert (
        CLIENT.get(
            f"/api/links/{link['link_id']}/open", follow_redirects=False
        ).status_code
        == 403
    )


def test_clean_link_requires_completed_check_before_open():
    link = assess("http://localhost:8000/mock/lumora/bill.html")
    assert (
        CLIENT.get(f"/api/links/{link['link_id']}/verdict").json()["status"]
        == "pending"
    )
    assert (
        CLIENT.get(
            f"/api/links/{link['link_id']}/open", follow_redirects=False
        ).status_code
        == 403
    )
    CLIENT.post(f"/api/links/{link['link_id']}/investigate")
    assert (
        CLIENT.get(f"/api/links/{link['link_id']}/verdict").json()["verdict"]
        == "looks_fine"
    )
    response = CLIENT.get(f"/api/links/{link['link_id']}/open", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:8000/mock/lumora/bill.html"


def test_live_mode_does_not_silently_replay(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "live")
    link = assess("http://localhost:8000/mock/lumora/bill.html")
    CLIENT.post(f"/api/links/{link['link_id']}/investigate")
    card = CLIENT.get(f"/api/links/{link['link_id']}/verdict").json()
    assert card["verdict"] == "inconclusive" and card["investigation"]["mode"] == "live"


def test_missing_fixture_and_reset_are_honest():
    link = assess("http://localhost:8000/mock/lumora/missing.html")
    CLIENT.post(f"/api/links/{link['link_id']}/investigate")
    assert (
        CLIENT.get(f"/api/links/{link['link_id']}/verdict").json()["verdict"]
        == "inconclusive"
    )
    CLIENT.get("/api/reset")
    assert CLIENT.get(f"/api/links/{link['link_id']}/verdict").status_code == 404


def test_secrets_and_local_runtime_are_ignored():
    root = Path(__file__).resolve().parent.parent
    ignores = (root / ".gitignore").read_text()
    assert ".env" in ignores.splitlines() and ".venv/" in ignores.splitlines()


def test_replay_rejects_truncated_completed_fixture(monkeypatch):
    url = "http://localhost:8000/mock/lumora/bill.html"
    monkeypatch.setattr(
        replay.json,
        "loads",
        lambda _: {"/mock/lumora/bill.html": {"start_url": url, "status": "done"}},
    )
    assert replay.investigate(url)["status"] == "failed"
