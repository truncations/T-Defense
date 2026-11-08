"""Temporary rules, not a measured classifier. Public interface stays triage(text)."""

import re

from app import baseline

GRAY_LOW = 0.40
GRAY_HIGH = 0.60


def triage(text: str) -> dict:
    provided = baseline.predict(text)
    if provided is not None:
        score = provided.get("score")
        return {
            "label": provided["label"],
            "category": provided.get("category", "unknown"),
            "score": score,
            "abstained": provided.get(
                "abstained", score is None or GRAY_LOW <= score <= GRAY_HIGH
            ),
            "reasons": provided.get("reasons", []),
        }
    lower = text.lower()
    linked = bool(re.search(r"https?://", lower))
    # Five readable rules. No expected labels or scenario IDs enter this function.
    urgency = bool(
        re.search(r"suspend|final notice|act now|immediately|expires today", lower)
    )
    account = bool(re.search(r"verify|confirm.*account|security check", lower))
    gift = bool(re.search(r"gift.?card|reward.*claim|claim.*reward", lower))
    secret = bool(
        re.search(r"password|one.time code|card number|social security", lower)
    )
    uncertain = bool(re.search(r"unusual activity|unrecognized|please confirm", lower))
    reasons = []
    if linked and urgency and account:
        label, category, abstained = "scam", "account_suspension", False
        reasons = [
            "Uses urgent account pressure.",
            "Asks you to verify through a link.",
        ]
    elif linked and gift:
        label, category, abstained = "scam", "gift_card", False
        reasons = ["Asks you to claim a reward through a link."]
    elif linked and (secret or account or uncertain):
        label, category, abstained = "unknown", "account_security", True
        reasons = ["The message needs more context."]
    else:
        label, category, abstained = "legitimate", "general", False
        reasons = ["Temporary rules found no text warning signs."]
    return {
        "label": label,
        "category": category,
        "score": None,
        "abstained": abstained,
        "reasons": reasons,
    }


def badge_for(result: dict) -> str:
    if result["abstained"]:
        return "unsure"
    if result["label"] == "scam":
        return "likely_scam"
    if result["label"] == "suspicious":
        return "suspicious"
    return "no_signs"
