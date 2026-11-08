---
name: demo-readiness-check
description: Use at the GATE, in Stage 5, before any commit tagged gate-demo or demo-final, or when asked "is the demo ready?". Walks through the T-Defense demo scenarios A–D in replay and live mode, checks fallbacks, and records demo_backup/ artifacts.
---

# Demo readiness check

Script: `teammate-build-kit/EVALUATION_AND_DEMO.md` Part 2. A demo that works three times in a row beats a better one that works once.

## Walkthrough (do it in replay mode first, then live)
1. Start fresh: stop any server, start it (commands in `AGENTS.md`), and call `GET /api/reset`.
2. Scenario A, "line suspended": red badge → check page → Likely scam with evidence.
3. Scenario B, "order shipped": the badge isn't red → check page → the decoy finds the redirect and card request → Suspicious or Likely scam.
4. Scenario C, "bill ready": No warning signs found, plus "What we couldn't check".
5. Scenario D: "I already entered my info" → the recovery checklist appears.
6. Inconclusive path: stop Playwright from working (for example `DEMO_MODE=live` with an invalid browser path, or the `slow.html` link) → the card says "We couldn't check this".

Automate 2–6 as a Playwright end-to-end test in `tests/test_demo_flow.py` (replay mode), then also do one run by eye.

## Pass criteria
- [ ] All scenarios pass 3 times in a row from a fresh server start, in replay mode.
- [ ] Live mode passes at least once; each decoy run takes under 10 s.
- [ ] No page needs the internet (block external requests and re-run).
- [ ] Text is readable at 380px wide; nothing overflows.
- [ ] `python -m pytest -q` passes and `python -m ruff check .` is clean.

## Artifacts
- Save screenshots of each scenario to `demo_backup/` (Playwright `page.screenshot`).
- Ask the human to screen-record a 90-second run. Codex can't record video. Remind them, and note it in `PROGRESS.md`.
- Tag: `git tag gate-demo` at the GATE, or `git tag demo-final` in Stage 5.

## At the GATE
Stop and tell the human: "The gate passed. Please watch one run in replay mode, then say 'continue' for Stage 3." List anything that's flaky.
