# AGENTS.md: T-Defense

Codex reads this file from the repo root. Keep it short. Full plan: `teammate-build-kit/BUILD_OVERVIEW.md`.

## Goal
A hackathon prototype (hackUTD 2026, T-Mobile Safe Signal track). The primary product is a user-activated Chrome/Edge extension that checks current-page structural risk signals with a local FastAPI backend and shows prominent on-page warnings. The previous synthetic SMS concept and strictly local fictional-page Decoy Twin remain at /sms-demo. Sponsor classifier/data/taxonomy are pending; current rules are temporary and have no claimed accuracy.

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

## User-approved overrides (2026-11-07)
- App name: T-Defense. Physical folder and GitHub repository: T-Defense, as confirmed by the user.
- Build through replay GATE, then STOP for user review. No Stage 3 yet.
- Commit locally after every passing stage. NEVER push before explicit GATE approval.
- Starter files are pending. Stage 0 is DEFERRED, not done. Use synthetic examples with source="placeholder" and temporary triage(text). Never report accuracy on placeholders. Run starter-inspector and replace the adapter when files arrive.
- Replay fixtures are hand-written simulated evidence, not recorded browser runs. Label this visibly. Live mode must fail inconclusive until Stage 3.
- Dependencies, Chromium and temporary files stay project-local. Downloads were approved via the permission tool. No optional MCP or global configuration changes needed.
- Current session can explicitly load the copied skills and spawn the two reviewer roles; do not require a restart solely to continue this authorized milestone.

## Branding correction approved by user (2026-11-07)
- Project/app name is T-Defense everywhere, including docs and project-local skill references. Stage runner is now t-defense-stage-runner.
- Use pink/magenta, charcoal and white for the T-Defense app as explicitly requested. This overrides prior name/color restrictions for the app. Fictional Lumora demo pages retain their separate teal/sand identity and DEMO banners.
- Product screen must explain this is a sample inbox with temporary text rules and simulated page evidence. Guided demo buttons may launch the existing check flows. No live investigator or push approval is implied.
- Source kit copies may be updated for this explicit rename. No git history rewrite is required.

## GATE approved and continuation authorized (2026-11-07)
- User approved the replay GATE and instructed continued building. Stage3 and subsequent kit work are now authorized. The earlier stop-at-GATE restriction is satisfied.
- Earlier conditional GitHub push authorization now applies to passing reviewed milestones. Check secrets and remote history, never force push. Credential-manager errors must be reported honestly.
- Prioritize standout warnings before concerning links, attachments or information requests. Clearly distinguish observed download attempts from unscanned attachment contents. Local-only investigator policy remains mandatory.


## User-directed browser-extension pivot (2026-11-07)
- The requested primary product is now a Chrome/Edge ManifestV3 extension that inspects the user-activated current website, repeats checks and watches newly added content, then shows prominent pink on-page warnings. This supersedes the kit's decision to cut extensions and the mock-SMS-only product scope.
- Native extension JavaScript/HTML/CSS is authorized; keep the existing Python/FastAPI backend. No Node build system or new application dependencies.
- Real-page inspection is opt-in and local: derive bounded structural risk flags in the extension; send only standardized flags and origins to the loopback backend. Never collect or transmit passwords, typed/form values, raw message text, cookies or full page HTML. No persistence of browsing content.
- The local Decoy Twin's original allowlist remains unchanged. The new page-assessment endpoint never fetches or submits to real websites and never types canaries into them.
- Use synthetic pages for adversarial tests; a benign public-page smoke test may read structural metadata without submitting forms. Keep rules/coverage limits honest; do not promise detection of all phishing.
- Primary homepage becomes extension setup/test dashboard. Preserve the prior SMS demo at /sms-demo. Use the same reviewer/tester checks, progress records and passing local commits before publication.

