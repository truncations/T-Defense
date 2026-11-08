import re
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    "page", ["index", "verify", "reward", "bill", "track", "help", "fee", "collect"]
)
def test_mock_pages_are_labeled_and_local(page):
    response = TestClient(app).get(f"/mock/lumora/{page}.html")
    assert response.status_code == 200
    assert "DEMO PAGE – NOT A REAL COMPANY – built for hackUTD" in response.text
    for url in re.findall(r'https?://[^\s"<>]+', response.text):
        assert urlsplit(url).hostname in {"localhost", "127.0.0.1"}
    if page == "bill":
        assert "<form" not in response.text and "<script" not in response.text
