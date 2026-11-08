# T-Defense progress

- Current primary milestone: Page Guard v0.3 social indicators + all findings VERIFIED AND PUBLISHED;153tests pass, reviewed.
- Setup: DONE
- Stage 0: DEFERRED — starter files pending; user authorized placeholder adapter.
- Stage 1: DONE
- Stage 2: DONE
- GATE: APPROVED BY USER (2026-11-07).
- Stage 3: DONE
- Stage 4: PARTIAL — recovery/runner complete; sponsor evaluation deferred until starter files.
- Stage 5: LOCAL DEMO READY — sponsor integration/evaluation still pending.

## Decisions
- App T-Defense; physical folder and existing GitHub repository T-Defense.
- Python 3.13.7. No global installs. Project-local virtual environment and Chromium.
- Hand-written replay evidence will be explicitly labeled simulated.
- No accuracy metrics on placeholder data. Starter integration/evaluation deferred.
- Kit skills copied to .agents/skills; role definitions copied to .codex/agents.
- Optional MCP servers skipped; Python Playwright provides the browser checks.
- Permission tool approved target folder and setup downloads. Initial alternate-folder attempt was denied; no files created there. Python ensurepip initially failed on sandbox temporary directory; project-local work/tmp fixed it.


## Setup — DONE (2026-11-07, America/Chicago)
- Built: local venv, Chromium headless shell, 7 skills, 2 reviewer definitions, health endpoint and browser hello-world.
- Checks: pytest 2 passed; ruff clean; safety_reviewer OK; demo_tester PASS using source, screenshot and parent browser evidence. Child TestClient hung; parent run passed in 3.31s.
- Git: existing history and MIT license preserved; origin configured; .env and local runtime/cache directories ignored. No push.
- Cut or changed: optional MCP skipped. Explicit skill loading avoids a restart for this milestone. Stage 0 deferred by user until starter files arrive.
- Human should look at: browser health confirmed automatically; next is placeholder phone and triage.


## Stage 1 — DONE (2026-11-07, America/Chicago)
- Built: 11 synthetic source=placeholder messages, temporary triage(text), replaceable baseline adapter, plain HTML/CSS/JS phone and badges; placeholder score=null.
- Checks: pytest 7 passed, ruff clean, safety_reviewer OK, demo_tester PASS (independent source/screenshot/uncached lint, parent browser evidence).
- Cut or changed: Stage 0 deferred per user; no starter claims or accuracy metrics. CONTRACTS documents placeholder source and provisional categories. Raw links remain plain text until Stage 2.
- Human should look at: phone at localhost:8000; Stage 2 adds check links and simulated replay evidence.


## Stage 2 — DONE (2026-11-07, America/Chicago)
- Built: opaque token check links; 4 verdicts; 5 fictional Lumora scenarios and supporting pages; exact-local replay lookup; simulated=true hand-written evidence; unavailable live adapter; server-gated Open anyway; timeout/blocked/expired link handling.
- Checks: pytest 57 passed, ruff clean, safety_reviewer OK after fail-open schema fix, demo_tester PASS after clean-page advice/recovery copy fixes. Browser exercised A/B/C and suspicious/blocked/timeout paths at 380px with external requests blocked.
- Safety fix: completed evidence requires strict schema, full required fields, null error, local URLs and consistent origin flags. Malformed evidence becomes failed/inconclusive; regression tests cover it.
- Cut or changed: reset endpoint moved forward for GATE. Replay is simulated, never described as recorded live output. Category recovery remains an explicitly unavailable demo placeholder; full Stage4 scope deferred.
- Human should look at: GATE will run 3 fresh-server walkthroughs, then stop for review.


