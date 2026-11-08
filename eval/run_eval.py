"""Evaluate integrated starter data only; keep local mock outcomes separate.

Stage0 must produce normalized rows (source=starter,text,label optional) after
inspecting actual files. Placeholder scenarios are deliberately rejected.
"""

import argparse
import json
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path

import httpx

from app import baseline, investigator, replay
from app.triage import triage
from app.verdict import combine

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "verify": "likely_scam",
    "reward": "likely_scam",
    "bill": "looks_fine",
    "track": "likely_scam",
    "help": "likely_scam",
    "fee": "suspicious",
    "attachment": "suspicious",
}
LABELS = {"scam", "legitimate"}


def metrics(
    actual: list[str], predicted: list[str], abstained: list[bool] | None = None
) -> dict:
    if not actual or len(actual) != len(predicted):
        raise ValueError("Nonempty equal-length labels required")
    if any(label not in LABELS for label in actual):
        raise ValueError("Unsupported observed label")
    abstained = abstained or [False] * len(actual)
    tp = sum(
        a == "scam" and p == "scam" and not skip
        for a, p, skip in zip(actual, predicted, abstained, strict=True)
    )
    fp = sum(
        a == "legitimate" and p == "scam" and not skip
        for a, p, skip in zip(actual, predicted, abstained, strict=True)
    )
    fn = sum(
        a == "scam" and (p != "scam" or skip)
        for a, p, skip in zip(actual, predicted, abstained, strict=True)
    )
    resolved = sum(not skip for skip in abstained)
    correct = sum(
        a == p and not skip
        for a, p, skip in zip(actual, predicted, abstained, strict=True)
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    matrix = {
        label: {column: 0 for column in ("scam", "legitimate", "abstained")}
        for label in LABELS
    }
    for a, p, skip in zip(actual, predicted, abstained, strict=True):
        column = "abstained" if skip else p
        if column not in matrix[a]:
            raise ValueError("Unsupported predicted label")
        matrix[a][column] += 1
    return {
        "accuracy": correct / len(actual),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0,
        "abstain_rate": sum(abstained) / len(actual),
        "resolved_accuracy": correct / resolved if resolved else None,
        "matrix": matrix,
    }


def starter_report(dataset: Path, sample: int | None, tuned: bool) -> str:
    if not dataset.exists():
        return "Provided baseline: unavailable. T-Defense-on-provided-data: unavailable.\n\nStarter files and the real classifier have not been integrated. No accuracy, precision, recall, F1, confusion matrix, or abstention metrics are reported on placeholder data."
    rows = json.loads(dataset.read_text(encoding="utf-8"))
    if (
        not isinstance(rows, list)
        or not rows
        or any(
            not isinstance(row, dict)
            or row.get("source") != "starter"
            or not isinstance(row.get("text"), str)
            or not row["text"].strip()
            for row in rows
        )
    ):
        raise ValueError(
            "Evaluation requires inspected source=starter rows; placeholder/team data is forbidden."
        )
    if tuned:
        rows = list(rows)
        random.Random(42).shuffle(rows)
        rows = rows[int(len(rows) * 0.7) :]
    if sample:
        rows = rows[:sample]
    base = [baseline.predict(row["text"]) for row in rows]
    if any(item is None for item in base):
        return "Provided data exists, but the baseline adapter is not integrated. Sponsor metrics remain unavailable. No placeholder metrics were substituted."
    if any(item.get("label") not in LABELS for item in base):
        raise ValueError("Stage0 must normalize observed baseline labels first")
    defended = [triage(row["text"]) for row in rows]
    abstained = [item["abstained"] for item in defended]
    if any(row.get("label") is None for row in rows):
        agreement = sum(
            a["label"] == b["label"] for a, b in zip(base, defended, strict=True)
        ) / len(rows)
        return f"Provided rows lack labels. Baseline agreement: {agreement:.3f}; abstain rate: {sum(abstained) / len(rows):.3f}. Accuracy/precision/recall/F1 are not available."
    actual = [row["label"] for row in rows]
    results = {
        "Provided baseline": metrics(actual, [item["label"] for item in base]),
        "T-Defense triage": metrics(
            actual, [item["label"] for item in defended], abstained
        ),
    }
    lines = [
        f"Evaluated {len(rows)} inspected starter rows. "
        + (
            "Fixed seed42 70/30 holdout; scoring only the30%."
            if tuned
            else "Rules fixed before provided-data evaluation; no tuning on these rows."
        ),
        "",
        "| System | Accuracy | Scam precision | Scam recall | F1 | Abstain rate | Resolved accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        values = [
            result[k]
            for k in (
                "accuracy",
                "precision",
                "recall",
                "f1",
                "abstain_rate",
                "resolved_accuracy",
            )
        ]
        lines.append(
            "| "
            + name
            + " | "
            + " | ".join("n/a" if value is None else f"{value:.3f}" for value in values)
            + " |"
        )
    for name, result in results.items():
        lines.extend(
            [
                "",
                f"{name} confusion matrix (rows actual; columns predictions):",
                "",
                "| Actual | Scam | Legitimate | Abstained |",
                "|---|---:|---:|---:|",
            ]
        )
        for label in ("scam", "legitimate"):
            lines.append(
                "| "
                + label
                + " | "
                + " | ".join(
                    str(result["matrix"][label][key])
                    for key in ("scam", "legitimate", "abstained")
                )
                + " |"
            )
        lines.append("")
    lines.append(
        "Abstentions count as misses for overall accuracy and scam recall; resolved accuracy is separate. These are measurements on the inspected supplied set, not a real-world guarantee."
    )
    return "\n".join(lines)


def build_report(
    dataset: Path, mode: str = "replay", sample: int | None = None, tuned: bool = False
) -> str:
    starter = starter_report(dataset, sample, tuned)
    try:
        commit = (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            ).stdout.strip()
            or "unknown"
        )
    except OSError:
        commit = "unknown"
    # Explicit fixed offset avoids requiring external tzdata on Windows.
    from datetime import timedelta, timezone

    stamp = datetime.now(timezone(timedelta(hours=-6))).isoformat(timespec="seconds")
    lines = [
        "# T-Defense evaluation status",
        "",
        f"Date: {stamp} (Central standard time). Commit: {commit}.",
        "",
        "## Provided baseline and T-Defense on provided data",
        "",
        starter,
        "",
        "## Our own demo pages — not T-Mobile data, not an accuracy claim",
        "",
        "The table checks expected prototype behavior on fictional pages. It is not message-classifier accuracy.",
        "",
        "| Page | Expected | Observed | Evidence mode | Status |",
        "|---|---|---|---|---|",
    ]
    live_available = mode == "live"
    if live_available:
        try:
            with httpx.Client(timeout=1, trust_env=False) as client:
                live_available = (
                    client.get("http://localhost:8000/api/health").status_code == 200
                )
        except httpx.HTTPError:
            live_available = False
    if mode == "live" and not live_available:
        lines.insert(
            8, "Live server unavailable; mock table uses recorded replay instead."
        )
    for page, expected in list(PAGES.items())[: sample or len(PAGES)]:
        url = f"http://localhost:8000/mock/lumora/{page}.html"
        result = (
            investigator.investigate(url) if live_available else replay.investigate(url)
        )
        if live_available and result["status"] != "done":
            result = replay.investigate(url)
            evidence_mode = (
                "recorded replay" if result.get("recorded") else "simulated replay"
            ) + " (live failed)"
        else:
            evidence_mode = (
                "live local browser"
                if live_available
                else "recorded replay"
                if result.get("recorded")
                else "simulated replay"
            )
        card = combine(
            {"label": "legitimate", "abstained": False, "reasons": []}, result
        )
        lines.append(
            f"| {page} | {expected} | {card['verdict']} | {evidence_mode} | {result['status']} |"
        )
    lines.extend(
        [
            "",
            "Attachment contents were not scanned. Real SMS integration, real-site coverage and sponsor metrics are not established by this table.",
            "",
            "## Next action",
            "",
            "Run starter-inspector when provided files arrive; inspect/normalize their real schema and integrate the baseline before reporting sponsor-set metrics. Mark tuned=true when rules/thresholds were changed using provided data; score only the held-out30%.",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/starter_eval.json")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/results.md")
    parser.add_argument(
        "--mode", choices=["live", "replay"], default=os.getenv("DEMO_MODE", "replay")
    )
    parser.add_argument("--sample", type=int)
    parser.add_argument("--tuned", action="store_true")
    args = parser.parse_args()
    if args.sample is not None and args.sample < 1:
        parser.error("--sample must be positive")
    try:
        report = build_report(args.dataset, args.mode, args.sample, args.tuned)
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(
        f"Saved evaluation status to {args.output}. Mock-page outcomes are not an accuracy claim."
    )


if __name__ == "__main__":
    main()
