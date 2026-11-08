# AGENTS.md: extension and page-assessment rules

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

## No pairing (user request, 2026-11-08)
- Pairing and installation approval are removed; this supersedes the earlier automatic-pairing approval rule. The loopback service authorizes only requests whose Origin is chrome-extension://<the X-TDefense-Client id>, because browsers always set Origin on extension fetches and the custom header forces a CORS preflight for websites.
- Paused downloads capture blob:/data: files at pause time and replay them through a fresh bypassed anchor, because sites revoke temporary links immediately after clicking them.
