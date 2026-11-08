# CODEX_BUILD_PROMPTS

**Normal use: Codex reads these itself.** In autopilot (see `CODEX_ADE_SETUP.md` Step 5), the `t-defense-stage-runner` skill treats each block below as a stage spec. When a block says "Stop", that means finish the stage (tests, review, commit, `PROGRESS.md`) and continue, unless a stop condition from that skill applies. The GATE is always a real stop.

**Manual fallback:** if autopilot misbehaves, paste these one at a time, in order. Each one ends with a **stop-and-check**. Don't paste the next stage until the check passes and you've committed.

If Codex gets stuck in a loop on one bug for more than about 20 minutes, say: "Stop. Explain the problem in plain words and give me the simplest workaround, even if it's less elegant." Remember: a working demo beats a clever one.

---

## Stage 0: Inspect the starter files (about 5% of time)

**Why:** nobody has looked at T-Mobile's files yet, and the plan is built on guesses about them. This stage swaps the guesses for facts before we write code that depends on them.

```text
Stage 0. Read AGENTS.md. Inspect everything in starter/ WITHOUT modifying it.
1. List every file with its size and type.
2. For the message set: format, number of rows, column names, label values and counts, whether messages contain URLs (count how many), and 5 example rows.
3. For the taxonomy: list every category and its description.
4. For the baseline classifier: language, how to run it, its inputs and outputs (label only, or a score/probability too?), and any dependencies. Install its dependencies into .venv only if they're small; ask me first if any are large.
5. Run the baseline as provided on the full message set and record accuracy, precision, recall and F1 per class, plus a confusion matrix. If it can't run, explain why and stop.
6. Write STARTER_FILES_REPORT.md with all of the above, labeling each fact "observed" or "guessed".
7. Compare with teammate-build-kit/CONTRACTS.md and teammate-build-kit/BUILD_OVERVIEW.md section 10 (Risks). List every assumption that turned out wrong and propose the smallest change to CONTRACTS.md. Apply the CONTRACTS.md changes and mark them "finalized after Stage 0".
8. Commit: "stage 0: starter files inspected".
Stop. Tell me in plain words what surprised you and whether any plan change is needed.
```

**Stop and check:**
- [ ] `STARTER_FILES_REPORT.md` exists, and the baseline numbers are in it.
- [ ] Send the planner the "assumptions that were wrong" list. **If the classifier can't run at all, tell the planner before going on.**

---

## Stage 1: Thin slice, phone plus triage badges (about 15%)

**Why:** the smallest version that works end to end proves the pieces connect.

```text
Stage 1. Read AGENTS.md, teammate-build-kit/CONTRACTS.md and STARTER_FILES_REPORT.md.
1. app/scenarios.py: load messages for the phone from data/scenarios.json (format in CONTRACTS.md). Seed it with 8 messages picked from the starter set (mixed labels), plus 3 written to link to fictional http://localhost:8000/mock/lumora/... pages. Mark each one with "source": "starter" or "team".
2. app/triage.py: a function triage(text) -> {label, category, score, abstained, reasons}. It wraps the baseline unchanged, adds the taxonomy category, and adds at most 5 simple readable rules (for example urgency words, a link plus a request for codes or payment). Abstain when the score is in a gray band (start with 0.40–0.60 if the baseline gives a score; otherwise abstain when the baseline and the rules disagree). Put the thresholds at the top of the file as constants.
3. Endpoints GET /api/scenarios and POST /api/assess exactly as in CONTRACTS.md. Keep the store in app/store.py as plain dicts.
4. static/phone.html, phone.css, phone.js: a phone-shaped frame (about 380px wide) with a message list. Each message shows a colored badge: red "Likely scam", amber "Suspicious", grey "Not sure", green "No warning signs". Keep it clean and large-text.
5. tests/test_triage.py: one obvious scam, one obvious legitimate message, and one gray-zone message that abstains.
6. Run pytest and ruff, start the server, and tell me what to look at.
7. Commit: "stage 1: phone + triage".
Stop.
```