## GATE — AUTOMATED PASS; USER REVIEW PENDING (2026-11-07, America/Chicago)
- Checks: three fresh-server replay browser walkthroughs passed consecutively (5.18s, 5.12s, 5.17s); full suite 57 passed; ruff clean; safety_reviewer OK; demo_tester PASS via independent source/screenshot/lint and parent browser evidence.
- Evidence: screenshots under demo_backup/. Silent browser recording saved and verified: demo_backup/gate-walkthrough.webm, duration 90.08s, 1280x1000 VP9.
- No Stage3 work or GitHub push. Human approval has NOT been received.
- User-approved scope: Stage0 deferred, synthetic placeholders and temporary triage; no accuracy metrics. Live investigation and full recovery remain deferred.
- Kit recording assumption updated: installed Python Playwright can record a browser context, so tools/record_demo.py captures a replay walkthrough. User can also make their own narrated 90-second screen recording.
- Human should look at: GATE_REVIEW.md and localhost:8000, then approve or request changes. Starter files should arrive in starter/ unchanged; use starter-inspector next when present.


## Branding and demo-clarity revision — DONE (2026-11-07, America/Chicago)
- User requested T-Defense throughout and a pink/magenta app theme. Updated app title, pages, docs, kit copies, reviewer definitions and stage-runner skill name/path/references (t-defense-stage-runner). Current source scan found no previous-name occurrences.
- Added visible sample-inbox explanation and guided Obvious scam / Hidden risk / Plain bill notice buttons. Expandable explanation distinguishes working text/link/verdict code from simulated page findings and pending baseline/live/recovery work. Mobile now shows the same demo orientation.
- Backend logic and API contracts unchanged; only FastAPI display title changed. No live investigator or push authorization inferred.
- Parent pytest 57 passed (10.19s); ruff clean. Initial verification without loopback permission stalled; after network permission was granted the full run passed. New guided-flow assertions cover all three controls.
- Updated screenshots; previous superseded setup/stage1 branded images removed from current tree. Replay walkthrough regenerated and verified: 90.04s, 1280x1000; extracted frame confirms updated branding. Original Git history is retained.
- GATE remains automated pass / human review pending. See DEMO_EXPLAINED.md for a plain-language backend walkthrough.
- Reviewer checks: safety_reviewer OK; demo_tester PASS (independent screenshots/source/lint; parent browser tests). Final staged whitespace and key-pattern checks clean; only .env.example tracked.

## In-app notification and badge explanations — DONE (2026-11-07, America/Chicago)
- User requested notification warnings and hover explanations. Added one aggregated in-phone demo warning per inbox load, with Review message and Dismiss controls. Review focuses the first flagged badge and opens its explanation.
- Badges now support hover, keyboard focus, tap-to-toggle, Escape, and outside dismissal. Explanations use text-only triage reasons and disclose that page evidence remains simulated.
- Notification uses two gentle box-shadow pulses; reduced-motion settings disable animation. No browser/OS notification permissions, real SMS access or live investigation added.
- Checks: full pytest 57 passed (14.85s), ruff clean. Existing browser flow now verifies count, notification review/dismiss, mobile toggles, desktop hover/focus/Escape and reduced motion, plus prior safety/demo paths.
- GATE approval, sponsor integration, Stage3 and GitHub push remain pending. Backend/API logic unchanged.
- Review: safety_reviewer OK, demo_tester PASS through independent source/screenshot/lint and parent browser evidence. Full screen-reader testing was not performed.

## GATE approval and continuation (2026-11-07)
- User explicitly approved the GATE and requested continued building plus standout warnings for links, attachments and information requests.
- Starter folder checked again: empty. Stage0 and sponsor metrics remain deferred; no placeholder accuracy reporting.
- Initial authorized GitHub fetch/push attempt failed in Git Credential Manager (Windows MSYS named-object access); no push claimed. Continuing local build while checking native Git authentication.

