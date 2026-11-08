# CODEX_ADE_SETUP: turn Codex into a T-Defense build team, then let it build

**What this is.** An **ADE** (agentic development environment) is Codex plus everything that makes it work well on *this* project without hand-holding:

| Piece | What it does | Where it lives |
|---|---|---|
| Project rules | Goal, stack, safety rules, definition of done. Codex reads them automatically at the start of each session (Verified) | `AGENTS.md` (repo root) |
| 7 specialized skills | Step-by-step expertise Codex loads when a task matches (Verified format and location) | `.agents/skills/<name>/SKILL.md` |
| 2 helper subagents | A safety reviewer and a demo tester that check Codex's own work before each commit (Verified format) | `.codex/agents/*.toml` |
| Sandbox settings | Codex edits freely inside the project and **asks you** before going outside it (Verified flags) | Command-line flags |
| Optional MCP servers | Current library docs (Context7) and a browser Codex can drive (Playwright MCP) | `~/.codex/config.toml`, via `codex mcp add` |
| Progress log | Lets Codex resume after a crash or a new session | `PROGRESS.md` |

**Your total effort:** about 10 minutes of setup, two pastes, then approving prompts and watching. Codex builds everything, using `BUILD_OVERVIEW.md` as the plan and `CODEX_BUILD_PROMPTS.md` as the stage specs.

---

## Step 1: Prepare the folder (you, 3 minutes)

1. Make an empty folder named `T-Defense`.
2. Copy the whole `teammate-build-kit/` folder into it, so you have `T-Defense/teammate-build-kit/`.
3. Put T-Mobile's starter files, unchanged, in `T-Defense/starter/`.
4. Open a terminal in `T-Defense/` (on Windows, use PowerShell; Codex uses its native Windows sandbox there, Verified).

## Step 2: Start Codex in "autonomous but fenced" mode (you, 1 minute)

```bash
codex --sandbox workspace-write --ask-for-approval on-request
```
**Why these flags (Verified in Codex docs):** `workspace-write` lets Codex edit files and run normal commands inside `T-Defense/` without asking each time. `on-request` makes it stop and ask before anything outside that boundary, such as internet downloads (`pip install`, the Chromium download) or global installs. That's the right balance: Codex works on its own, but you're the gate for anything risky.

Don't use `danger-full-access` or `--ask-for-approval never`. Those remove the fence entirely.

If you use the Codex IDE extension or app instead of the CLI, pick the equivalent setting: Codex may edit the workspace and asks before going further. (Exact menu names are Unverified.)

## Step 3: Paste the ADE bootstrap prompt (Codex, about 15–30 minutes)

Paste everything inside this block:

```text
You are bootstrapping an agentic development environment (ADE) for the T-Defense hackathon project, then setting up the dev environment. Do NOT build product features yet.

Read first, in this order: teammate-build-kit/README.md, teammate-build-kit/BUILD_OVERVIEW.md, teammate-build-kit/AGENTS.md, teammate-build-kit/TOOLING_AND_SKILLS.md, and this file (teammate-build-kit/CODEX_ADE_SETUP.md).

I am a beginner. Before any global install, large download or network access, explain it in 1–2 plain sentences and wait for my approval.

PART A: ADE
1. If this isn't a git repo, run `git init`.
2. Copy teammate-build-kit/AGENTS.md to ./AGENTS.md.
3. Copy every folder in teammate-build-kit/codex-skills/ to ./.agents/skills/ (keep each <name>/SKILL.md). You should end up with 7 skills: t-defense-stage-runner, starter-inspector, mock-site-builder, decoy-investigator, verdict-card-writer, eval-reporter, demo-readiness-check.
4. Create the two subagent files in ./.codex/agents/ exactly as given in section "Subagent definitions" of teammate-build-kit/CODEX_ADE_SETUP.md.
5. Create PROGRESS.md containing a "# T-Defense progress" heading and the stage list: Setup, 0, 1, 2, GATE, 3, 4, 5, all marked TODO.
6. Optional MCP servers: check whether Node.js is installed (`node --version`). If it is, ask me whether to add them, then run:
     codex mcp add context7 -- npx -y @upstash/context7-mcp
     codex mcp add playwright -- npx @playwright/mcp@latest
   and verify with `codex mcp list`. If Node is missing, skip both, note it in PROGRESS.md, and do NOT install Node unless I say so.

PART B: Environment (follow teammate-build-kit/CODEX_SETUP_PROMPT.md steps 3–10 exactly)
This covers .gitignore, .env.example, the .venv, packages, the Chromium download (ask first), the folder layout, the hello-world chain (health endpoint, phone page, Lumora index page, 2 tests), requirements.txt pinning, and SETUP_REPORT.md.

PART C: Finish
1. Run `python -m pytest -q` and `python -m ruff check .`.
2. Mark "Setup" DONE in PROGRESS.md, with versions and anything skipped.
3. Commit: "setup: ADE + environment + hello world".
4. Tell me: what works, what failed, and that I must RESTART Codex now so it loads AGENTS.md and the new skills and agents. Then stop.
```

## Step 4: Restart and verify the ADE (you, 2 minutes)

Quit Codex and start it again with the same command as Step 2. Then check:

