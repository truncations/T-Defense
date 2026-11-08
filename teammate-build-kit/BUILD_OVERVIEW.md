# BUILD_OVERVIEW: T-Defense

Labels used here: **Verified** means checked against an official source (see `AUDIT_NOTES.md`). **Team-stated** means the team told us. **Assumed** means our best guess, to be confirmed. **Unverified** means we tried and could not confirm.

---

## 1. Pitch and the one memorable idea

**Pitch.** Scam texts work because people tap first and think later. T-Defense is protection built into the messaging app, so there's nothing to install and nothing to turn on. Every incoming message is quietly scored using T-Mobile's baseline classifier and scam taxonomy. When a link looks risky, a **Decoy Twin** opens it before you do. The Decoy Twin is a throwaway fake customer with a made-up identity, running inside a sealed browser. When you tap, you see a plain-language card: what the page tried to take from the decoy, how sure we are, and exactly what to do next. If you already typed your details in, T-Defense walks you through recovery.

**The one memorable idea:** *"Something already fell for it, so you don't have to."* The Decoy Twin shows what a scam page **does**, not only what a message **says**.

Honest framing for the pitch (hard rules; see `AUDIT_NOTES.md` claims C10 and C11 for status):
- We show a **mock messaging app**. We do **not** claim a carrier can read encrypted chats (for example end-to-end encrypted RCS or iMessage). T-Defense would run inside a messaging app the customer opts into, or on plain SMS links where that is lawful and disclosed.
- The decoy visits **only our own demo pages**. Real scam pages can behave differently for automated browsers, so a clean decoy result reads "no warning signs found," never "safe."

---

## 2. The decision

### Chosen architecture: one Python app, one plain web page, one decoy browser

```text
  Browser tab: mock phone (static/phone.html, plain HTML + JS)
        |  fetch() JSON
        v
  FastAPI app  (app/main.py, one process, port 8000)
   |-- /api/scenarios ........ loads data/scenarios.json (synthetic messages)
   |-- /api/assess ........... app/triage.py  -> wraps starter/ baseline classifier
   |                                          + taxonomy category + simple rules
   |-- /api/links/{id}/... ... app/verdict.py -> combines triage + decoy evidence
   |        |
   |        v
   |   app/investigator.py  "Decoy Twin"
   |     Playwright, headless Chromium, fresh browser context,
   |     ALLOWLIST: only http://localhost:8000/mock/ and http://127.0.0.1:8000/mock/
   |     fills forms with fake canary values, records observations, 10 s timeout
   |        |
   |        +-- fallback: data/demo_replay.json (recorded decoy results)
   |
   |-- /mock/lumora/... ...... mock_sites/ (fictional brand, labeled DEMO)
   |-- /check/{link_id} ...... the "check page" (interstitial) shown when a link is tapped
   `-- in-memory store ....... app/store.py (dicts; cleared on restart)
```

Terms: a **headless browser** is a real browser running with no window, controlled by code. A **browser context** is a fresh, incognito-like profile with its own cookies and storage. An **interstitial** is a page shown between tapping a link and reaching it. An **allowlist** is a list of the only places a program may go.

**How a message flows through it:**
1. The phone loads the synthetic messages. For each one it calls `/api/assess`.
2. Triage returns a risk level, a scam category, and whether it **abstains** (says "not sure").
3. For risky or not-sure messages with a link, the server starts the Decoy Twin right away and caches the result. This is the "the decoy opens it first" idea.
4. Each link in the message is rewritten to `/check/{link_id}`. The link ID is a random token, so the real URL never goes in the address bar.
5. When you tap, the check page shows the verdict card. If the decoy hasn't finished, the card says so and waits. If the decoy fails, the verdict is **Inconclusive**, never "Looks fine."

### Alternatives that lost

| Alternative | Why it lost (plain words) |
| --- | --- |
| **Browser extension that watches pages** (the team's first idea) | The judge called extensions friction (Team-stated). It also needs one adapter per website, breaks when sites change, and must ask for broad permission to read your pages. **Kept as a stretch slide, not code.** |
| **React + TypeScript + Vite frontend and SQLite** (the second handoff's stack) | That's four extra tools and a second running server for beginners on a roughly 24-hour clock. **What we lose:** reusable components and type checking. A single phone screen doesn't need them. |
| **LLM agent that freely browses** | Unsafe, slow, and needs network access and credits. It can also be manipulated by page text (prompt injection). The decoy follows a fixed, coded script instead. |
| **Carrier-network proxy or DNS filtering** | It can't see encrypted traffic or page behavior, and we can't demo it honestly in 24 hours. |
| **Lovable-generated UI** | It produces a React project and a separate repo, so wiring it to our backend costs time, and credits run out mid-edit. Use it only for a look-and-feel mock if spare time appears (see section 11). |

---

## 3. Scope

### Must-have demo (all of these, or no demo)
| # | Item | Stage | Owner | Check |
|---|---|---|---|---|
| M1 | Mock phone shows synthetic messages, each with a risk badge | 1 | Builder | Open `http://localhost:8000/` and see badges |
| M2 | Triage wraps the provided baseline and returns label, category, score, abstain | 1 | Builder | `python -m pytest tests/test_triage.py` passes |
| M3 | Links rewritten to a check page that shows a verdict card with evidence and next steps | 2 | Builder | Tap a link in the phone and see the card |
| M4 | Four verdicts work: Likely scam, Suspicious, Looks fine, Inconclusive | 2 | Builder | `tests/test_verdict.py` covers all four |
| M5 | Five Lumora Wireless demo pages exist (see `MOCK_SITES_SPEC.md`) | 2 | Builder; copy by planner | Each opens at `/mock/lumora/...` with a DEMO banner |
| M6 | Decoy Twin runs live on the demo pages, with replay fallback | 3 | Builder | `tests/test_investigator.py` passes; `DEMO_MODE=replay` also works |
| M7 | Recovery checklist ("I already entered my info") | 4 | Builder; text by planner | Button on the card opens the checklist |
| M8 | Evaluation numbers: baseline vs T-Defense on provided data, abstain rate, and a separate table for mock pages | 4 | Builder | `python -m eval.run_eval` writes `eval/results.md` |

