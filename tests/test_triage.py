from fastapi.testclient import TestClient

from app.main import app
from app.triage import badge_for, triage


def test_obvious_pressure_is_flagged():
    result = triage(
        "Your line is suspended today. Verify: http://localhost:8000/mock/lumora/verify.html"
    )
    assert badge_for(result) == "likely_scam"
    assert result["score"] is None


def test_plain_message():
    assert badge_for(triage("Your project meeting is at four.")) == "no_signs"


def test_gray_zone_abstains():
    assert triage(
        "Unusual activity. Please confirm: http://localhost:8000/mock/lumora/help.html"
    )["abstained"]


def test_provider_can_replace_placeholder_without_contract_change(monkeypatch):
    monkeypatch.setattr(
        "app.baseline.predict",
        lambda text: {"label": "scam", "score": 0.9, "category": "provided"},
    )
    result = triage("anything")
    assert result["category"] == "provided"
    assert not result["abstained"]


def test_scenarios_are_placeholder_and_assess_ignores_expected_fields():
    client = TestClient(app)
    rows = client.get("/api/scenarios").json()
    assert len(rows) == 12
    assert all(
        row["source"] == "placeholder"
        and not any(k.startswith("expected_") for k in row)
        for row in rows
    )
    response = client.post(
        "/api/assess",
        json={"message_id": "demo", "text": "Plain reminder", "expected_label": "scam"},
    )
    assert response.json()["badge"] == "no_signs"