## Domain reputation and email coverage (user request, 2026-11-07)
- Opt-in VirusTotal domain reports are authorized as the sole third-party backend request in page assessment. Only fixed GET https://www.virustotal.com/api/v3/domains/{validated-public-hostname}; no target fetching, URL/file submission, private/reserved/IP lookups or redirect following. The original Decoy allowlist remains unchanged.
- Key remains server-side in ignored .env/environment. Per-tab opt-in disclosure must state queried domains enter VirusTotal's community dataset; avoid confidential hostnames. Hostnames include subdomains; no full links/message text/form values are sent.
- Bound and cache requests within public API limits. Missing key, quotas, unknown/old reports, failures and all-timeout reports remain partial/inconclusive; never equate zero detections with safety. Runtime cache expires and is not a browsing-history database.
- Test email extraction with synthetic Gmail-like HTML only. Do not access or save real inbox messages. Show/Inspect findings survive rechecks, with clear historical/removed-element labels. No trained model, full URL reputation, attachment analysis or arbitrary-site dummy form submission is implied by this milestone.

## Social indicators and all-findings UI (user request, 2026-11-07)
- Combine local psychological/social text indicators into strict standardized social_signals IDs; no raw text or typed values in backend requests. User-supplied branded scam text may appear verbatim in synthetic regression fixtures; demo pages stay fictional Lumora.
- Never claim text indicators establish installed ransomware, malicious file contents, deepfake media, an offender's identity or actual grooming. Use factual observable requests and cautious next steps. No long-term chat/account access is authorized.
- Every detected live node gets automatic high-contrast numbered markers and a matching scrollable list row. Remove Show/Next buttons. Background checks retain headline counts and use a separate activity line. New risk ! pulsing must respect reduced motion.
- Preserve prior/out-of-batch/incomplete evidence with explicit historical labels. Manual rechecks clear resolved/removed evidence, not uninspected live nodes. Highlights live only in the extension shadow UI, never rewrite host element styles, and clear on Stop/navigation.

## Continuous monitoring and explicit local trust (user request, 2026-11-07)
- User now authorizes persistent all-supported-site monitoring until Stop. This supersedes per-tab-only activation: request optional HTTP/HTTPS permissions through a genuine toolbar gesture, register gated persistent bootstrap, persist only enabled/layout preferences locally. Keep pairing session-only and VirusTotal per-tab/origin opt-in, never broaden third-party sharing automatically.
- User added local trust database. Only explicit genuine-toolbar preview/confirmation may save an exact scoped content fingerprint. IndexedDB records hash/origin/kind/time, not plaintext, input values or full URLs. No negative-result auto-whitelist. Hash complete bounded text/effective controls incl external associations; refuse incomplete identities. Changed content/targets/metadata recheck. Revoke immediately invalidates pending cached bypasses. Whole-page trust is prohibited.
- Current request supersedes sticky removed-history display: prune closed/hidden/removed message rows automatically and reset same-page route scope. Reuse unchanged DOM rows/markers; routine footer remains constant; diagnostic updates stay collapsed. Compact movable bottom dock must leave profile controls usable. Uninspected/incomplete current evidence cannot silently become safe.
- Treat promotional email/image-heavy email and supported mail Spam-folder cues as low-severity local spam/coverage cautions, not proof of phishing or medical validity. No OCR, actual account access or subscription inference. Strong local security warnings short-circuit optional VirusTotal fallback.


## Disposable VM infrastructure (user request, 2026-11-08)
- New vm_kit is a separate opt-in Windows Hyper-V runner. The original app/investigator.py localhost/mock allowlist remains mandatory and unchanged. No direct target browsing by the host application.
- A trusted clean offline Windows base is cloned using a per-job differencing disk. One guest NIC, no guest default route/NAT, and external-to-guest Hyper-V ACLs permit only the authenticated bounded host broker. Broker permits public IPv4 only, pins DNS answers and excludes host/local routes/public egress endpoints. Actual deployment must pass per-job boundary probes; do not claim isolation active from source tests.
- PowerShell Direct is used only before untrusted navigation. During inspection results use a bounded authenticated raw JSON channel with a closed schema, no page text/URLs/HTML or verdict. VM credentials/tokens stay runtime-only. No mapped host folders, clipboard integration or guest accounts from the user's real services.
- Read-only browser behavior is a guest application policy; encrypted CONNECT traffic is opaque to the broker. No typing, form submissions, downloads, account actions or arbitrary AI tool use. AI optionally selects evidence-backed templates from standardized flags; no cloud model, no untrusted page instructions.
- Provisioning/admin/reboot/OS-media prerequisites are explicit. Current session cannot elevate and no ISO/base exists. Prepare/test source now; never report a live VM, verified hardware boundary, Windows/Ollama success or end-to-end extension integration until actually demonstrated.
