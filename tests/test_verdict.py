import copy
import json
from pathlib import Path

import pytest

from app.verdict import combine

FIXTURES = json.loads(
    (Path(__file__).resolve().parent.parent / "data/demo_replay.json").read_text()
)
PLAIN = {"label": "legitimate", "abstained": False, "reasons": []}


@pytest.mark.parametrize(
    "page,expected",
    [
        ("verify", "likely_scam"),
        ("reward", "likely_scam"),
        ("bill", "looks_fine"),
        ("track", "likely_scam"),
        ("help", "likely_scam"),
        ("fee", "suspicious"),
        ("slow", "inconclusive"),
    ],
)
def test_four_verdicts(page, expected):
    card = combine(PLAIN, FIXTURES[f"/mock/lumora/{page}.html"])
    assert card["verdict"] == expected
    assert len(card["evidence"]) <= 3 and len(card["next_steps"]) <= 3
    assert card["unknowns"]


@pytest.mark.parametrize("status", ["failed", "blocked", "pending", "unexpected"])
def test_failures_never_look_fine(status):
    assert combine(PLAIN, {"status": status})["verdict"] == "inconclusive"


def test_missing_and_strong_text_failures():
    assert combine(PLAIN, None)["verdict"] == "inconclusive"
    strong = {"label": "scam", "abstained": False, "reasons": ["Urgent pressure."]}
    assert combine(strong, {"status": "failed"})["verdict"] == "likely_scam"
    assert (
        combine(strong, FIXTURES["/mock/lumora/bill.html"])["verdict"] == "suspicious"
    )


def test_hidden_instructions_cannot_make_clean_verdict():
    inv = copy.deepcopy(FIXTURES["/mock/lumora/bill.html"])
    inv["ai_directed_text"] = True
    assert combine(PLAIN, inv)["verdict"] == "suspicious"


def test_unrecognized_field_still_counts_as_finding():
    inv = copy.deepcopy(FIXTURES["/mock/lumora/bill.html"])
    inv["fields_requested"] = ["unrecognized_sensitive_field"]
    assert combine(PLAIN, inv)["verdict"] != "looks_fine"


def test_truncated_completed_evidence_fails_closed():
    card = combine(PLAIN, {"status": "done"})
    assert card["status"] == "failed" and card["verdict"] == "inconclusive"


@pytest.mark.parametrize(
    "field,value",
    [
        ("error", "some error"),
        ("fields_requested", None),
        ("canaries_cross_origin", "false"),
        ("duration_ms", -1),
        ("cross_origin_final", True),
        ("recorded", False),
    ],
)
def test_malformed_completed_evidence_fails_closed(field, value):
    inv = copy.deepcopy(FIXTURES["/mock/lumora/bill.html"])
    inv[field] = value
    assert combine(PLAIN, inv)["verdict"] == "inconclusive"


def test_clean_bill_does_not_receive_spam_reporting_advice():
    card = combine(PLAIN, FIXTURES["/mock/lumora/bill.html"])
    assert not any("7726" in step for step in card["next_steps"])
