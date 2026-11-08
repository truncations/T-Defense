"""Replay recorded local browser evidence, or explicitly labeled simulated fixtures."""

import json
from pathlib import Path
from urllib.parse import urlsplit

from app.evidence import valid_completed
from app.safety import allowed_url


def investigate(url: str) -> dict:
    if not allowed_url(url):
        return {
            "mode": "replay",
            "status": "blocked",
            "start_url": url,
            "simulated": True,
            "error": "Only local demo pages can be checked.",
        }
    try:
        fixtures = json.loads(
            (
                Path(__file__).resolve().parent.parent / "data/demo_replay.json"
            ).read_text(encoding="utf-8")
        )
        result = fixtures.get(urlsplit(url).path)
        if not result or result["start_url"] != url:
            raise ValueError("No simulated replay fixture exists for this exact URL.")
        targets = [
            result.get("final_url", url),
            *result.get("redirect_chain", []),
            *result.get("canaries_sent_to", []),
        ]
        if any(not allowed_url(target) for target in targets):
            raise ValueError("Replay fixture contains a blocked URL.")
        if result.get("status") == "done" and not valid_completed(result):
            raise ValueError("Incomplete completed evidence.")
        return dict(result, mode="replay", simulated=result.get("simulated", False))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {
            "mode": "replay",
            "status": "failed",
            "start_url": url,
            "simulated": True,
            "error": "Simulated evidence is unavailable.",
        }
