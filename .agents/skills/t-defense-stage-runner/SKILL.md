---
name: t-defense-stage-runner
description: Use whenever building, continuing or resuming the T-Defense project, or when asked to "run the next stage", "continue", or "autopilot". Runs one build stage from teammate-build-kit/CODEX_BUILD_PROMPTS.md end to end, verifies it, gets it reviewed, commits, and logs progress.
---

# Running a T-Defense build stage

Use this loop for every stage (Setup, 0, 1, 2, GATE, 3, 4, 5).

## Before starting
1. Read `AGENTS.md`, `PROGRESS.md` (create it if missing) and `git log --oneline -10`. Find the first stage not marked DONE in `PROGRESS.md`.
2. Read that stage's prompt block in `teammate-build-kit/CODEX_BUILD_PROMPTS.md`. It is the spec. Treat its numbered steps as your task list.
3. Load any matching skill for the stage:
   - Stage 0: `$starter-inspector`
   - Stage 2: `$mock-site-builder` and `$verdict-card-writer`
   - Stage 3: `$decoy-investigator`
   - Stage 4: `$eval-reporter`
   - GATE and Stage 5: `$demo-readiness-check`

## While working
- Make small changes. Run `python -m pytest -q` after each meaningful step, not only at the end.
- If a test fails, fix it. If the same failure survives 3 attempts, write down the problem and try the simplest workaround that keeps the demo working. Cut a stretch feature before you break a must-have.
- Keep the API shapes in `teammate-build-kit/CONTRACTS.md`. If one must change, edit that file in the same commit and note it in `PROGRESS.md`.

## Finishing a stage
1. Run `python -m pytest -q` and `python -m ruff check . --fix` and `python -m ruff format .`. Both must be clean.
2. Ask the `safety_reviewer` subagent to review `git diff` against the AGENTS.md safety rules. Fix anything it flags as BLOCKER.
3. Ask the `demo_tester` subagent to start the app and walk through what this stage added (it uses replay mode from Stage 2 on). Fix anything it reports as broken.
4. Commit with the message `stage N: <short summary>`.
5. Append to `PROGRESS.md`:
   ```
   ## Stage N — DONE (time)
   - Built: ...
   - Checks: pytest X passed, ruff clean, reviewer OK, tester OK
   - Cut or changed: ...
   - Human should look at: ...
   ```

## When to stop and ask the human (do not continue past these)
- Any global install, large download, or network access outside the repo (for example `python -m playwright install chromium`, installing Node).
- Stage 0 finds that the starter classifier can't run, or that the data is very different from the plan.
- The GATE: always stop after the GATE walkthrough so the human can watch it work once.
- Anything that would break an AGENTS.md safety rule.
- More than about 45 minutes stuck on one problem.

Otherwise, continue straight to the next stage without waiting.