### Stretch goals (only after the halfway gate passes)
- S1: "Report this" button that saves the link hash and category.
- S2: A one-line tip about the scam tactic, from the taxonomy.
- S3: Optional LLM that rewrites the explanation in friendlier words (`USE_LLM=false` by default; the template text is the fallback).
- S4: Public demo URL (only if the event requires remote judging).
- S5: Prompt-injection tripwire: the decoy flags pages containing text aimed at AI agents (see `MOCK_SITES_SPEC.md`, page 5).

### Cut list (drop in this order when time runs short)
1. S4 public URL → demo from the laptop.
2. S3 LLM wording → template text.
3. S1 report button → mention it in the pitch.
4. S2 tactic tips → fold into the evidence lines.
5. Live decoy during the demo → `DEMO_MODE=replay`. Say "recorded earlier today" out loud. **Protect creativity:** keep the Decoy Twin story and its evidence cards even when replayed.
6. Page 5 (injection) and page 4 (redirect) → keep pages 1 to 3.
7. Never cut: honest Inconclusive, synthetic-only data, the evaluation table.

---

## 4. Judging criteria → what we show → proof

Criteria are Verified from the Safe Signal track page. Weights are unknown.

| Criterion | What we show | How we prove it |
|---|---|---|
| Creativity | Decoy Twin: a fake customer falls for it first and reports what was stolen | Live run on a Lumora page during the demo |
| Impact | Catches a scam whose **text looks harmless** because the page behavior gives it away | Demo scenario B (see `EVALUATION_AND_DEMO.md`) |
| Usability | Nothing to install; one tap; three-second card; plain next steps | Demo flow; the card has at most 3 evidence lines and 3 next steps |
| Security and privacy | Allowlist, canary-only data, link tokens instead of URLs, nothing stored after restart, fail to Inconclusive | Slide with the checklist from section 5; `tests/test_safety.py` |
| Detection accuracy | Baseline vs T-Defense on T-Mobile's set, plus the abstain rate | `eval/results.md`, with mock-page results reported separately |

---

## 5. Privacy and safety checklist

- [ ] Only synthetic messages from `starter/` or `data/scenarios.json`. No real customer data, ever.
- [ ] The investigator refuses any URL not on the allowlist (`localhost:8000/mock/` or `127.0.0.1:8000/mock/`). A test proves it.
- [ ] The decoy types only canary values: obviously fake data that's easy to spot (for example name "Decoy Twin", card `4242 4242 4242 4242` with a fake expiry, SSN `000-00-0000`). No real credentials.
- [ ] Every mock page uses the fictional brand "Lumora Wireless" with a visible "DEMO PAGE – NOT A REAL COMPANY" banner. No real brand names, logos or look-alikes, including T-Mobile's.
- [ ] Page text is treated as data, never as instructions. The decoy runs a fixed script, not an AI.
- [ ] The phone sends link IDs, not raw URLs, in addresses. The store keeps a SHA-256 hash of each URL, the verdict and the category. It does not keep the message text beyond the running process.
- [ ] Failure means Inconclusive. A timeout, crash or blocked URL is never "Looks fine."
- [ ] Every verdict card lists what we checked and what we could not check.
- [ ] Keys, if any, live in `.env`. `.env` is in `.gitignore`, and `.env.example` holds only placeholder names.

