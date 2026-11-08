"""Offline preparation boundary; no model calls or browser permissions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.evidence import valid_completed

MAX_OBSERVATIONS = 16
MAX_OUTPUT_BYTES = 4096
FIELD_KINDS = frozenset(
    {"password", "card_number", "ssn", "one_time_code", "gift_card", "pin"}
)


class ExplanationItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    observation_id: str = Field(max_length=8)
    interpretation: Literal[
        "review_requested_field", "review_behavior", "coverage_limit"
    ]


class ModelExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    findings: list[ExplanationItem] = Field(max_length=MAX_OBSERVATIONS)


def project_evidence(evidence: dict) -> dict:
    """Whitelist categories, not arbitrary page strings or destination URLs."""
    observations = []

    def add(kind: str, value: str | bool) -> None:
        observations.append(
            {"id": f"e{len(observations) + 1}", "kind": kind, "value": value}
        )

    if evidence.get("status") != "done" or not valid_completed(evidence):
        add("coverage", "incomplete")
    else:
        for field in sorted(set(evidence["fields_requested"]) & FIELD_KINDS):
            add("requested_field", field)
        if set(evidence["fields_requested"]) - FIELD_KINDS:
            add("other_fields", True)
        for key in (
            "cross_origin_final",
            "canaries_cross_origin",
            "download_attempted",
            "ai_directed_text",
        ):
            if evidence.get(key):
                add(key, True)
        if evidence.get("urgency_phrases"):
            add("urgency_observed", True)
        if evidence.get("simulated"):
            add("coverage", "simulated")
        elif evidence.get("mode") == "replay":
            add("coverage", "recorded_replay")
        if not observations:
            add("coverage", "no_flags_in_tested_steps")
    return {"version": 1, "observations": observations[:MAX_OBSERVATIONS]}


def validate_explanation(raw: bytes, projected: dict) -> dict | None:
    """Reject arbitrary prose/tools/verdicts; render only trusted templates.

    Evidence references alone do not prove faithful prose. This initial boundary
    deliberately supports no free-form model prose until quality is evaluated.
    """
    if len(raw) > MAX_OUTPUT_BYTES:
        return None
    try:
        output = ModelExplanation.model_validate_json(raw)
    except (ValidationError, ValueError):
        return None
    observations = {item["id"]: item for item in projected["observations"]}
    seen = set()
    findings = []
    for item in output.findings:
        observation = observations.get(item.observation_id)
        if observation is None or item.observation_id in seen:
            return None
        seen.add(item.observation_id)
        expected = (
            "coverage_limit"
            if observation["kind"] == "coverage"
            else "review_requested_field"
            if observation["kind"] == "requested_field"
            else "review_behavior"
        )
        if item.interpretation != expected:
            return None
        findings.append(
            {"observation_id": item.observation_id, "interpretation": expected}
        )
    required = {
        item["id"] for item in projected["observations"] if item["kind"] == "coverage"
    }
    if not required.issubset(seen):
        return None
    return {"source": "validated_selection_only", "findings": findings}
