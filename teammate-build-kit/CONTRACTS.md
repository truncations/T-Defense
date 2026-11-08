# CONTRACTS (DRAFT: finalize after Stage 0)

> **Status: DRAFT — user-approved placeholder milestone.** Field names for labels, categories and scores are guesses until Codex inspects `starter/` in Stage 0. Codex updates this file then and marks changed sections "finalized after Stage 0". Keep everything else stable so the frontend doesn't break.

All endpoints live in the one FastAPI app on `http://localhost:8000`. Everything is JSON, and the store is in memory (wiped on restart).

Verdict values (fixed): `likely_scam`, `suspicious`, `looks_fine`, `inconclusive`.
Confidence values (fixed): `low`, `medium`, `high`. These are words, not fake-precise percentages.

---

## `data/scenarios.json` (the planner writes extra entries in this format)
```json
[
  {
    "message_id": "team-001",
    "source": "team",
    "sender": "LumoraAlerts",
    "text": "Lumora Wireless: your line will be suspended today. Verify now: http://localhost:8000/mock/lumora/verify.html",
    "expected_label": "scam",
    "expected_category": "account_suspension",
    "note": "Demo scenario A"
  }
]
```
- `source`: `"starter"` (copied from T-Mobile's set) or `"team"` (ours).
- `expected_label` and `expected_category` are for evaluation only. **Never send them to the triage function.**
- Team links must point to `http://localhost:8000/mock/lumora/...`.

---

## `GET /api/health`
```json
{"status": "ok", "demo_mode": "live"}
```

## `GET /api/scenarios`
Returns the list above without `expected_*` fields.

## `POST /api/assess`
Request:
```json
{"message_id": "team-001", "text": "Lumora Wireless: your line will be suspended today. Verify now: http://localhost:8000/mock/lumora/verify.html"}
```
Response:
```json
{
  "assessment_id": "a_7f3c",
  "message_id": "team-001",
  "triage": {
    "label": "scam",
    "category": "account_suspension",
    "score": 0.81,
    "abstained": false,
    "reasons": ["Urgent deadline (\"today\")", "Asks you to verify an account through a link"]
  },
  "badge": "likely_scam",
  "links": [
    {"link_id": "Lk9x2QmZ", "display_text": "localhost:8000/mock/lumora/verify.html", "check_url": "/check/Lk9x2QmZ"}
  ]
}
```
- `score` may be `null` if the baseline gives no score (Stage 0 decides).
- `badge` is triage-only: `likely_scam`, `suspicious`, `unsure` (abstained), or `no_signs`.
- Side effect: if `badge` is not `no_signs` and a link exists, the server starts an investigation in the background.

## `POST /api/links/{link_id}/investigate`
Starts an investigation if none exists. Returns `{"link_id": "...", "status": "pending" | "done" | "failed" | "blocked"}`.

## `GET /api/links/{link_id}/verdict`
```json
{
  "link_id": "Lk9x2QmZ",
  "status": "done",
  "verdict": "likely_scam",
  "confidence": "high",
  "confidence_reason": "The message used pressure tactics AND the page sent our decoy's card number to a different site.",
  "evidence": [
    "The page asked our decoy for a password and a card number.",
    "When the decoy submitted, the data went to a different site (127.0.0.1) than the one you'd see.",
    "The page showed a 10-minute countdown to rush you."
  ],
  "unknowns": [
    "We only checked what the page did for an automated visitor. Real scam pages can act differently.",
    "We did not check who owns this website."
  ],
  "next_steps": [
    "Don't open this link.",
    "If you're worried about your account, call the number on your bill or card, not the one in the message.",
    "Report it: forward the text to 7726 (SPAM)."
  ],
  "investigation": { "...": "see below" },
  "triage": { "...": "same as in /api/assess" }
}
```
- `status: "pending"` → the frontend polls once a second for up to 15 seconds, then shows `inconclusive`.
- `failed` or `blocked` → `verdict` is `inconclusive`, unless triage is a strong `likely_scam`. **Never `looks_fine`.**
- `looks_fine` wording on screen: **"No warning signs found"**, always shown with `unknowns`.

## Investigation object (from `app/investigator.py` or `data/demo_replay.json`)
```json
{
  "mode": "live",
  "status": "done",
  "start_url": "http://localhost:8000/mock/lumora/verify.html",
  "final_url": "http://127.0.0.1:8000/mock/lumora/collect.html",
  "redirect_chain": ["http://localhost:8000/mock/lumora/verify.html"],
  "cross_origin_final": true,
  "fields_requested": ["password", "card_number", "one_time_code"],
  "canaries_sent_to": ["http://127.0.0.1:8000/mock/lumora/collect.html"],
  "canaries_cross_origin": true,
  "urgency_phrases": ["10 minutes", "suspended today"],
  "download_attempted": false,
  "ai_directed_text": false,
  "duration_ms": 2140,
  "error": null
}
```
`demo_replay.json` is an object keyed by mock page path (`"/mock/lumora/verify.html": { ...investigation... }`), each with `"mode": "replay"`.

## `GET /api/recovery?category=account_suspension`
```json
{"category": "account_suspension", "steps": ["...", "..."]}
```

## `POST /api/report` (stretch S1)
Request `{"link_id": "Lk9x2QmZ"}` → `{"reported": true}`. Stores only `sha256(url)`, the category and a timestamp.

## `GET /api/reset` (Stage 5)
Clears the store. Returns `{"reset": true}`.

## Pages (HTML, not JSON)
- `/`: the phone (`static/phone.html`)
- `/check/{link_id}`: the check page (`static/check.html`; reads `link_id` from the path)
- `/mock/lumora/...`: demo pages (`mock_sites/lumora/`)

## Interim contract additions (user approved, 2026-11-07)
- source also accepts "placeholder" until starter-inspector replaces the temporary examples. All current examples are placeholders.
- triage(text) remains the public interface. app/baseline.py predict is the future adapter boundary. Placeholder scores are null; categories are provisional.
- No accuracy or abstention metrics are reported on placeholder data. Stage 0 is deferred, not finalized.
- GET /api/health includes demo_mode, with replay as the interim default.

## Replay milestone clarifications (2026-11-07)
- Investigation fixtures contain simulated=true. They are hand-written examples, not prior live runs. duration_ms=0 is not a measured browser latency.
- Live mode is deliberately unavailable until Stage 3 and returns failed/blocked, never silently replayed evidence.
- Replay requires an exact local fixture URL; external hosts, alternate ports, userinfo, query/fragment, encoded paths and path traversal are rejected. Blocked URLs return inconclusive unless text alone is strongly scam-like.
- GET /api/links/{link_id}/open permits only completed suspicious/looks_fine local demo links, returning a 303 redirect. Other links return 403.
- GET /api/reset is implemented early for fresh-server GATE checks. All state remains process-local.
- Recovery at Stage 2 is a labeled placeholder with the bill/card contact advice; full category checklists remain Stage 4.


## Stage 3 extensions and resolved interim restrictions
- GATE approved by user. Live mode is implemented on local fictional pages; the prior stub/unavailable restriction is superseded.
- Investigation adds recorded (bool), form_targets (list of canonical URLs), blocked_requests (nonnegative int), and uninspected_content (false for a completed result). simulated=true denotes hand-written evidence; replay+recorded=true denotes captured local browser output, not a current check.
- Canonical URLs omit query values so canaries are not copied into evidence addresses. Initial URLs still forbid queries; local form requests may carry synthetic query values. Resource requests are restricted to /mock/ plus the exact /static/mock.css stylesheet on the same allowed hosts/port. WebSockets/service workers are blocked.
- Appearance of additional pages/frames fails incomplete; blocked operations cannot count as clean. Download attempts are canceled and attachment contents are explicitly unscanned.
- /open returns403 for download attempts even if the verdict is suspicious. Other eligible local completed links retain the existing gating.
- Twelve source=placeholder messages now include a harmless attachment-download example. No sponsor accuracy claims are introduced.
- Jobs use a bounded worker, at most2concurrent browser processes, URL/mode cache and reset generation protection. Individual investigations are capped below10seconds; queued starts can add waiting time. Frontend polling retains fail-to-inconclusive behavior.


## Stage4 recovery and evaluation additions
- GET /api/recovery accepts payment, identity, gift_card, account_suspension, account_security, or falls back to general. All categories include independent-contact, password change, two-step/account PIN and 7726 steps; selected sensitive-field evidence chooses the card's checklist.
- The recovery placeholder is superseded by the implemented checklist and local API fallback. No external links are emitted.
- eval/run_eval.py only reports classifier metrics when inspected normalized rows have source=starter and the real baseline adapter returns valid normalized predictions. Placeholder/team rows are rejected. Missing files/adapter are reported as unavailable, never substituted with demo metrics.
- Future Stage0 normalization target: data/starter_eval.json, a list of {source:"starter",text,label?}, with observed labels normalized to scam/legitimate. --tuned applies seed42 70/30 holdout, scoring only30%; --sample is a smoke-test option. Actual input mapping must come from starter inspection, not guesses about the original files.
- Confusion tables include an explicit abstained column. Abstentions count as misses for overall accuracy and scam recall; resolved-only accuracy and abstention rate are reported separately.
- Mock-page expected/observed outcomes remain a separate table labeled not an accuracy claim. Attachment contents remain unscanned.


## Browser Page Guard extension (user-directed scope revision, 2026-11-07)

Primary GET `/` and `/extension` serve extension setup; GET `/sms-demo` preserves the previous phone UI. GET `/extension-lab` serves synthetic dynamic scenarios. GET `/api/extension/download` returns a ZIP containing fixed public extension files only.

GET `/api/extension/pairing` is local/same-origin only and returns `{pairing_code}` with no-store; this generated process key is never a committed config secret. POST `/api/extension/connect` and `/api/page/assess` require `X-TDefense-Key` plus `X-TDefense-Client` (extension ID); present Origin must match that extension. Host is fixed loopback port8000. No permissive CORS is enabled.

POST `/api/page/assess`: strict `{page_origin, reason, elements, coverage}`. At most200 elements,128KiB. Each signal includes opaque element_id, kind(form/link/message), standardized urgency/sensitive_request/gift_code_request/has_link/download flags, file_kind, target_scheme, target_origin, displayed_origin and sensitive_fields kinds. Origins have no credentials/path/query/fragment. Raw text, page HTML and form values are forbidden extra fields. Coverage reports elements_seen/elements_scanned/truncated/frames_unchecked. Exact enums/constraints are defined by Pydantic models in app/page_guard.py.

Returns scan_id, scanned_at, engine, status, verdict, warning_count, warnings, coverage and unknowns. Each warning identifies its element_id, rule IDs, title, severity, evidence and next_step. No match means no observed signs, never a safety guarantee; limited coverage is inconclusive. Backend errors are unavailable in the overlay. GET `/api/extension/stats` contains aggregate scan/finding counters and last time only. Snapshots/origins are not retained.

The browser worker calls only the fixed local backend. The content script keeps node mappings and locally derived text signatures; neither raw text nor signatures leave the page. Result rendering checks current snapshot identity; guarded overrides bind to destination/method metadata. Background completions must match the current run and document. This API never invokes the legacy local-only investigator or fetches real destinations.

## Page Guard v0.2 additions

Signal.kind also permits page; the collector includes the current document as a mapped node. Signal optionally adds email_context, account_action and wrapped_destination booleans. Total snapshot cap remains200 including that page signal. Wrapped links transmit only locally decoded destination origins. Batch priority favors focused links and rendered emails ahead of navigation; this is bounded coverage, not complete scanning.

Trusted extension worker adds X-TDefense-Reputation: enabled only after popup opt-in. Page scripts cannot toggle it. /api/page/assess otherwise retains its existing shape and adds reputation={enabled,status,domains}. Each domain result has validated domain, provider=VirusTotal, status, and when valid counts/analyzed_at/stale/cached. Statuses include disabled,not_configured,no_public_domains,checked,partial,pending,rate_limited,unknown,stale,unavailable,not_checked,no_reported_detections,malicious,suspicious as appropriate to aggregate/domain level. Positive findings merge into warnings; enabled incomplete checks set status=partial and no-warning verdict=inconclusive. Zero reports or only timeouts never become a safety claim. Backend GET /api/extension/config returns only virustotal_configured boolean (no-store, loopback Host).

Only validated public hostnames go to fixed VirusTotal domain-report GET API with backend x-apikey. No redirects/proxy or destination fetches. Rate budgets shared under lock; pending requests deduplicate, bounded memory cache expires and no page snapshot persists. Browser findings retained during review are labeled previous evidence while pending/removed, with current scan state separate. Node mappings and review history clear on pause/navigation. Extension control message REPUTATION is restricted to its genuine popup; permission/run generation protects old responses when settings change.

## Page Guard v0.3

Signal optionally adds social_signals: at most14 strict known IDs (defined by Signal Literal and app/social_rules.py). The extension derives them locally from normalized bounded visible text; message context includes supported Discord-style bodies and links in separate paragraphs. Python requires links for reward flags, combines explicit severity/evidence/nextsteps with structural rules, and rejects arbitrary flags/raw fields. No trained classifier or malware/media analysis is added.

UI warning IDs still map to collected DOM nodes; session-only node-keyed ledger tracks current/pending/changed/outside/removed statuses separately from backend scan state. Every marked live node has matching numbered shadow-overlay rectangles and list row; selection scrolls to that node. Disconnected references are released and removed historical rows capped50. Background checks do not reset warning counts. Manual requests use generation protection and refresh only covered structural evidence or completed negative domain reports; out-of-batch/incomplete prior evidence survives. No safe-element classification exists.

No new API endpoints or provider calls. Snapshot/document authentication and VirusTotal constraints unchanged. Data-warning-count is latest backend finding count; data-finding-count includes retained review rows; data-marked-count counts connected marked nodes. Header/current-vs-previous row labels distinguish them. Check failures never clear known findings. Continue once bypass is deleted in finally after a synchronous replay, even if native validation suppresses submission.

## Page Guard v0.4

Signal.social_signals additionally permits crypto-multiplier,promotional-email,image-heavy-email,mail-spam-folder (max18). Warnings add category=possible_spam when all matched rules are local spam/coverage cues; otherwise security_risk. Coverage optionally includes trusted_skipped aggregate; filtered trusted nodes are not sent. Result.reputation.status local_findings means explicit local medium/high security evidence made an external lookup unnecessary. New-site reputation consent remains off.

Extension protocol adds gated TDEFENSE_HELLO/bootstrap registration for continuous mode, genuine-popup START/STOP globally and TRUST_PREVIEW/TRUST_SELECTED/TRUST_ENTRIES/TRUST_DELETE/TRUST_CLEAR/RESET_POSITION. TRUST_PREVIEW token storage contains fingerprint/origin/kind/documentId/token only; returned preview text is ephemeral in popup, never database or Python. Confirmation rechecks current document/fingerprint. Content can request only own-origin TRUST_LIST/position and cannot commit trust. TrustStore IndexedDB elements store keyed fingerprint with origin index; metadata includes kind/createdAt only, capped5000 without eviction.

FilterTrusted excludes exact locally trusted scope/descendants, adjusts elements_scanned and trusted_skipped, preserves coverage truncation. SHA256 source includes site origin, complete bounded local visible text and effective link/form/input metadata, associated external controls and labels; values never enter identity. Oversized/unsupported secure-crypto identities cannot be trusted. Source strings remain local to content script; only fingerprints/ephemeral preview cross browser messaging, never backend. Generation checks protect revocation, navigation and settings from stale async responses.

UI is current-scope: closed/hidden/removed nodes prune immediately; valid negative covered evidence resolves automatically. Unchanged row, fact, marker and headline nodes remain stable. Footer status is constant during ordinary checks, diagnostic scan IDs remain under disclosure. Default bottom-right compact dock supports pointer/keyboard relocation saved as bounded ratios. Centered SVG risk icon opens findings. No safe certification or complete frame/file/media/JS analysis added.


## Shared panel position v0.4.1

TDEFENSE_POSITION validates bounded viewport ratios, serializes local preference updates/reset, and broadcasts TDEFENSE_POSITION_CHANGED {position:{x,y}} to other open tabs. New documents read the same global panelPosition preference. Content generation guards prevent a delayed initial read overriding a newer move/broadcast. Each viewport clamps locally; no page data, backend requests or conversation analysis is added.

Worker errors optionally use code TRANSIENT for network/timeout/HTTP408/429/5xx failures. Content retries the same bounded snapshot once after600ms, subject to active/scope/trust/manual-generation checks. Authentication/validation failures do not use TRANSIENT. Confirmed unavailable status survives pending/manual retries until validated success; stale failed requests cannot overwrite new scope state.
