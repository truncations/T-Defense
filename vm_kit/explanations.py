"""Closed vocabulary: the model selects evidence-backed templates, never actions/verdicts."""

TEMPLATES = {
    "cross_origin_form": "A form requests sensitive information and targets a different origin. Verify that destination independently.",
    "insecure_form": "A form requests sensitive information over HTTP. Do not enter private details.",
    "redirected": "The browser was redirected to another origin. A redirect alone does not establish fraud.",
    "password_request": "The page requests a password. Use the service independently before entering credentials.",
    "download_attempt": "The page attempted a download. The download was canceled and its contents were not inspected.",
    "incomplete": "Some content or requests could not be inspected. This result does not establish safety.",
    "no_observed_flags": "No supported warning signs were observed in this limited read-only inspection. The website is not verified safe.",
}
FLAGS = set(TEMPLATES) - {"no_observed_flags"}


def permitted(flags):
    if (
        not isinstance(flags, dict)
        or set(flags) != FLAGS
        or any(type(v) is not bool for v in flags.values())
    ):
        raise ValueError("Invalid evidence flags")
    found = [key for key in TEMPLATES if flags.get(key)]
    return found or ["no_observed_flags"]


def selection(value, flags):
    allowed = permitted(flags)
    if not isinstance(value, dict) or set(value) != {"template_ids"}:
        raise ValueError("Invalid AI output")
    ids = value["template_ids"]
    if (
        not isinstance(ids, list)
        or not 1 <= len(ids) <= 3
        or any(type(x) is not str or x not in allowed for x in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("AI selected unsupported evidence")
    return ids


def validate_report(report):
    if not isinstance(report, dict) or set(report) != {
        "version",
        "status",
        "flags",
        "template_ids",
        "ai_status",
        "observed_requests",
        "blocked_requests",
    }:
        raise ValueError("Unexpected result fields")
    if (
        type(report["version"]) is not int
        or report["version"] != 1
        or report["status"] not in ("done", "inconclusive")
        or report["ai_status"] not in ("not_requested", "validated", "unavailable")
    ):
        raise ValueError("Invalid result status")
    selection({"template_ids": report["template_ids"]}, report["flags"])
    if report["status"] == "done" and (
        report["flags"]["incomplete"] or report["ai_status"] == "unavailable"
    ):
        raise ValueError("Incomplete result marked done")
    for key in ("observed_requests", "blocked_requests"):
        if type(report[key]) is not int or not 0 <= report[key] <= 500:
            raise ValueError("Invalid request counter")
    if report["status"] == "done" and (
        report["observed_requests"] == 0 or report["blocked_requests"] > 0
    ):
        raise ValueError("Completed report has contradictory counters")
    return report


def summary(report):
    validate_report(report)
    # Always include all supported warning evidence, even if the AI omitted a template.
    return [TEMPLATES[key] for key in permitted(report["flags"])]
