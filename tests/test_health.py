from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
