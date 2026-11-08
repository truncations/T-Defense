"""Concrete privacy and output boundaries for future local inference."""

import json

import pytest

from app.local_ai import MAX_OBSERVATIONS, project_evidence, validate_explanation


def test_incomplete_is_not_clean_and_raw_page_data_is_removed():
    projected = project_evidence(
        {"status": "failed", "error": "private message", "start_url": "secret URL"}
    )
    assert projected == {
        "version": 1,
        "observations": [{"id": "e1", "kind": "coverage", "value": "incomplete"}],
    }


def test_completed_projection_removes_raw_strings_and_keeps_known_signals():
    url = "http://localhost:8000/mock/lumora/login"
    evidence = {
        "mode": "replay",
        "status": "done",
        "start_url": url,
        "final_url": url,
        "redirect_chain": [url],
        "cross_origin_final": False,
        "fields_requested": ["password", "private label"],
        "canaries_sent_to": [],
        "canaries_cross_origin": False,
        "urgency_phrases": ["untrusted page instruction"],
        "download_attempted": False,
        "ai_directed_text": True,
        "duration_ms": 1,
        "error": None,
        "simulated": True,
    }
    projected = project_evidence(evidence)
    assert projected["observations"] == [
        {"id": "e1", "kind": "requested_field", "value": "password"},
        {"id": "e2", "kind": "other_fields", "value": True},
        {"id": "e3", "kind": "ai_directed_text", "value": True},
        {"id": "e4", "kind": "urgency_observed", "value": True},
        {"id": "e5", "kind": "coverage", "value": "simulated"},
    ]
    assert MAX_OBSERVATIONS == 16
    serialized = json.dumps(projected)
    assert url not in serialized
    assert "private label" not in serialized
    assert "untrusted page instruction" not in serialized


@pytest.mark.parametrize(
    "output",
    [
        {"findings": [], "verdict": "safe"},
        {"findings": [], "tools": ["shell"]},
        {"findings": [{"observation_id": "e999", "interpretation": "coverage_limit"}]},
        {"findings": [{"observation_id": "e1", "interpretation": "review_behavior"}]},
        {"findings": []},
        {
            "findings": [{"observation_id": "e1", "interpretation": "coverage_limit"}]
            * 2
        },
    ],
)
def test_untrusted_outputs_rejected(output):
    assert (
        validate_explanation(json.dumps(output).encode(), project_evidence({})) is None
    )


def test_valid_selection_preserves_incomplete_coverage():
    raw = b'{"findings":[{"observation_id":"e1","interpretation":"coverage_limit"}]}'
    result = validate_explanation(raw, project_evidence({}))
    assert result == {
        "source": "validated_selection_only",
        "findings": [{"observation_id": "e1", "interpretation": "coverage_limit"}],
    }


def test_large_output_rejected():
    assert validate_explanation(b" " * 4097, project_evidence({})) is None
