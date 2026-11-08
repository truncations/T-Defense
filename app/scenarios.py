import json
from pathlib import Path


def load_scenarios() -> list[dict]:
    rows = json.loads(
        (Path(__file__).resolve().parent.parent / "data/scenarios.json").read_text(
            encoding="utf-8"
        )
    )
    return [
        {k: v for k, v in row.items() if not k.startswith("expected_")} for row in rows
    ]