---

## 6. Build plan

Timeline (Verified): hacking began Sat Nov 7 at 12:00 pm CT. The Devpost draft is due Sat at 11:00 pm, final submission Sun at 12:00 pm, and judging runs Sun 1–4 pm. Plan around about 20 working hours, sleep included. Percentages are shares of the time you have left when you start.

**Who runs it:** Codex, on its own. After the builder's two pastes (`CODEX_ADE_SETUP.md`), the `t-defense-stage-runner` skill takes Codex through every stage below, checks each one with the `safety_reviewer` and `demo_tester` subagents, commits, and logs to `PROGRESS.md`. It stops for the builder only at installs, Stage 0 surprises, and the GATE.

| Stage | Share | What | Spec |
|---|---|---|---|
| Setup | 10% | ADE (rules, skills, subagents) plus environment and a hello-world through the whole chain; `SETUP_REPORT.md` | `CODEX_ADE_SETUP.md` → `CODEX_SETUP_PROMPT.md` |
| 0 Inspect | 5% | Read and run the starter files, write `STARTER_FILES_REPORT.md`, fix `CONTRACTS.md` | Stage 0 |
| 1 Thin slice | 15% | Phone, scenarios, triage badges (M1, M2) | Stage 1 |
| 2 Check page | 15% | Link tokens, verdict card, four verdicts, mock pages, replay file (M3–M5) | Stage 2 |
| **GATE (~45–50%)** | | **A full demo works with `DEMO_MODE=replay`: message → tap → card. Commit and tag `gate-demo`. If it doesn't work, stop new features and fix this.** | |
| 3 Decoy Twin | 20% | Live Playwright investigator (M6) | Stage 3 |
| 4 Evaluate and recover | 15% | Eval script, recovery checklist (M7, M8) | Stage 4 |
| 5 Freeze | 20% | **Feature freeze.** Rehearse, fallbacks, README, Devpost, video if required | Stage 5 |

---

## 7. Evaluation plan (details in `EVALUATION_AND_DEMO.md`)

1. Measure the **provided baseline as-is** first, on the provided data, before changing anything.
2. Measure **T-Defense triage** (baseline + rules + abstain) on the same data. If we tune any rule or threshold, tune on a split we then don't score on.
3. Report **abstain rate** (the share of messages marked "not sure") and accuracy on the messages we didn't abstain on.
4. Report **mock-page decoy results in a separate table**. They are our own pages, so they don't count as accuracy on T-Mobile's data.

---

## 8. Three-minute demo script and fallbacks

The full script is in `EVALUATION_AND_DEMO.md`. Short version: (A) an obvious scam text gets flagged → (B) a harmless-looking text that the Decoy Twin catches → (C) a real-looking legitimate message gets "No warning signs found, here's what we couldn't check" → (D) "I already entered my info" brings up recovery → (E) the accuracy slide.

| Failure | Fallback |
|---|---|
| No Wi-Fi | Everything runs on `localhost`; nothing needs the internet |
| Playwright or browser breaks | Restart with `DEMO_MODE=replay` (recorded decoy results) |
| Whole app breaks | `demo_backup/` screenshots plus a 90-second screen recording made at the gate and again in Stage 5 |
| LLM or API down | Off by default; template text is always there |

---

## 9. Roles

**Builder (you) + Codex:** Codex writes, tests and commits everything in the repo on autopilot. You set up the ADE, approve install requests, watch the GATE run, make the screen recording, and pass files between Codex and the planner (`CODEX_ADE_SETUP.md` Step 6).

**Planner (no code, in parallel):**
- Write 12–20 extra synthetic scenarios for `data/scenarios.json`, in the format given in `CONTRACTS.md`. Include 3 "text looks harmless, page is a scam" cases and 3 legitimate ones.
- Write Lumora Wireless page copy and the recovery checklist text (`MOCK_SITES_SPEC.md`).
- Write the pitch, slides, Devpost text and demo narration. Run the demo timing.
- Find out what the $500 Maritime credit covers (Unverified, see section 11) and confirm the event's AI and submission rules with organizers.
- Send the builder content as files. **The planner does not push code.**

