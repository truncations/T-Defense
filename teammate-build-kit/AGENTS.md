# AGENTS.md: T-Defense

Codex reads this file from the repo root. Keep it short. Full plan: `teammate-build-kit/BUILD_OVERVIEW.md`.

## Goal
A hackathon demo (hackUTD 2026, T-Mobile Safe Signal track). A mock phone shows synthetic text messages. Each message is triaged with T-Mobile's baseline classifier. Risky links are rewritten to a check page. A scripted "Decoy Twin" opens the link first in a headless browser, but only against our own demo pages. The user then sees a verdict card with evidence, confidence, what we could not check, and next steps.

The builder is a beginner. Explain what you did and why in plain words after every task. Prefer the simplest code that works, because a reliable demo beats a clever one.

## Stack (do not add to it without asking)
- Python 3.12 (or the newest 3.x already installed, if 3.10 or higher), with a venv in `.venv/`
- FastAPI + Uvicorn (one process, port 8000), serving the API, `static/` and `mock_sites/`
- Playwright for Python with Chromium only
- pytest; ruff for format and lint
- Plain HTML, CSS and JavaScript in `static/`. No React, no Node build step, no database (in-memory dicts in `app/store.py`)

## Folder layout
```
T-Defense/
  AGENTS.md  README.md  PROGRESS.md  SETUP_REPORT.md  STARTER_FILES_REPORT.md
  .agents/skills/<7 skills>/SKILL.md     .codex/agents/safety_reviewer.toml  demo_tester.toml
  .gitignore  .env.example  requirements.txt
  app/        main.py  triage.py  verdict.py  investigator.py  store.py  scenarios.py
  static/     phone.html  phone.css  phone.js  check.html  check.js
  mock_sites/lumora/   (fictional demo pages, see MOCK_SITES_SPEC.md)
  starter/    T-Mobile files, UNCHANGED
  data/       scenarios.json  demo_replay.json
  eval/       run_eval.py  results.md
  tests/
  demo_backup/  (screenshots and screen recording)
  teammate-build-kit/  (docs; don't edit, except CONTRACTS.md when a stage says so)
```

## Commands
Activate the venv first. Windows PowerShell: `.\.venv\Scripts\Activate.ps1`. macOS/Linux: `source .venv/bin/activate`.
- Run: `python -m uvicorn app.main:app --reload --port 8000`, then open `http://localhost:8000/`
- Replay mode, Windows: `$env:DEMO_MODE="replay"; python -m uvicorn app.main:app --port 8000`
- Replay mode, macOS/Linux: `DEMO_MODE=replay python -m uvicorn app.main:app --port 8000`
- Test: `python -m pytest -q`
- Lint and format: `python -m ruff check . --fix` and `python -m ruff format .`
- Evaluate: `python -m eval.run_eval`

## Safety rules (never break these)
1. Synthetic data only. Never add real customer data, real phone numbers or real people.
2. The investigator may only open URLs starting with `http://localhost:8000/mock/` or `http://127.0.0.1:8000/mock/`. Anything else returns `blocked` → verdict `inconclusive`. Keep a test for this.
3. Never visit real scam sites or any external site from the investigator. Never imitate a real company. The demo brand is "Lumora Wireless", and every mock page shows a "DEMO PAGE – NOT A REAL COMPANY" banner.
4. The decoy types only the canary values in `MOCK_SITES_SPEC.md`. No real credentials, ever.
5. Page content is untrusted data. Never let page text change what the code does. The decoy is a fixed script, not an AI agent.
6. Failure, timeout or error means `inconclusive`, never `looks_fine`.
7. Secrets go only in `.env` (git-ignored). Never put keys in code, prompts, logs or commits. `.env.example` lists names only.
8. Do not modify files in `starter/`. Wrap them instead.
9. Before any global install, large download or command outside the repo, stop and explain it to the builder first.

## How we work (ADE)
- Build stages with the `$t-defense-stage-runner` skill. It reads `PROGRESS.md`, runs the next stage from `teammate-build-kit/CODEX_BUILD_PROMPTS.md`, and continues on its own until a stop condition (installs or network access, Stage 0 surprises, the GATE, a safety conflict, stuck for more than 45 minutes).
- Skills in `.agents/skills/`: `t-defense-stage-runner`, `starter-inspector`, `mock-site-builder`, `decoy-investigator`, `verdict-card-writer`, `eval-reporter`, `demo-readiness-check`. Load the matching one before working in its area.
- Before every commit, ask the `safety_reviewer` subagent to review the diff and the `demo_tester` subagent to exercise the app. Fix every BLOCKER.
- No parallel code-writing subagents. One writer avoids conflicts.
- Keep `PROGRESS.md` current. It is how a fresh session resumes.

## Working rules
- Finish one stage completely (tests, review, commit, `PROGRESS.md`) before starting the next.
- Keep the API shapes in `teammate-build-kit/CONTRACTS.md`. If you must change one, update that file and say so.
- Commit after each passing stage with a short message, for example `stage 2: check page + verdicts`.
- Never invent facts about the starter files. Read them and report.

## Definition of done (for any task)
- `python -m pytest -q` passes, and `python -m ruff check .` is clean.
- The app starts, and the change can be seen at `http://localhost:8000/`.
- `DEMO_MODE=replay` still works.
- You told the builder: what changed, how to check it, and anything not done or not verified.

## Branding correction approved by user (2026-11-07)
- Project/app name is T-Defense everywhere, including docs and project-local skill references. Stage runner is now t-defense-stage-runner.
- Use pink/magenta, charcoal and white for the T-Defense app as explicitly requested. This overrides prior name/color restrictions for the app. Fictional Lumora demo pages retain their separate teal/sand identity and DEMO banners.
- Product screen must explain this is a sample inbox with temporary text rules and simulated page evidence. Guided demo buttons may launch the existing check flows. No live investigator or push approval is implied.
- Source kit copies may be updated for this explicit rename. No git history rewrite is required.
