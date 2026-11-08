# T-Defense

A local mock messaging app that warns before you follow a concerning link or share information. The replay GATE is approved; **live Decoy Twin checks now run against fictional local demo pages**.

All 12 messages are synthetic (`source: "placeholder"`). Text assessment still uses temporary rules because the provided classifier, dataset and taxonomy have not arrived. No accuracy claims or placeholder-data metrics are reported.

## Run

From the repository root on Windows (Python 3.13.7 tested):

```powershell
$env:DEMO_MODE = "live"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open http://localhost:8000/. Stop with Ctrl+C. Run live mode without `--reload` on Windows. Use `$env:DEMO_MODE = "replay"` for the backup mode; it reuses clearly labeled browser evidence recorded on our local mock pages. The app reads environment variables and does not automatically load `.env`. The default when unset remains replay.

## Try it

- **Obvious scam:** urgent text plus a page requesting fake credentials and payment details.
- **Hidden risk:** ordinary-looking tracking text; the page redirects and requests a card.
- **Plain bill notice:** no observed page warning signs, with explicit limitations.
- **LumoraFiles:** harmless attachment-download attempt; the decoy cancels it and the card says its contents were not scanned. “Open anyway” is disabled.
- **DemoAccount:** slow page; a failed check becomes inconclusive.

An in-app warning appears when temporary text rules flag examples. Hover/focus/tap a badge for reasons. Concerning check cards show a prominent warning to keep attachments closed and avoid passwords, card details or codes. These components operate inside the demo; they do not monitor other apps or create OS push notifications. Brief highlights respect reduced-motion preferences.

## Setup on another machine

Use Python 3.10+ and Git. Downloads require network access; no global packages are needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$pwd\.playwright"
.\.venv\Scripts\python.exe -m playwright install chromium --only-shell
New-Item -ItemType Directory -Path starter -Force
```

On Unix use `.venv/bin/python` and `export DEMO_MODE=live`. Activation is optional; the explicit interpreter path works directly. On Windows, optional activation is `.\.venv\Scripts\Activate.ps1`.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Stop any manual server first: tests own port 8000. They cover live local checks, replay flows, strict evidence, URL boundaries, blocked requests, popups/frames, worker timeout, mobile layout and warning interactions. The suite includes an intentional slow-page test. If the sandbox's temporary directory is blocked, create `work/tmp` and set `$env:TEMP = "$pwd\work\tmp"; $env:TMP = $env:TEMP`.

## How it works

FastAPI serves plain HTML/CSS/JavaScript and JSON APIs. `triage(text)` returns text clues and check tokens. Risky or uncertain links start background jobs; other links start when their check page opens. Jobs run Playwright's fixed script in a bounded worker process, with up to two concurrent investigations. Cache entries share observed results for an exact URL/mode during this server run. Store locks are released during browser work; reset-generation checks prevent stale jobs restoring cleared state.

The decoy waits for scripted redirects, inspects input metadata and urgency/AI-directed text, fills known fields with the kit's canary values, and submits one form. It records canonical URLs without form-query values, requested fields, submission targets, blocked requests and download attempts. Evidence validation precedes verdict combination. It does not follow instructions written on a page.

See [DEMO_EXPLAINED.md](DEMO_EXPLAINED.md), [PROGRESS.md](PROGRESS.md), and [teammate-build-kit/CONTRACTS.md](teammate-build-kit/CONTRACTS.md).

## Limits and safeguards

- Only HTTP localhost or 127.0.0.1 on port 8000 under `/mock/` can be initial targets. Userinfo, encoded/traversal paths, queries and fragments are rejected for initial URLs.
- Browser requests stay within the local mock paths; the local mock stylesheet is the only static-resource exception. Form queries carry only canaries. Other hosts, ports and API paths are blocked. WebSockets and service workers are blocked.
- A fresh nonpersistent context is used. Only listed fake canary values are filled. Downloads are canceled; attachment contents are not scanned.
- Extra pages/frames are not investigated, so their appearance fails closed. The short observation window may miss delayed or visitor-dependent behavior. This is a constrained local prototype, not an internet-facing browser sandbox.
- The worker has a nine-second watchdog and shorter internal action budget. Queued jobs can take longer to begin; the card times out to inconclusive after waiting.
- Missing, malformed, blocked and failed checks never yield “No warning signs found.” Strong scam text may retain its warning while disclosing incomplete page evidence.
- “Open anyway” requires a completed eligible local verdict on the server and is prohibited for download-attempt results.
- State is process-local. Restart or `GET /api/reset` clears it and invalidates tokens. No database or real-message integration exists.
- `.env`, browser binaries, `.venv` and temporary files are ignored. No keys are needed for the demo. Use `--no-access-log` to avoid logging canary form queries.

## Next steps and project process

Place provided files unchanged in `starter/`, then run `$starter-inspector`. Stage 0 remains deferred. `app/baseline.py` is the replaceable boundary; do not calculate accuracy on placeholder scenarios. Category recovery and the evaluation runner are implemented. Run `.\.venv\Scripts\python.exe -m eval.run_eval --mode replay` for the current report, or use `--mode live` with the local server running. Provided-data metrics remain unavailable until Stage0 inspects and integrates the starter files.

The repository is https://github.com/truncations/T-Defense.git, with its existing MIT license/history retained. GATE approval permits publication. Native Git credentials are unavailable in this session; the connected GitHub account can publish the reviewed source snapshot. Original local stage commits and generated media are preserved on a local stage-history archive branch when aligning the source branch. Publication status is recorded in PROGRESS.md. Project-local rules, seven skills and two reviewer roles continue to govern stage commits; use `$t-defense-stage-runner` to resume.

Screenshots and the current silent walkthrough are generated locally in `demo_backup/`; binary backups are excluded from public source publication. Their own on-screen labels identify live versus recorded replay evidence. Reset demo on the homepage clears stored checks and issues fresh tokens.

Credits: teammate build kit for the plan/workflow. Sponsor starter files are not yet supplied or integrated. Lumora Wireless is fictional.

Documentation: [Playwright network controls](https://playwright.dev/python/docs/network), [browser contexts](https://playwright.dev/python/docs/api/class-browsercontext), [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/).
