"""Validate untrusted guest JSON before rendering a fixed-template host report."""

import json
import sys

from vm_kit.explanations import summary, validate_report


def main():
    data = sys.stdin.read(65537)
    if len(data) > 65536:
        raise ValueError("Guest report exceeds limit")
    report = validate_report(json.loads(data))
    print(
        json.dumps(
            {
                "inspection": report,
                "summary": summary(report),
                "scope": "Origin-only, read-only inspection; not a safety certification.",
            }
        )
    )


if __name__ == "__main__":
    main()
