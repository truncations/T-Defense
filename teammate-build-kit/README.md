# Teammate Build Kit: T-Defense (hackUTD 2026, T-Mobile Safe Signal)

This kit sets up **Codex to build the whole project on its own**. You (the builder) prepare a folder, paste two prompts, approve Codex's install requests, and watch one checkpoint. Codex does the rest, following the plan and specs in this folder. You don't need access to the planner's machine.

## Start here: 3 steps
1. Read `BUILD_OVERVIEW.md` sections 1–3 (5 minutes) so you know what's being built.
2. Follow `CODEX_ADE_SETUP.md` from top to bottom. It has the folder setup, the command to start Codex, **paste 1** (ADE bootstrap + environment), a restart and check, and **paste 2** (autopilot build).
3. While Codex works, use `CODEX_ADE_SETUP.md` Step 6 ("What you do while Codex works").

## What is in here

| File | What it is | Who reads it |
|---|---|---|
| `README.md` | This page | You |
| `CODEX_ADE_SETUP.md` | **The main guide.** Sets up Codex's environment (rules, 7 skills, 2 subagents, sandbox, optional MCP) and holds both paste-in prompts | You, then Codex |
| `codex-skills/` | 7 skills Codex copies into `.agents/skills/` | Codex |
| `BUILD_OVERVIEW.md` | The plan: pitch, architecture, scope, cut list, schedule, risks, glossary | You, planner, Codex |
| `AGENTS.md` | Project rules. Codex copies it to the repo root | Codex |
| `CODEX_SETUP_PROMPT.md` | Environment and hello-world steps (run as part of paste 1) | Codex |
| `CODEX_BUILD_PROMPTS.md` | Stage specs 0–5 that Codex follows (you can also paste them by hand as a fallback) | Codex |
| `TOOLING_AND_SKILLS.md` | Every tool: why, install, check, undo | You, Codex |
| `CONTRACTS.md` | Draft API and JSON shapes (finalized in Stage 0) | Codex |
| `MOCK_SITES_SPEC.md` | Fictional "Lumora Wireless" demo pages, canary data, recovery text | Codex |
| `EVALUATION_AND_DEMO.md` | Numbers to report, 3-minute demo script, fallbacks | You, planner, Codex |
| `AUDIT_NOTES.md` | Every claim checked, with status and source | Planner |

Hard deadline (Verified from the event page): Devpost submissions are due **Sunday Nov 8, 12:00 pm Central**. Make a draft entry by **Saturday 11:00 pm**.
