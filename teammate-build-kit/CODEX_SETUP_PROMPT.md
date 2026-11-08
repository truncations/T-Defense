# CODEX_SETUP_PROMPT

**Normal use:** you don't paste this. The ADE bootstrap prompt in `CODEX_ADE_SETUP.md` (Step 3) tells Codex to follow steps 3–10 below. Paste this whole block yourself only as a fallback, if the bootstrap fails.

**Why this step exists:** if the environment is broken, every feature after it is broken too. This prompt only sets things up and proves the chain works end to end. It builds **no features**.

**Before you paste:** you're in the `T-Defense/` folder. `AGENTS.md` is at its root. The kit is in `T-Defense/teammate-build-kit/`, and T-Mobile's files are in `T-Defense/starter/` (it's fine if that folder is still empty).

Copy everything inside the block into Codex:

```text
You are setting up the development environment for the T-Defense hackathon project. Read AGENTS.md and teammate-build-kit/TOOLING_AND_SKILLS.md first. Do NOT build any features yet.

I am a beginner. Before running any command that installs something globally, downloads something large, or touches files outside this folder (for example installing Python or git, or `python -m playwright install chromium`), stop, tell me in one or two plain sentences what it does and why, and wait for my "ok".

Steps:
1. Tell me my OS and check: python --version, git --version. If Python is under 3.10 or missing, stop and tell me how to install 3.12.
2. If this folder isn't a git repo yet, run `git init` and make the first commit containing only AGENTS.md and teammate-build-kit/.
3. Create .gitignore (.venv/, .env, __pycache__/, .pytest_cache/, .ruff_cache/, *.pyc) and .env.example with placeholder names only: DEMO_MODE=live, USE_LLM=false, OPENAI_API_KEY=
4. Create the venv in .venv and tell me the exact activate command for my OS.
5. Inside the venv, install: fastapi uvicorn httpx pytest ruff playwright. Then ask before running `python -m playwright install chromium`.
6. Create the folder layout from AGENTS.md with empty placeholder files where needed. Do not touch starter/.
7. Hello world, minimal code only:
   a. app/main.py: GET /api/health returns {"status": "ok"}; serves static/ at / and mock_sites/ at /mock.
   b. static/phone.html: fetches /api/health and shows "Backend OK" or "Backend DOWN".
   c. mock_sites/lumora/index.html: a one-line page titled "Lumora Wireless DEMO".
   d. tests/test_health.py: uses FastAPI TestClient to check /api/health.
   e. tests/test_browser_smoke.py: starts the app on port 8000 in a background thread (or uses a pytest fixture), opens http://localhost:8000/mock/lumora/index.html in headless Chromium with Playwright, and asserts the title contains "Lumora".
8. Run: python -m pytest -q and python -m ruff check . Then start the server with `python -m uvicorn app.main:app --port 8000` and tell me to open http://localhost:8000/ and confirm I see "Backend OK".
9. Pin versions: python -m pip freeze > requirements.txt
10. Write SETUP_REPORT.md: OS, Python version, every package and version from requirements.txt, each of the 4 hello-world checks (pass/fail), anything that failed or was skipped, and every global install I approved.
11. Commit: "setup: environment + hello world".

Stop after step 11. Summarize in plain words what works, what doesn't, and what I should check by hand. Do not start Stage 0.
```

**Stop and check (you, by hand):**
- [ ] `http://localhost:8000/` shows "Backend OK".
- [ ] `python -m pytest -q` shows 2 passed.
- [ ] `SETUP_REPORT.md` exists and lists versions.
- [ ] `git log --oneline` shows the setup commit.

If anything failed, paste the error back into Codex and say: "Fix only this setup problem, then re-run the four checks." Don't move on until all four pass.
