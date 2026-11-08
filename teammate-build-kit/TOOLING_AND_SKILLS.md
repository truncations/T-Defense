# TOOLING_AND_SKILLS

Rule: use the fewest tools that work, because every tool is something that can break at 3 a.m. Each item lists what it is, why we need it, how to install it, a one-line check, how to undo it, its priority, and the time it takes.

**Version numbers:** none are pinned here. We didn't want to state versions from memory. Codex installs the current version and records what it got in `SETUP_REPORT.md`, then pins those exact versions in `requirements.txt` (`pip freeze > requirements.txt`) so nothing shifts mid-hackathon.

⚠️ = needs a global install, a large download, or access outside the repo. **Codex must explain it to you and wait for your OK before running it.**

---

## Runtimes and environment

| Tool | What and why | Install | Check | Undo | Priority | Time |
|---|---|---|---|---|---|---|
| ⚠️ Python 3.12 (3.10+ is OK) | The language for the whole backend. One language means fewer moving parts | Already installed? Run the check first. If not: download from python.org (Windows: tick "Add to PATH") | `python --version` | Uninstall from the OS | Must | 0–10 min |
| venv (built into Python) | A private package folder for this project, so installs don't touch the rest of your computer. Python includes it, so no extra tool like `uv` is needed | `python -m venv .venv`, then activate (see `AGENTS.md`) | `python -c "import sys; print(sys.prefix)"` shows a path ending in `.venv` | Delete the `.venv/` folder | Must | 2 min |
| pip (built in) | Installs Python packages into the venv | Comes with Python | `python -m pip --version` | n/a | Must | 0 |

Node.js is **not needed**: the frontend is plain HTML and JS. Install it only if you choose the optional Context7 MCP server below.

## Version control

| Tool | What and why | Install | Check | Undo | Priority | Time |
|---|---|---|---|---|---|---|
| ⚠️ git | Saves snapshots ("commits") so you can undo a bad change in seconds | git-scm.com, if missing | `git --version` | n/a | Must | 0–10 min |
| `.gitignore` | Tells git never to save `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` | Codex writes it | `git status` doesn't list `.venv` | Edit the file | Must | 1 min |
| Habits | Commit after every passing check. Only the builder commits to `main`. For a risky experiment: `git switch -c try-<name>`; if it fails, `git switch main` | n/a | `git log --oneline` shows small commits | `git restore .` drops uncommitted changes | Must | 0 |

## Backend, testing, quality

| Tool | What and why | Install (inside venv) | Check | Undo | Priority | Time |
|---|---|---|---|---|---|---|
| FastAPI | Builds the JSON API and serves the HTML pages from one process | `python -m pip install fastapi` | `python -c "import fastapi; print(fastapi.__version__)"` | `pip uninstall fastapi` | Must | 1 min |
| Uvicorn | Runs the FastAPI app as a local web server | `python -m pip install uvicorn` | `python -m uvicorn --version` | `pip uninstall uvicorn` | Must | 1 min |
| Pydantic | Checks that request and response JSON has the right fields. Comes with FastAPI | (installed with FastAPI) | `python -c "import pydantic; print(pydantic.VERSION)"` | n/a | Must | 0 |
| httpx | Needed by FastAPI's `TestClient`, which lets tests call the API without starting a server (Assumed dependency; Codex confirms) | `python -m pip install httpx` | `python -c "import httpx"` | `pip uninstall httpx` | Must | 1 min |
| pytest | Runs the automated tests | `python -m pip install pytest` | `python -m pytest --version` | `pip uninstall pytest` | Must | 1 min |
| ruff | Formats code and catches common mistakes in one fast tool | `python -m pip install ruff` | `python -m ruff --version` | `pip uninstall ruff` | Nice | 1 min |
| pre-commit hooks | Run checks automatically before each commit | — | — | — | **Skip**: one more thing that can block a commit at the deadline. Run `ruff` and `pytest` by hand instead | 0 |

## Browser automation (the Decoy Twin)