## Stage 3 — DONE (2026-11-07, America/Chicago)
- Built: live fixed-script Playwright worker, bounded lifetime,2jobslots, shared URL/mode cache, responsive API and reset-generation protection. Local forms use only kit canaries; canonical evidence omits query values. Recorded replay captured from local runs.
- Warnings: prominent stop-before-continuing card for concerning/incomplete checks, explicit password/card/code advice; harmless attachment demo records/cancels download and blocks Open anyway. Attachment contents remain unscanned.
- Checks: full pytest81passed (104.15s), ruffclean, safety_reviewer OK and demo_tester PASS. Coverage includes initialURL no-launch, routeboundaries, externalport receiver0, blocked sockets, transientpopup/frame failclosed, JSON/text/embedded canary capture, timeoutcleanup, responsive health and live/replayUI.
- Review fixes: any uninspected popup/frame or blocked socket fails closed; canary matching covers decoded path/query/body but excludes origin to avoid matching port8000 as CVV000; taskkill failure falls back to termination/reaping. A timing test now measures a reused client's server response rather than HTTPclient setup.
- GitHub connector now verified as truncations with push permission; nativeCLI credentials still unavailable. Publication not yet claimed.
- Starter files remain empty. Stage0 deferred and no placeholder accuracy metrics. Continuing to recovery and evaluation infrastructure.

## Stage4 — RECOVERY/RUNNER COMPLETE; SPONSOR EVALUATION DEFERRED
- Built: category-specific recovery API and accessible card checklist, fixed safe-text fallback; independent contact, password changes, two-step/PIN and7726 guidance from kit.
- Eval runner rejects non-starter rows, requires integrated baseline for classifier metrics, supports seed42 held-out scoring when tuned, explicit abstention confusion column and resolved accuracy. Missing starter/adapter is reported unavailable. Seven local mock outcomes stay separate and are not an accuracy claim.
- Checks: full pytest89passed (99.99s), ruffclean; after reviewer requested accurate fallback provenance label,8focused recovery/eval checks passed. Safety reviewer OK; demo tester PASS through independent screenshots/source/lint and parent browser evidence.
- Current eval/results.md reports no sponsor metrics. Sponsor evaluation cannot be marked DONE without provided classifier/data/taxonomy; Stage0 remains deferred.
- Continuing only independent demo polish, final live/replay rehearsal and source publication. GitHub connector is verified for truncations/T-Defense; nativeCLI authentication unavailable.

## Local demo polish — DONE; SPONSOR INTEGRATION STILL DEFERRED
- Full final suite89passed (101.62s), ruffclean. Three fresh-server replay rehearsals passed in6.54s,6.43s,6.21s. Live browser rehearsal and bounded investigator tests pass in the full suite.
- Refreshed recorded replay from current local runs; separate live evaluation matched all7expected fictional-page behaviors. This is not classifier accuracy. Slow-page failure remained bounded near8seconds; attachment contents remain unscanned.
- Reset demo clears jobs/cache and obtains fresh check tokens; browser regression verifies token replacement.
- Safety/demo reviewers approved source/reset/docs pending final recording completion. Original local stage commits and media will be preserved on a local archive branch before source-main synchronization.
- Connected GitHub account truncations is verified with push permission. NativeCLI helper authentication is unavailable; publish a reviewed UTF8source snapshot using the connected account, without force updates. Exclude generatedPNG/WebM backups, starter files, runtime/cache folders and environment secrets; include only empty-key .env.example.
- Source export uses committed Git blobs and a temporary index to compute an exact expected source-treeSHA. Public tree must match before the guarded expected-HEAD ref update. Publication is not yet claimed.
- Stage0 and actual sponsor evaluation remain deferred because starter/ is empty. Use demo-local-ready rather than demo-final; no full-project completion claim until starter integration and evaluation pass.
- Final recording saved and inspected:89.88seconds (approximately90s),1280x1000VP9; extracted15s frame confirms current T-Defense branding, prominent action warning and recorded-replay disclosure. Includes attachment scenario and recovery.
- Final safety/demo reviewers cleared source/docs/reset and publication preparation; recording verification condition is now satisfied.
- Local milestone tagged demo-local-ready. Actual sponsor evaluation is not complete and demo-final is deliberately not claimed.