**Git rule for two people:** only the builder commits to the `T-Defense` repo, on `main`. The planner's content arrives as files the builder drops into `data/` or `mock_sites/` and commits. Before risky changes, Codex makes a branch (`git switch -c try-<name>`) and merges only if the tests pass.

---

## 10. Risks and assumptions

| Risk or assumption | Label | What changes the plan |
|---|---|---|
| Starter files are Python, runnable, with labeled messages | Assumed | If the classifier isn't Python, wrap it as a subprocess or reimplement its output format. If there are no labels, the eval reports only agreement and abstain rate |
| Messages contain URLs | Assumed | If not, our scenarios attach fictional `lumora` links; we say so in the eval |
| Baseline outputs a probability or score | Assumed | If it only outputs labels, abstain comes from baseline vs rules disagreeing |
| Playwright runs on the demo laptop | Verified on supported OS (Windows 11+, macOS 14+) | On an older OS: replay mode only |
| Judge meant "no install, runs in background" | Team-stated, partly | If the judge wanted network-level protection, reframe the pitch: T-Defense as a carrier-offered messaging-app feature, same demo |
| Demo is in person, about 2–3 minutes per team | Assumed (2025 used in-person judging) | If there's a video, record the gate demo early |
| Maritime $500 credit has a use for us | Unverified | If it hosts apps, it could serve S4; otherwise we skip it |
| No AI-tool restrictions in rules | Unverified (Devpost rules page blocked our fetch) | If restricted, remove S3; Codex use must be disclosed if asked |

---

## 11. Resource plan

| Resource | Use | Estimated spend | If it runs out or is down |
|---|---|---|---|
| Codex (builder) | All coding | Builder's own plan | Follow the prompts by hand; the stages are small |
| Maritime ($500, both of us) | Maritime is a managed cloud for AI agents (Verified via YC launch page). **Not needed for the core demo.** Possible use: S4 public URL | $0 planned | Skip; the demo is local |
| Lovable (105 credits each) | Optional: the planner sketches the phone look, and the builder copies colors and layout by hand | ≤ 20 credits; Build-mode edits cost about 0.5–2 credits each (Verified) | Skip; Codex styles the plain HTML |
| NVIDIA Brev ($60 shared) | **Skip.** No GPU needed: the baseline classifier and rules run on a laptop CPU (Assumed until Stage 0) | $0 | n/a |
| OpenAI API (S3 only) | Optional explanation wording | Only if a key exists | `USE_LLM=false` |

**Logins:** each person signs in to Maritime and Lovable with their own hackathon account. Nobody shares passwords. If a hosted service is used, its key goes only in the builder's `.env`, sent over a private DM and never committed. Sponsor tools aren't required by the Safe Signal track and aren't listed as affecting its prizes (Verified from the track page). Using one doesn't enter us in that sponsor's track unless we submit there.

---

## 12. Glossary

- **ADE (agentic development environment)**: Codex plus project rules, skills, helper subagents and sandbox settings, so it can build on its own.
- **Skill**: a folder with a `SKILL.md` that gives Codex expert steps for one kind of task.
- **Subagent**: a helper Codex starts for a side job, here reviewing safety or testing the demo.
- **Sandbox**: the fence that limits what Codex can touch without asking you.
- **API**: a set of web addresses a program calls to get or send data, here returning JSON.
- **Abstain**: the system says "not sure" instead of guessing.
- **Allowlist**: the only places a program may visit; everything else is refused.
- **Baseline classifier**: T-Mobile's provided model that labels messages scam or not.
- **Browser context**: a fresh incognito-like browser profile with its own cookies.
- **Canary value**: fake data that's obviously ours, so we can spot where it goes.
- **Codex**: OpenAI's coding agent, which reads `AGENTS.md` for repo rules.
- **Decoy Twin**: our scripted fake customer that opens risky links first.
- **`.env` file**: a local file holding secret keys, never committed to git.
- **FastAPI**: a Python library for building web APIs.
- **Headless browser**: a real browser running without a window, driven by code.
- **Interstitial / check page**: the page shown between tapping a link and reaching it.
- **JSON**: a text format for structured data, like `{"verdict": "suspicious"}`.
- **LLM**: a large language model, an AI that writes text.
- **MCP server**: a plug-in that gives Codex extra tools, such as up-to-date docs.
- **Playwright**: a library that controls browsers from code.
- **Prompt injection**: text on a page that tries to give orders to an AI.
- **Taxonomy**: T-Mobile's list of scam categories.
- **Uvicorn**: the program that runs the FastAPI app as a web server.
- **Virtual environment (venv)**: a private folder of Python packages for one project.
- **Replay mode**: using recorded decoy results instead of a live browser.