| Tool | What and why | Install | Check | Undo | Priority | Time |
|---|---|---|---|---|---|---|
| Playwright for Python | Controls a real browser from code. Each run gets a fresh, isolated browser context (Verified). Note: a context is a clean profile, **not** a security sandbox, which is why the allowlist rule exists | `python -m pip install playwright` | `python -m playwright --version` | `pip uninstall playwright` | Must | 1 min |
| ⚠️ Chromium for Playwright | The browser Playwright drives. A large download (Assumed: roughly 150+ MB) into a cache folder **outside the repo** | `python -m playwright install chromium` (Chromium only, not all browsers) | Setup's smoke test opens `http://localhost:8000/mock/lumora/index.html` headless and prints the page title | `python -m playwright uninstall` | Must | 3–10 min |
| OS support | Playwright needs Windows 11+, macOS 14+, or Ubuntu 22.04/24.04 (Verified). On an older OS, use replay mode only | n/a | n/a | n/a | Info | 0 |

## Frontend
Nothing to install. Plain `static/*.html`, `*.css` and `*.js`, opened through the FastAPI server. **Skip** React, Vite, Tailwind and npm.

## Helpers for Codex itself

| Tool | What and why | Install | Check | Undo | Priority | Time |
|---|---|---|---|---|---|---|
| `AGENTS.md` at the repo root | Codex automatically reads it from the project root down to the current folder (Verified). It holds our rules | Copy it from this kit | Ask Codex: "What are the safety rules in AGENTS.md?" | Delete or edit | Must | 1 min |
| ⚠️ Context7 MCP server | Gives Codex current library docs (FastAPI, Playwright) instead of guessing from memory. Needs Node.js (`npx`) | `codex mcp add context7 -- npx -y @upstash/context7-mcp` (Verified from Codex docs) | `codex mcp list` shows `context7` | Set `enabled = false` under `[mcp_servers.context7]` in `~/.codex/config.toml` | Nice | 5–15 min (more if Node is missing) |
| ⚠️ Playwright MCP server | Lets Codex (and the `demo_tester` subagent) drive a browser itself to look at pages. Needs Node.js | `codex mcp add playwright -- npx @playwright/mcp@latest` (Unverified: command from third-party guides; the Codex docs link the package) | `codex mcp list` shows `playwright` | Set `enabled = false` under `[mcp_servers.playwright]` | Nice: `demo_tester` falls back to the Python Playwright library | 5 min |
| Sandbox flags | Codex edits inside the repo freely and asks before going outside it, such as network access or global installs | Start with `codex --sandbox workspace-write --ask-for-approval on-request` (Verified) | Codex asks before `pip install` reaches the internet or before writing outside the repo | Restart without flags | Must | 0 |
| Codex skills (`.agents/skills/<name>/SKILL.md`) | 7 project skills giving Codex specialist instructions per area (stage runner, starter inspector, mock sites, decoy, verdict copy, eval, demo check). Codex loads only the name and description until a task matches (Verified) | The bootstrap copies `teammate-build-kit/codex-skills/*` → `.agents/skills/` | Type `/skills` in Codex: 7 T-Defense skills listed | Delete the folder | Must | 1 min |
| Codex subagents (`.codex/agents/*.toml`) | `safety_reviewer` (checks each diff against the safety rules) and `demo_tester` (runs tests and clicks through the app). They inherit the sandbox; they can't do more than the main Codex (Verified) | The bootstrap writes both from `CODEX_ADE_SETUP.md` | Ask Codex "Which custom agents can you spawn?" | Delete the files | Must | 1 min |
| `PROGRESS.md` | Stage scoreboard that lets a new Codex session resume where the last one stopped | The bootstrap creates it | Each finished stage shows DONE | n/a | Must | 0 |
| Built-in `$skill-creator` | Codex's bundled helper for writing new skills (Verified) | Already built in | `$skill-creator` | n/a | Nice: only if Codex keeps making the same mistake, ask it to capture the fix as a new skill | 5 min |

## Hello-world chain (end of setup)
Setup is done only when all four are true:
1. `GET http://localhost:8000/api/health` returns `{"status": "ok"}`.
2. `python -m pytest -q` shows at least 1 passing test.
3. A headless Chromium opens a local page (`/mock/lumora/index.html`) and prints its title.
4. `http://localhost:8000/` shows a page that fetches `/api/health` and displays "Backend OK".

Then Codex writes `SETUP_REPORT.md`: OS, Python version, every installed package and its version, which of the four checks passed, anything that failed, and what you approved.