## GitHub source publication — VERIFIED (2026-11-07)
- Published reviewed source checkpoint0e7bd1178fe75ea298b921f9cabdec8667ef3347 on truncations/T-Defense main using the authenticated GitHub connection. Existing remote commits and MIT license retained; nonforce update used the verified prior head as a lease.
- GitHub tree fb336100674f1d434a16918c3fcd8de4a7d89bd4 exactly matched the temporary-index source tree exported from reviewed local milestone5e862ef9401ca10a85324df58006b8d22d13b8be. Anonymous fetch independently confirmed the published commit and tree.
- Published85UTF8source/config/docs/test files. Excluded14generatedPNG/WebM media files from public source; they remain local and in original local stage history. starter/ remains empty. Only .env.example is tracked; secret-pattern and environment exclusions checked.
- Original local stage history is preserved on local/stage-history-2026-11-07 (including all passing stage commits and binary demo backups). Public GitHub uses reviewed source checkpoint commits because the native Windows Git credential helper is unavailable.
- This publication record will be published as a documentation-only follow-up; local main will then align to the verified public source tree without deleting working files. The archive branch will retain the publication-log commit too.
- Current result: local demo ready,89tests pass,3freshreplayrehearsals pass, live investigations/recovery/warnings implemented. Sponsor integration and actual sponsor-data metrics remain pending; no placeholder accuracy claims.


## Browser Page Guard — USER-DIRECTED PIVOT (2026-11-07)
- Replaced primary mock-SMS presentation with a real Chrome/Edge MV3 extension, downloadable bundle, local setup/pairing dashboard and dynamic synthetic test lab. Previous concept remains /sms-demo. Kit extension cut superseded by explicit user request; stage-runner/reviewer/progress process retained.
- Browser observes initial/manual, DOM mutation, visible-tab8second periodic and concerning interaction events. Local collector derives bounded message/link/form/attachment metadata. Worker sends only standardized flags, input kinds and origins to authenticated fixed-loopback /api/page/assess; Python applies real structural rules, returns evidence/nextsteps and unique scanIDs. No real-page fetches or form submissions by backend; legacy local Decoy allowlist unchanged.
- Prominent pink overlay expands for fresh risks and recycled messages; hover explains findings, Show element locates them, toolbar independently shows count. Supported concerning clicks/submissions pause for review with explicit Continue once. Reduced-motion styling and fresh-warning live announcement included. Form values, passwords, raw messages/HTML/cookies and full URL queries are never transmitted. Backend retains only aggregate counters, not snapshots/history. Pairing is process/browser-session-only.
- Review fixes: invalidate pending completions on navigation/run/document changes; verify current snapshot before rendering; pending changes never retain a clean indicator; unavailable clears old findings; overrides bind resolved destination/method/base metadata. Include submitter formaction destinations and external form-associated inputs. Mark root/control budget truncation and frames inside discovered components as partial.
- Verification so far: focused17tests passed actual MV3 worker/content/backend traffic. Initial full106tests passed in133.51s; final full107tests passed in168.91s including actual HTTPS collector regression for form overrides/external fields and open-root coverage. Ruff check/format and JavaScript syntax checks clean. Read-only actual example.com check reached backend (no forms/links submitted); automation test copy grants only example.com, shipped extension relies on user-invoked activeTab.
- Final source safety review: no blockers. Demo tester source PASS (internal typography/alert fixes verified); actual screen-reader audio not tested. Final regression condition satisfied. Fresh setup/dashboard/download and preserved SMS route checks passed. Finalsource example.com smoke completed a real backend check without submissions.
- Honest limits: temporary structural rules, legitimate-page false alarms and missed risks possible; no classifier accuracy claims. Frames/closed trees/attachment contents unscanned, bounded page coverage. Earlier page handlers/programmatic navigation/submission and middle/context-menu actions can evade interception. Page overlays can be tampered with; toolbar remains independent. No store publication or production-ready claim.
- Starter classifier/dataset/taxonomy still absent; Stage0 and sponsor metrics remain deferred. User-facing ZIP/quickstart/screenshots prepared outside public source. Committed passing local milestone9d0814dab5f2c9070f3ce62afd40e388cb0eaae5 and published source checkpoint80c9d7f7f66614ace4a8a78aeedf5afd8644ab53 through the connected GitHub account. Nonforce expected-head update succeeded; anonymous fetch confirmed the commit. Published tree5586289d6d76e9411d281fc0e1f789dc86f05ae4 matches the103file reviewed Git source exactly. All indexed files passed key/environment scans; only .env.example is tracked. Original local stage commit will remain on local/extension-history-2026-11-07 before main synchronization. This progress record is a docs-only follow-up.

