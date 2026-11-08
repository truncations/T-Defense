"""Evidence templates. Incomplete checks never become looks_fine."""

from app.evidence import valid_completed

UNKNOWN = [
    "A real page may behave differently for another visitor.",
    "We did not check who owns this website.",
]
DEFAULT_STEPS = [
    "Go back and leave this link closed.",
    "Contact the company using the number on your bill or card.",
    "Report the text by forwarding it to 7726 (SPAM).",
]


def combine(triage: dict, investigation: dict | None) -> dict:
    evidence = []
    unknowns = list(UNKNOWN)
    strong_triage = triage.get("label") == "scam" and not triage.get("abstained", True)
    status = (investigation or {}).get("status", "pending")
    if status == "done" and not valid_completed(investigation):
        investigation = dict(
            investigation,
            status="failed",
            error="Completed evidence was incomplete or invalid.",
        )
        status = "failed"
    if (investigation or {}).get("simulated"):
        unknowns.insert(
            0, "This is hand-written simulated evidence. No live browser ran."
        )
    if (investigation or {}).get("mode") == "replay" and (investigation or {}).get(
        "recorded"
    ):
        unknowns.insert(
            0,
            "This replays a recorded local demo check; the page was not rechecked now.",
        )
    if (investigation or {}).get("download_attempted"):
        unknowns.append("Attachment contents were not opened or scanned.")
    if status != "done":
        unknowns.insert(0, "The page could not be checked.")
        verdict = "likely_scam" if strong_triage else "inconclusive"
        evidence = triage.get("reasons", [])[:2] if strong_triage else []
        confidence = "medium" if strong_triage else "low"
        reason = (
            "Text clues raised concerns; the page check is incomplete."
            if strong_triage
            else "There is not enough page evidence to reach a conclusion."
        )
    else:
        inv = investigation
        fields = inv.get("fields_requested", [])
        sensitive = bool(
            set(fields)
            & {"password", "card_number", "ssn", "one_time_code", "gift_card", "pin"}
        )
        field_names = {
            "password": "a password",
            "card_number": "a card number",
            "ssn": "a Social Security number",
            "one_time_code": "a one-time code",
            "gift_card": "gift-card codes",
            "pin": "a card PIN",
        }
        if sensitive:
            names = [field_names[field] for field in fields if field in field_names]
            evidence.append("The page asks for " + " and ".join(names[:2]) + ".")
        if inv.get("canaries_cross_origin"):
            evidence.append(
                "The simulated decoy's details go to a different local demo site."
                if inv.get("simulated")
                else "The page sent the decoy’s fake details to a different local demo site."
            )
        elif inv.get("cross_origin_final"):
            evidence.append("The page redirects to a different local demo site.")
        if inv.get("ai_directed_text"):
            evidence.append("Hidden text tries to instruct automated checkers.")
        if inv.get("urgency_phrases"):
            evidence.append("The page uses time pressure to rush a decision.")
        if inv.get("download_attempted"):
            evidence.append("The page attempts a download.")
        # Unknown field types also count as findings: never silently call them clean.
        findings = bool(
            fields
            or inv.get("canaries_sent_to")
            or inv.get("redirect_chain", [])[1:]
            or evidence
        )
        strong = inv.get("canaries_cross_origin") or (
            sensitive
            and (
                inv.get("urgency_phrases")
                or inv.get("cross_origin_final")
                or inv.get("ai_directed_text")
            )
        )
        if strong:
            verdict, confidence, reason = (
                "likely_scam",
                "high",
                (
                    "The simulated page behavior shows several warning signs."
                    if inv.get("simulated")
                    else "The decoy observed several page warning signs."
                ),
            )
        elif findings or strong_triage:
            verdict, confidence, reason = (
                "suspicious",
                "medium",
                "At least one warning sign needs a closer look.",
            )
            if not evidence:
                evidence = ["Text clues or page requests still raise concerns."]
        else:
            verdict, confidence, reason = (
                "looks_fine",
                "low",
                (
                    "The simulated check has no page warning signs."
                    if inv.get("simulated")
                    else "The completed local check found no page warning signs."
                ),
            )
            evidence = [
                (
                    "The simulated page has no sensitive forms, redirects, or urgency."
                    if inv.get("simulated")
                    else "The decoy found no sensitive forms, redirects, or urgency."
                )
            ]
    return {
        "status": status,
        "verdict": verdict,
        "confidence": confidence,
        "confidence_reason": reason,
        "evidence": evidence[:3],
        "unknowns": unknowns,
        "next_steps": (
            [
                "Open the company’s app directly to view your bill.",
                "Keep the limits of this demo check in mind.",
                "Contact the company independently if anything seems unusual.",
            ]
            if verdict == "looks_fine"
            else list(DEFAULT_STEPS)
        ),
        "investigation": investigation,
        "triage": triage,
    }