**Stop and check:**
- [ ] `http://localhost:8000/` shows the phone with badges.
- [ ] `python -m pytest -q` passes.

---

## Stage 2: Check page, verdicts, mock sites, replay (about 15%) → then the GATE

**Why:** this is the core user experience. With replay data it works before the risky browser part exists.

```text
Stage 2. Read AGENTS.md, teammate-build-kit/CONTRACTS.md and teammate-build-kit/MOCK_SITES_SPEC.md.
1. Build the five Lumora Wireless demo pages in mock_sites/lumora/ exactly as MOCK_SITES_SPEC.md describes, each with the DEMO banner. No real brand names or logos.
2. Link rewriting: when a message is assessed, each URL gets a random link_id (secrets.token_urlsafe). Store url, sha256(url), message_id. The phone shows the link text, but tapping it goes to /check/{link_id}. The raw URL never appears in the address bar.
3. app/verdict.py: combine(triage, investigation) -> verdict card fields from CONTRACTS.md. Verdicts: likely_scam, suspicious, looks_fine, inconclusive. Rules: an investigation that's missing, failed, timed out or blocked → inconclusive (unless triage alone is a strong likely_scam, in which case keep likely_scam and list "page could not be checked" under unknowns). Never output looks_fine without a completed investigation with zero findings. Give at most 3 evidence lines, at most 3 next steps, and always list unknowns.
4. data/demo_replay.json: hand-written decoy results for each of the 5 mock pages, in the investigation format from CONTRACTS.md, with "mode": "replay".
5. Endpoints: POST /api/links/{link_id}/investigate and GET /api/links/{link_id}/verdict. For now the investigation ALWAYS reads demo_replay.json (Stage 3 adds live mode).
6. static/check.html + check.js: the check page. Big verdict word and color, a one-line confidence ("We're fairly sure because..."), evidence, "What we couldn't check", next steps, and buttons: "Go back (recommended)", "Open anyway" (only for looks_fine and suspicious), and "I already entered my info" (placeholder for now). On load, call POST /api/links/{link_id}/investigate (this covers links whose triage badge was no_signs, like demo scenario B), then GET the verdict. If the status is pending, show "Our decoy is checking this link..." and poll every second for up to 15 seconds, then show inconclusive.
7. tests/test_verdict.py: all four verdicts, plus "failed investigation never becomes looks_fine".
8. tests/test_safety.py: the raw URL is not in the /check page address; link IDs are random.
9. Run pytest and ruff. Commit: "stage 2: check page + verdicts + mock sites".
Stop and tell me how to walk through the full demo in replay mode.
```

### 🚧 GATE: the halfway point
Run the app in replay mode (commands in `AGENTS.md`) and walk through it: phone → tap a risky link → verdict card → back. Then:
- [ ] It works three times in a row from a fresh server start.
- [ ] `git tag gate-demo` and commit.
- [ ] Take screenshots and a 90-second screen recording into `demo_backup/`. This is your emergency demo.
- [ ] Tell the planner the gate passed.

**If the gate fails:** don't start Stage 3. Fix only what blocks the walkthrough.

---

## Stage 3: Live Decoy Twin (about 20%)

**Why:** this is the creative core. It comes after the gate so a Playwright problem can't sink the whole demo.