## Reputation + email/inspection fixes — VERIFIED LOCALLY (2026-11-07)
- User requested stronger detection, VirusTotal domain checking, fixes for disappearing inspected findings and Gmail misses. User will configure API key locally; none was requested in chat or installed by the agent.
- Built: opt-in fixed-endpoint domain-report enrichment, server-only key, strict public hostname validation, shared4/minute500/day process budgets,429 backoff, bounded expiring cache, validated counts/date and honest incomplete statuses. No live provider call has been made; test transport is explicitly mocked.
- Fixed collector priority for rendered email links, local supported Google wrapper extraction, hover/focus selected-link scans, contextual account-action caution and current-page domain mapping. No actual Gmail account/message accessed. Coverage remains bounded; full URL reputation, trained classifier, arbitrary-site investigator, attachment analysis and complete frame coverage remain unimplemented.
- Fixed finding loss: pending changes keep prior node mappings without a clean status; Show/right-click Inspect pins reviewed evidence, labels changed/removed nodes historical and permits explicit close. Snapshot/document stale-response protections remain.
- Focused39tests passed (36.25s) including actualMV3/FastAPI with only VT transport mocked: email beyond260navigationlinks, decodedtarget, no provider requests without opt-in, positive domain warning, pinned/removed finding, missing-key/quota/timeout/zero-detection UI and privacy sentinels. Final full131tests passed in137.36s; latest-source focused42tests passed in39.51s after serialized consent/start-stop generation hardening. Tests include all-timeout, config-key nonexposure, current-page priority, Inspect pinning, pending-check opt-out and delayed-connect cancellation. Ruff check/format and JavaScript syntax clean. Safety reviewer OK; demo tester PASS, with passing test conditions now satisfied.
- Docs/API/.env.example updated. No production detection accuracy claim. Fresh final-source read-only public-page extension smoke and dashboard/download/email-lab checks passed. Current backend reports no configured VirusTotal key. No real Gmail message was accessed and no live VirusTotal request was made. Refreshed v0.2 ZIP and local key setup guide are ready. Passing local stage commit3826dbb23b969063572563f2b11ef10bd2d6e92b published as checkpointc26ebfb23751889de71c930d20bb08048f317b77 using a guarded nonforce update. Anonymous fetch confirmed exact source treeff9251e47375943e904920846f2245b42e378579 across106source files. Index and export secret checks passed; only .env.example tracked. Original local stage/doc commits will remain on local/reputation-history-2026-11-07 before main synchronization. This factual record is a docs-only follow-up; user key configuration/live provider validation remain pending.

## Social indicators + all findings — VERIFIED LOCALLY (2026-11-07)
- User requested the missed reward/account phishing case, all automatic highlights/scrollable rows, removal of Show/Next, stable count and flashing !. Broader listed threats are handled as visible text indicators only, never asserted as proven malware/media/identity/grooming.
- Added14 standardized combined social flags, whole-message link context incl supported Discord-style markup, explicit backend evidence/nextsteps and cautionary-negation handling. Exact supplied Nitro text and14 threat-pattern variants plus benign/cautionary cases pass actual-collector-to-Python tests; no brand/domain hardcoding.
- Replaced single-finding UI with auto numbered yellow/dark/red shadow markers and all-row scrollable list; each row locates its source. Headline separate from activity, unreadrisk ! slowpulse/reduced-motion. Retained historical rows are labeled; manual partial refresh preserves uninspected live/incomplete reputation evidence, clears removed evidence explicitly, and releases detached nodes. No host style mutations.
- Review fixes: native-validation replay bypass deleted in finally; outage announcements gated to transitions; partial refresh cannot discard out-of-batch live evidence. Tests for invalid required form replay and retained email/VT flow pass. Initial marker test measured across separate renderer tasks and raced scrolling/RAF; after3 attempts moved both measurements into one bounded eventual renderer assertion, preserving exact coordinate checks for every source node.
- Focused23existing browser/social checks passed; new14-node highlight/list test now passes all exact-position checks, scrolling, stable headline through mutations+periodic checks, reduced motion, partial retention and explicit removal refresh (16.85s). Full153tests passed in162.11s. Latest-source desktop/mobile marker test passed in17.12s including zero headline DOM rewrites through mutations/periodic scans. Ruff check/format and JS syntax clean. Parent inspected desktop/mobile screenshots; moved marker number labels outside link text. Fresh actual-extension lab run produced6mapped findings across reward/software/extortion, and final read-only example.com check passed with provider disabled. Safety reviewer OK and demo tester PASS, test conditions satisfied. Refreshed v0.3 ZIP/guide ready. Passing local stage4a0bef659ddd9a4c5e14d9a16302724c30ff346c published as checkpoint04c6879787c0db2e9c0e0c57fb8b670fbe4e26fa via expected-head nonforce update. Anonymous fetch confirms exact source tree05c2a241b2ebda49f38f7c9f514b17a83217db8e across109UTF8files; staged/export secret checks pass, only .env.example tracked. Local stage/doc commits will be preserved on local/social-history-2026-11-07 before main alignment. This factual record is a docs-only follow-up. No live VirusTotal call or real user account access performed.

