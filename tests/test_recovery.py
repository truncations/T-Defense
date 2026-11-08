import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    "category,expected",
    [
        ("payment", "card issuer"),
        ("identity", "credit freeze"),
        ("gift_card", "receipt"),
        ("unknown", "two-step"),
    ],
)
def test_recovery_has_category_advice_and_common_steps(category, expected):
    data = TestClient(app).get("/api/recovery", params={"category": category}).json()
    text = " ".join(data["steps"])
    assert expected in text and "7726" in text and "Change the password" in text
    assert "http" not in text
