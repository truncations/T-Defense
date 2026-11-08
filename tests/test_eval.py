import json

import pytest

from eval.run_eval import build_report, metrics, starter_report


def test_missing_starter_reports_unavailable_not_placeholder_metrics(tmp_path):
    report = build_report(tmp_path / "missing.json", mode="replay", sample=2)
    assert "No accuracy" in report and "not an accuracy claim" in report
    assert "| verify | likely_scam | likely_scam |" in report


def test_placeholder_data_is_rejected(tmp_path):
    path = tmp_path / "rows.json"
    path.write_text(
        json.dumps(
            [{"source": "placeholder", "text": "Synthetic example", "label": "scam"}]
        )
    )
    with pytest.raises(ValueError, match="forbidden"):
        starter_report(path, None, False)


def test_metrics_math_and_abstention_are_separate():
    result = metrics(
        ["scam", "legitimate", "scam"],
        ["scam", "legitimate", "unknown"],
        [False, False, True],
    )
    assert result["resolved_accuracy"] == 1
    assert result["matrix"]["scam"]["abstained"] == 1
    assert result["recall"] == 0.5


def test_integrated_adapter_table_format_and_no_label_leakage(tmp_path, monkeypatch):
    from eval import run_eval

    rows = [
        {"source": "starter", "text": "Unit fixture A", "label": "scam"},
        {"source": "starter", "text": "Unit fixture B", "label": "legitimate"},
    ]
    path = tmp_path / "unit-fixture.json"
    path.write_text(json.dumps(rows))
    seen = []

    def predict(text):
        seen.append(text)
        return {
            "label": "scam" if text.endswith("A") else "legitimate",
            "score": 0.9,
            "abstained": False,
            "reasons": [],
        }

    monkeypatch.setattr(run_eval.baseline, "predict", predict)
    report = starter_report(path, None, False)
    assert report.index("| T-Defense triage |") < report.index("confusion matrix")
    assert all(
        isinstance(value, str) and value.startswith("Unit fixture") for value in seen
    )