## Continuous/current-scope checks + local trust — VERIFIED LOCALLY (2026-11-07)
- Latest user scope: crypto giveaway and independent local spam/image-ad cues; no UI/footer flicker, centered!, clear closed-message findings, always-on across sites, nonblocking movable dock; then explicit local database for trusted exact elements.
- Added local decimal crypto multiplier detector, separate promotion/image-heavy/Spam-folder cautions and strong-local-risk VT short-circuit. No OCR, medical judgment, sender subscription inference or account API access. User image transcribed only into synthetic test examples; no real mail visited.
- Persistent mode uses optional website grant from toolbar, registered bootstrap, per-document generations and global enable/stop serialization. Browser preference persists, pairing stays session-only, new-site VT consent stays off. Native IndexedDB trust records SHA/origin/kind/time only; toolbar preview/token+fingerprint revalidation, no automatic whitelisting; changed form fields/external controls/targets invalidate trust. Revocation generation protects pending filters. Runtime content still fingerprints metadata to detect changes.
- UI: compact bottom-right movable/keyboard dock, centeredSVG!, reused list/facts/markers, static monitoring footer with diagnostic disclosure. Hidden/removed/new-route messages clear immediately; changed covered structural evidence refreshes each valid scan. Found/fixed dynamic inline positions losing to all:initial!important, plus repeated fresh/unread reconstruction. Prior v0.3 removed-history retention is superseded.
- Focused64local/backend tests pass; core actualMV3 continuous browser test passed crosssite/newtab/reload/profile-restart trust persistence, hash-only storage, metadata changes and revoke. Existing3browser tests passed50.18s after updated current-scope expectations. Full suite159passed235.62s, including delayed-revoke/Spam-context cases. Latest actual-MV3 continuous/email/findings3passed52.13s including pointer/keyboard movement. Ruff clean; safety reviewer OK and demo tester PASS. Docs/API/permission/trust disclosure updated; Fresh final-backend actual-extension lab crypto2 -> automatic clear0 -> promotional caution passed; read-only example.com reached backend without actions/provider calls. Parent inspected screenshot. v0.4 ZIP contains10 byte-matched files; guide ready. Staged secret checks follow before commit/publication.

- Publication verified: passing local stage3733bcc1584f36428d5136db39d2eeda7f5d9788 published as source checkpoint433f935640c56d0e0c18d9c097828347fdcc89ad using guarded nonforce update. Anonymous fetch confirms exact tree6bcb754c24a08a2004c4468dfc9ae09f56b8da95 across112UTF8source files. Staged/export environment/key scans passed; only .env.example tracked. No real mail access or live VirusTotal request. Local source/doc commits will remain on local/continuous-trust-history-2026-11-07 before clean exact-content main alignment. This factual publication record is a docs-only follow-up. Backend restarted on loopback8000; v0.4 guide/ZIP/screenshots ready.
