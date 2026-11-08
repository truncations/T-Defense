# T-Defense replay GATE review

Status: replay GATE APPROVED by the user. The entries below preserve the original review checkpoint; current live-build details are in PROGRESS.md and DEMO_EXPLAINED.md. GitHub push has not completed because local credentials are unavailable.

## Open the app

The development server can run at http://localhost:8000/. If it has stopped:

```powershell
Set-Location C:\Users\Aaron\Documents\programming\T-Defense
$env:DEMO_MODE = "replay"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

## What to review

- LumoraAlerts: Likely scam, with simulated sensitive-form and different-origin submission evidence.
- LumoraOrders: ordinary-looking text, then a Likely scam card because the simulated page redirects and asks for a card.
- LumoraBilling: No warning signs found, with limits and independent-contact advice.
- LumoraDelivery: Suspicious.
- DemoNotice / DemoAccount: external-link block or simulated timeout yields We couldn’t check this.
- Return using Go back (recommended). All check addresses contain opaque tokens.

All messages have source="placeholder". Triage uses temporary rules. Replay findings are hand-written examples, not recorded live investigation output. No accuracy numbers were computed or reported.

## Validation

- Full suite: 57 passed; Ruff clean.
- GATE walkthrough: 3 consecutive passes from fresh server starts (5.18s, 5.12s, 5.17s).
- Browser test coverage: scam, redirect, clean, suspicious, blocked, timeout, expired token, tokenized address, recovery placeholder, local-only requests, 380px no-overflow.
- Safety reviewer: OK. Strict completed-evidence validation fixed a fail-open issue found during review; regressions now cover incomplete/malformed fixtures.
- Demo tester: PASS. Independent screenshot/source/lint review; parent browser execution evidence used because the child sandbox hung on TestClient. Main-environment tests passed.
- .env and variants ignored; only empty-key .env.example tracked. No .env history or detected key/private-key patterns in staged source. Browser binaries, virtual environment and temporary files are ignored.
- Existing GitHub history and MIT license retained; main tracks origin/main. No force-push or history replacement.
- Screenshots: demo_backup/gate-*.png. Silent browser recording: demo_backup/gate-walkthrough.webm (90+ seconds; simulated replay walkthrough, not a live decoy run).

## Still deferred

- Stage 0: inspect provided starter files with $starter-inspector, run the real baseline, integrate the adapter, replace placeholders, finalize contracts. starter/ is currently empty.
- Stage 3: live Playwright Decoy Twin, after GATE approval.
- Stage 4: complete category recovery checklists and evaluation on provided data. The current recovery control explicitly says the full checklist is unavailable.
- Stage 5: final freeze, judging rehearsal and submission materials.

## Your review

Watch one run in replay mode. The silent recording can help, or screen-record your own 90-second run for the team as the kit recommends.

Tell Codex whether you approve the GATE, whether to push the passing commits to GitHub, and whether to begin Stage 3. Approval has not been assumed.

## Updated review: T-Defense branding and guided demo

Use Start the demo on the homepage: Obvious scam, Hidden risk, or Plain bill notice. The new explanation is visible on mobile and desktop. Pink/magenta app styling and the project name follow the user's correction. See DEMO_EXPLAINED.md for the actual backend flow and its limits. The full updated suite passes 57 tests; human GATE approval is still pending.