```text
Stage 3. Read AGENTS.md (safety rules 2–6 especially) and teammate-build-kit/MOCK_SITES_SPEC.md.
1. app/investigator.py: a plain (non-async) function investigate(url) using Playwright's SYNC API, started from the server with asyncio.to_thread (or FastAPI's run_in_threadpool) so each run gets its own thread and its own Playwright instance. Reason: on Windows, running Playwright's async API inside Uvicorn's event loop (especially with --reload) is a known source of "NotImplementedError" subprocess errors. If you still hit loop errors, run live mode without --reload.
   - FIRST check the allowlist: the URL must start with http://localhost:8000/mock/ or http://127.0.0.1:8000/mock/. Otherwise return status "blocked" without launching a browser.
   - Launch headless Chromium, then a NEW browser context per investigation, closed afterwards.
   - Block every request whose host isn't localhost or 127.0.0.1 (page.route abort).
   - Record: the redirect chain; the final URL; whether the final origin differs from the start; form fields by type (password, card number, SSN, one-time code, gift card, plus input name/label/placeholder); where each form submits; urgency phrases from the list in MOCK_SITES_SPEC.md; download attempts; and text aimed at AI agents (the phrases listed in the spec).
   - Fill forms ONLY with the canary values in MOCK_SITES_SPEC.md, submit once, and record where the canaries were sent and whether a cross-origin request carried them.
   - Total timeout 10 seconds. On any exception return status "failed" with a short error.
   - Return the investigation JSON from CONTRACTS.md with "mode": "live".
2. Run investigations as a background task when an assessment has a risky or abstained link (FastAPI BackgroundTasks or asyncio.create_task). Cache results in store.py. If DEMO_MODE=replay, read data/demo_replay.json instead.
3. On the check page, show the decoy's findings as "What happened when our decoy opened it" with canary lines like: "The page asked our decoy for a card number and sent it to a different site."
4. tests/test_investigator.py: page 1 finds credential and cross-origin submission; page 3 (legit) has zero findings; a non-allowlisted URL (http://example.com/) returns blocked with no browser launched; a page that hangs leads to failed then inconclusive.
5. Compare live results with demo_replay.json and update the replay file to match the live output exactly.
6. Run pytest and ruff. Commit: "stage 3: live decoy twin".
Stop.
```

**Stop and check:**
- [ ] Live mode: the check page shows decoy findings within about 10 seconds.
- [ ] Replay mode still works.
- [ ] The blocked-URL test passes.

---

## Stage 4: Evaluation and recovery (about 15%)

```text
Stage 4. Read teammate-build-kit/EVALUATION_AND_DEMO.md.
1. eval/run_eval.py: run (a) the baseline alone and (b) T-Defense triage on the provided starter message set. If you tuned any threshold or rule, use a fixed random 70/30 split (seed 42), tune on the 70 only, and report on the 30. Report accuracy, precision, recall and F1 for the scam class, a confusion matrix, the abstain rate, and accuracy on non-abstained messages. Then (c) run the decoy (live, or replay if live fails) on the 5 mock pages and report a SEPARATE table with the expected vs observed verdict. Write everything to eval/results.md with the date and mode.
2. Recovery: "I already entered my info" opens a checklist chosen by the scam category (text in MOCK_SITES_SPEC.md, section Recovery). It must include: contact the company using the number on your card or bill, not the message; change the password you used; turn on account PINs or 2-step verification; report the text by forwarding it to 7726 (SPAM). Plain steps only, no links out.
3. Test: run_eval runs on a tiny sample without crashing.
4. Commit: "stage 4: eval + recovery".
Stop and show me eval/results.md.
```

**Stop and check:**
- [ ] `eval/results.md` has a baseline row, a T-Defense row, the abstain rate, and a separate mock-page table.
- [ ] Send the results file to the planner for the slides.

---

## Stage 5: Feature freeze and demo polish (about 20%)

**Why:** most hackathon demos fail from last-minute changes. From here on, only polish and fixes.

```text
Stage 5. FEATURE FREEZE: no new features. Only:
1. Fix any bug found while walking through teammate-build-kit/EVALUATION_AND_DEMO.md scenarios A–E.
2. Make every text readable from 2 meters: large fonts, high contrast, no overflow at 380px wide.
3. Add a "Demo reset" button (or GET /api/reset) that clears the store.
4. Write README.md: what T-Defense is, how to run it (live and replay), the safety rules, honest limits, and credits to T-Mobile starter files.
5. Re-record demo_backup/ screenshots and the screen recording.
6. Run pytest and ruff, commit "stage 5: demo ready", and tag demo-final.
Stop.
```

**Final check (you plus the planner):** rehearse the 3-minute script twice with a timer, once in live mode and once in replay. Submit on Devpost **before 12:00 pm Sunday**.
