"""Reject incomplete completed evidence instead of interpreting absence as clean."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.safety import allowed_url


class CompletedEvidence(BaseModel):
    model_config = ConfigDict(strict=True)
    mode: Literal["live", "replay"]
    status: Literal["done"]
    start_url: str
    final_url: str
    redirect_chain: list[str]
    cross_origin_final: bool
    fields_requested: list[str]
    canaries_sent_to: list[str]
    canaries_cross_origin: bool
    urgency_phrases: list[str]
    download_attempted: bool
    ai_directed_text: bool
    duration_ms: int = Field(ge=0)
    error: None
    simulated: bool = False
    recorded: bool = False
    form_targets: list[str] = Field(default_factory=list)
    blocked_requests: int = Field(default=0, ge=0)
    uninspected_content: Literal[False] = False


def valid_completed(evidence: dict) -> bool:
    try:
        item = CompletedEvidence.model_validate(evidence)
        targets = [
            item.start_url,
            item.final_url,
            *item.redirect_chain,
            *item.canaries_sent_to,
            *item.form_targets,
        ]
        if not all(allowed_url(url) for url in targets):
            return False
        if not item.redirect_chain or item.redirect_chain[0] != item.start_url:
            return False
        origin = urlsplit(item.start_url).netloc
        if item.cross_origin_final != (urlsplit(item.final_url).netloc != origin):
            return False
        if item.canaries_cross_origin != any(
            urlsplit(url).netloc != origin for url in item.canaries_sent_to
        ):
            return False
        return not item.blocked_requests and (
            item.mode == "live" or item.simulated or item.recorded
        )
    except (ValidationError, TypeError, ValueError):
        return False