| Check | How | Expect |
|---|---|---|
| Rules loaded | Ask: "Summarize the safety rules you are following." | It lists the AGENTS.md rules (allowlist, synthetic data, fail to inconclusive...) |
| Skills loaded | Type `/skills` | 7 T-Defense skills listed |
| Subagents known | Ask: "Which custom agents can you spawn?" | `safety_reviewer`, `demo_tester` |
| MCP (if added) | Run `codex mcp list` in a terminal | `context7`, `playwright` |
| App works | Open `http://localhost:8000/` after asking Codex to start the server | "Backend OK" |

If a skill is missing, ask: "Check .agents/skills/ — each skill needs a SKILL.md with name and description frontmatter." Then restart again.

## Step 5: Paste the autopilot prompt (Codex builds the product)

```text
Use $t-defense-stage-runner to build T-Defense autonomously, stage by stage, from PROGRESS.md: Stage 0, 1, 2, GATE, 3, 4, 5.
The plan is teammate-build-kit/BUILD_OVERVIEW.md. Stage specs are in teammate-build-kit/CODEX_BUILD_PROMPTS.md. Contracts are in teammate-build-kit/CONTRACTS.md. Mock pages are in teammate-build-kit/MOCK_SITES_SPEC.md. The demo and evaluation are in teammate-build-kit/EVALUATION_AND_DEMO.md.
For each stage: load the matching skill, do every numbered step, keep tests green, have safety_reviewer review the diff and demo_tester exercise the result, fix what they flag, commit, and update PROGRESS.md. Then continue to the next stage without waiting for me.
Stop and ask me only for: global installs, large downloads or network access; Stage 0 surprises that change the plan; the GATE (I want to watch it once); anything that would break an AGENTS.md safety rule; or being stuck for more than 45 minutes.
Simplicity rule: if something is fragile, choose the simpler version and log what we lost in PROGRESS.md. Follow the cut list in BUILD_OVERVIEW.md section 3 if time is short. Today's hard deadline is Sunday Nov 8, 12:00 pm Central. Feature freeze starts at Stage 5.
After each stage, give me a 3-line summary: what was built, how I can see it, and anything I need to do.
```

## Step 6: What you do while Codex works

- **Approve or deny prompts.** Approve `pip install`, the Chromium download, and `git` commands. Deny anything that touches files outside `T-Defense/`, installs system software you didn't expect, or visits a website other than package sites (pypi.org, npm).
- **Watch `PROGRESS.md`.** It's the scoreboard. Each stage should appear as DONE with checks.
- **At Stage 0:** send `STARTER_FILES_REPORT.md` to the planner.
- **At the GATE:** watch one replay-mode run yourself. Screen-record 90 seconds into `demo_backup/`. Say "continue".
- **At Stage 4:** send `eval/results.md` to the planner for slides.
- **When the planner sends content** (extra scenarios, page copy, recovery text): drop the files in, and tell Codex: "New content from the planner is in <file>. Merge it following the contracts and re-run tests."
- **If Codex loses track** (new session, crash, context gets long): restart it and paste: `Use $t-defense-stage-runner to resume from PROGRESS.md.`
- **If Codex loops on one bug:** "Stop. Explain the problem in plain words and give me the simplest workaround, even if it's less elegant."
- **If the deadline is close:** "Apply the cut list in BUILD_OVERVIEW.md section 3 until the remaining time fits Stage 5."

---

## Subagent definitions

Codex creates these two files in Step 3. Subagents are separate helper agents, defined in TOML files with `name`, `description` and `developer_instructions` (Verified). They inherit your sandbox and approval settings, so they can't do more than the main Codex can (Verified). Both mostly read and check. We deliberately have **no** parallel code-writing agents, because two writers editing the same files cause conflicts (Verified warning in the docs).

`.codex/agents/safety_reviewer.toml`
```toml
name = "safety_reviewer"
description = "Read-only reviewer. Use before every T-Defense commit to check the diff against AGENTS.md safety rules and CONTRACTS.md."
developer_instructions = """
You review, you never edit files. Read AGENTS.md, teammate-build-kit/CONTRACTS.md and teammate-build-kit/MOCK_SITES_SPEC.md, then run `git diff` (and `git diff --staged`).
Report BLOCKER for any of: investigator can reach a URL outside http://localhost:8000/mock/ or http://127.0.0.1:8000/mock/; any external network request from mock pages or the decoy; non-canary data typed by the decoy; real brand names, logos or real people; real customer data; a failure path that can produce looks_fine; secrets in code or committed .env; edits inside starter/; page text influencing program behavior.
Report WARN for: API shape drift from CONTRACTS.md without updating it; the word "safe" or "guaranteed" in user-facing text; missing tests for a new behavior; new dependencies not in AGENTS.md's stack.
Answer with a short list: BLOCKER / WARN / OK lines, each with file and line. If none, answer "OK: no issues".
"""
```

`.codex/agents/demo_tester.toml`
```toml
name = "demo_tester"
description = "Tester. Use after each T-Defense stage to run the test suite and exercise the running app like a judge would."
developer_instructions = """
Do not change application code. You may create or update files under tests/ and demo_backup/ only.
1. Run `python -m pytest -q` and report failures.
2. Start the app on port 8000 (replay mode from Stage 2 on, see AGENTS.md), then exercise what this stage added using Playwright (the Python library, or the Playwright MCP server if available): load http://localhost:8000/, tap links, read the check page.
3. Compare what you see with teammate-build-kit/EVALUATION_AND_DEMO.md scenarios A–D for stages that include them.
4. Check readability at 380px width and that no page requests an external host.
5. Stop the server. Report: PASS or FAIL per item, exact steps to reproduce each failure, and screenshots saved in demo_backup/.
"""
```
