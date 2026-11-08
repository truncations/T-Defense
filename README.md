# T-Defense

A Chrome/Edge browser extension that monitors supported websites until you stop it, watches new content and periodically reassesses links, messages and sensitive forms. A prominent pink overlay explains concerning signs and pauses supported risky clicks/submissions for review. **Actual extension signals are assessed by the local FastAPI backend; these page results are not replay fixtures.**

## Browser extension: current primary demo

1. Start the local backend using the command below. There is no setup page or pairing: the extension connects to it automatically whenever it is running.
2. Download/extract the extension, or use this repository's `extension/` folder directly. In `chrome://extensions` or `edge://extensions`, enable Developer mode, choose Load unpacked and select the folder containing `manifest.json`.
3. Open the toolbar popup, click **Start everywhere** and grant the optional HTTP/HTTPS website access once. Monitoring then follows supported tabs and sites until **Stop everywhere**. The preference survives browser restarts.
4. To see warnings reliably, open http://127.0.0.1:8000/extension-lab, add a synthetic message, form or attachment. Click the compact dock’s ! button for numbered findings. Every completed result has a real backend scan ID/time.

Checks repeat periodically and after DOM changes; browser background throttling can delay them. Pause everywhere stops all tabs. The engine uses temporary structural rules, not the pending sponsor classifier. It can miss phishing and can warn on legitimate pages. It inspects at most 200 candidates and bounded open component trees; frames, closed components and attachment contents remain unscanned. Programmatic navigation/form.submit, earlier page handlers, middle/context-menu clicks and unsupported frames may evade action interception. A page can tamper with injected overlays: also check the genuine toolbar badge/popup. This is a developer prototype, not a production security guarantee.

The extension reads visible text locally to derive flags but sends only standardized flags, field kinds and site origins to the fixed loopback backend. It never sends raw messages, HTML, typed values, passwords, cookies or full URLs/queries. Python never fetches real sites or submits their forms. Pairing is session-only; browsing snapshots are not persisted. Explicit trust decisions are persisted as origin-scoped hashes in browser-local IndexedDB. The local Decoy Twin described below remains a separate fictional-page-only demonstration.

Extension implementation and permissions: [extension/README.md](extension/README.md). The previous SMS concept is preserved at http://127.0.0.1:8000/sms-demo.

All 12 messages are synthetic (`source: "placeholder"`). Text assessment still uses temporary rules because the provided classifier, dataset and taxonomy have not arrived. No accuracy claims or placeholder-data metrics are reported.

## Run

From the repository root on Windows (Python 3.13.7 tested):

```powershell
$env:DEMO_MODE = "live"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open http://127.0.0.1:8000/ for extension setup; `/sms-demo` for the previous concept. Stop with Ctrl+C. Run live mode without `--reload` on Windows. Use `$env:DEMO_MODE = "replay"` for the backup mode; it reuses clearly labeled browser evidence recorded on our local mock pages. The app reads environment variables and does not automatically load `.env`. The default when unset remains replay.

## Previous SMS concept

- **Obvious scam:** urgent text plus a page requesting fake credentials and payment details.
- **Hidden risk:** ordinary-looking tracking text; the page redirects and requests a card.
- **Plain bill notice:** no observed page warning signs, with explicit limitations.
- **LumoraFiles:** harmless attachment-download attempt; the decoy cancels it and the card says its contents were not scanned. “Open anyway” is disabled.
- **DemoAccount:** slow page; a failed check becomes inconclusive.

An in-app warning appears when temporary text rules flag examples. Hover/focus/tap a badge for reasons. Concerning check cards show a prominent warning to keep attachments closed and avoid passwords, card details or codes. These components operate inside the demo; they do not monitor other apps or create OS push notifications. Brief highlights respect reduced-motion preferences.

## Setup on another machine

Use Python 3.10+ and Git. Downloads require network access; no global packages are needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$pwd\.playwright"
.\.venv\Scripts\python.exe -m playwright install chromium
New-Item -ItemType Directory -Path starter -Force
```

On Unix use `.venv/bin/python` and `export DEMO_MODE=live`. Activation is optional; the explicit interpreter path works directly. On Windows, optional activation is `.\.venv\Scripts\Activate.ps1`.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Stop any manual server first: tests own port 8000. They include the actual MV3 extension in bundled Chromium, live local checks, replay flows, strict evidence, URL boundaries, blocked requests, popups/frames, worker timeout, mobile layout and warning interactions. The suite includes an intentional slow-page test. If the sandbox's temporary directory is blocked, create `work/tmp` and set `$env:TEMP = "$pwd\work\tmp"; $env:TMP = $env:TEMP`.

## Previous SMS / local Decoy implementation

FastAPI serves plain HTML/CSS/JavaScript and JSON APIs. `triage(text)` returns text clues and check tokens. Risky or uncertain links start background jobs; other links start when their check page opens. Jobs run Playwright's fixed script in a bounded worker process, with up to two concurrent investigations. Cache entries share observed results for an exact URL/mode during this server run. Store locks are released during browser work; reset-generation checks prevent stale jobs restoring cleared state.

The decoy waits for scripted redirects, inspects input metadata and urgency/AI-directed text, fills known fields with the kit's canary values, and submits one form. It records canonical URLs without form-query values, requested fields, submission targets, blocked requests and download attempts. Evidence validation precedes verdict combination. It does not follow instructions written on a page.

See [DEMO_EXPLAINED.md](DEMO_EXPLAINED.md), [PROGRESS.md](PROGRESS.md), and [teammate-build-kit/CONTRACTS.md](teammate-build-kit/CONTRACTS.md).

## Limits and safeguards

- Only HTTP localhost or 127.0.0.1 on port 8000 under `/mock/` can be initial targets. Userinfo, encoded/traversal paths, queries and fragments are rejected for initial URLs.
- Browser requests stay within the local mock paths; the local mock stylesheet is the only static-resource exception. Form queries carry only canaries. Other hosts, ports and API paths are blocked. WebSockets and service workers are blocked.
- A fresh nonpersistent context is used. Only listed fake canary values are filled. Downloads are canceled; attachment contents are not scanned.
- Extra pages/frames are not investigated, so their appearance fails closed. The short observation window may miss delayed or visitor-dependent behavior. This is a constrained local prototype, not an internet-facing browser sandbox.
- The worker has a nine-second watchdog and shorter internal action budget. Queued jobs can take longer to begin; the card times out to inconclusive after waiting.
- Missing, malformed, blocked and failed checks never yield “No warning signs found.” Strong scam text may retain its warning while disclosing incomplete page evidence.
- “Open anyway” requires a completed eligible local verdict on the server and is prohibited for download-attempt results.
- State is process-local. Restart or `GET /api/reset` clears it and invalidates tokens. No database or real-message integration exists.
- `.env`, browser binaries, `.venv` and temporary files are ignored. No keys are needed for the demo. Use `--no-access-log` to avoid logging canary form queries.

## Next steps and project process

Place provided files unchanged in `starter/`, then run `$starter-inspector`. Stage 0 remains deferred. `app/baseline.py` is the replaceable boundary; do not calculate accuracy on placeholder scenarios. Category recovery and the evaluation runner are implemented. Run `.\.venv\Scripts\python.exe -m eval.run_eval --mode replay` for the current report, or use `--mode live` with the local server running. Provided-data metrics remain unavailable until Stage0 inspects and integrates the starter files.

The repository is https://github.com/truncations/T-Defense.git, with its existing MIT license/history retained. GATE approval permits publication. Native Git credentials are unavailable in this session; the connected GitHub account can publish the reviewed source snapshot. Original local stage commits and generated media are preserved on a local stage-history archive branch when aligning the source branch. The reviewed source is now published; the initial verified checkpoint is 0e7bd1178fe75ea298b921f9cabdec8667ef3347. Original local history/media are on local/stage-history-2026-11-07. Publication details are recorded in PROGRESS.md. Project-local rules, seven skills and two reviewer roles continue to govern stage commits; use `$t-defense-stage-runner` to resume.

Screenshots and the current silent walkthrough are generated locally in `demo_backup/`; binary backups are excluded from public source publication. Their own on-screen labels identify live versus recorded replay evidence. Reset demo on `/sms-demo` clears stored checks and issues fresh tokens.

Credits: teammate build kit for the plan/workflow. Sponsor starter files are not yet supplied or integrated. Lumora Wireless is fictional.

Documentation: [Playwright network controls](https://playwright.dev/python/docs/network), [browser contexts](https://playwright.dev/python/docs/api/class-browsercontext), [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/).

## VirusTotal domain reputation and email checks (v0.2)

Place `VIRUSTOTAL_API_KEY=your-key` in the ignored project `.env` file, or set that environment variable. Only this key is read from `.env`; other app settings still use environment variables. The backend reads it on subsequent checks. Never paste the key in chat, the extension or Git. The setup dashboard displays readiness without exposing it.

Reload the unpacked extension in Chrome/Edge after updating its files, then refresh the website tab. Start monitoring, then explicitly enable **VirusTotal domain checks for this tab** in the popup. Opt-in resets when monitoring stops or crosses to another site. Clicking Start again on the same origin retains it. The VirusTotal API key stays in the backend; only its separate pairing code goes into the popup.

Queried public hostnames, including subdomains, are shared with VirusTotal and added to its community dataset. Avoid confidential hostnames. No full URLs, email text, HTML, cookies, typed values or attachments go to VirusTotal. The backend makes fixed domain-report GET requests; the provider may scan queried domains. It does not submit files/URLs or browse the destination itself. Private/reserved hosts and literal IPs are excluded. Reports apply to domains, not exact paths: a compromised page on a reputable host can be missed.

The implementation shares a conservative four-per-minute/500-per-UTC-day budget per backend process and respects provider429 backoff. Account limits remain authoritative, including across restarts/other clients. Each scan considers at most16 domains for requests; remaining domains are explicitly unchecked. The first four uncached eligible domains can run; cached hits do not use quota. A bounded512-entry memory cache keeps reports up to15minutes, errors60seconds. No cache is persisted. Report date and uncertainty are shown. Missing-key, all-timeout, unknown, old, failed and limited checks never establish safety. The public API prohibits commercial use and has other restrictions; consult [VirusTotal terms/limits](https://docs.virustotal.com/reference/public-vs-premium-api) before enabling it for a deployment.

Email collection recognizes currently rendered message bodies (including Gmail-style markup), prioritizes their links before navigation chrome and decodes supported Google /url query wrappers locally. Hover/focus prioritizes a chosen link even beyond the current batch. It does not fetch email through Gmail APIs or read accounts. Markup can change, collapsed messages/frames remain unsupported and the200-element bounded snapshot still applies. Account-action requests in email produce a contextual caution, not a phishing verdict; legitimate email can trigger it.

**Automatic highlights and the findings list** retain evidence through mutation checks. Right-click Inspect selects the associated row. Pending changes remain unconfirmed. Removed/changed nodes leave a clearly historical finding until a requested recheck resolves it, rather than silently losing the evidence. New evidence still comes from current snapshots; retained findings do not prove the current page is malicious.

Use the lab's **Add email-style message** for synthetic wrapper extraction. Its example.invalid destinations are deliberately excluded from external reputation queries. Tests exercise real MV3-to-FastAPI traffic with only VirusTotal's transport mocked; no live provider claim is made without a configured key. This milestone adds domain reputation and email/inspection fixes, not the remaining trained classifier, full redirect/network interception, attachment scanner or complete-frame coverage.

## Version0.3: social-engineering indicators and all findings

The collector now derives14 standardized social indicator IDs from bounded local message text: reward/account bait, reward scarcity, cracks/cheats, requests to weaken security or run supplied commands, ransom-payment demands, guaranteed-return deposits, relationship money pressure, fake-support access requests, private-image extortion, coercive threats, secrecy/isolation, claimed-authority requests, emergency identity/payment pressure and upfront release fees. Python combines these flags with link/form evidence and returns explicit reasons and appropriate next steps. The user-provided Nitro example is tested verbatim, including a link in a separate paragraph. No rule depends on the sample brand/domain or scenario ID.

These are explainable English-pattern combinations, not a trained model. A warning describes what text requests; it does not establish installed ransomware, malicious file bytes, actual grooming, verified impersonation, or voice/video deepfakes. Long-term relationships, images/audio and off-page context are not analyzed. Benign/cautionary cases are regression-tested; false positives and misses remain possible. Raw messages still never leave the page; only validated indicator IDs are added to the snapshot.

Every detected live element gets a numbered yellow highlight with dark/red borders. Matching list entries are scrollable and clicking a row scrolls to the exact source element, including offscreen findings. Highlights track scrolling/resizing without rewriting page element styles. No Show element/Show highlighted/Next finding button remains. Unmarked content is never certified safe. All current marked nodes are listed; coverage remains199 candidates plus the document per scan. Up to50 removed historical rows are retained without retaining their detached DOM nodes.

Background scans use a separate activity line; they do not replace an existing warning count. The ! indicator pulses slowly for new/changed findings until you open/select the list; reduced-motion disables pulsing. Check again explicitly refreshes resolved evidence. Partial scans preserve prior findings outside the batch and unavailable reputation evidence; previous findings are dashed/labeled. Removed nodes can be cleared by an explicit recheck. Navigation/Stop removes the list and highlights. Continue once overrides only one synchronous supported event; failed native form validation cannot leave an override behind.

The live lab adds a reward/account lure and selectable synthetic pressure examples. These use fictional Lumora wording; real service wording is quoted only in test fixtures. Existing VirusTotal domain checks and their opt-in/privacy/coverage limitations remain unchanged. Reload extension v0.3 and refresh the website tab after updating.

## Version0.4: current scopes, continuous monitoring, and local trust

Local detection now recognizes decimal cryptocurrency transfers plus multiplied/immediate returns (the supplied ETH giveaway), commercial email promotion patterns, large linked-image coverage cautions, and supported visible Gmail Spam-folder context. Promotional spam is a separate low-severity category and does not establish fraud or medical legitimacy. No OCR, image-text extraction, sender subscription history or Gmail account API is used. Strong local security findings short-circuit VirusTotal; optional domain reports remain a fallback for otherwise unresolved content, with per-tab consent unchanged.

Start everywhere asks Chrome/Edge for optional HTTP/HTTPS access in a direct toolbar click, then registers a persistent bootstrap and activates current/new supported tabs. Monitoring preference persists locally until Stop everywhere; browser-internal/protected pages and uninspected frames remain unsupported. The local backend must run. Pairing remains browser-session/process-bound, so restarting browser/backend can require pairing again. New origins do not inherit VirusTotal consent. Stop unregisters the bootstrap and removes UI in all tabs; permission revocation stops the mode. Legacy direct per-tab helpers remain only for compatibility/testing.

The default UI is a compact bottom-right dock below top profile controls. Expand it only to review findings. Drag its handle or use arrow keys; position is browser-local, with Reset panel position in the popup. ! uses a centered SVG. Unchanged list/fact nodes are reused, monitoring text stays constant, and changing diagnostic IDs/times are in a closed Check details disclosure. New routes, hidden/removed messages and resolved covered findings clear automatically, superseding v0.3 history retention. Out-of-batch or unavailable current evidence remains explicitly incomplete, not silently safe.

The local trust database uses native IndexedDB, not a Python/cloud database. Select a finding, open the genuine toolbar popup, preview the exact scope, then Trust this exact content. A trusted message includes its descendant links/forms; a selected link within a recognized message scopes to that message. Whole pages and oversized/incomplete identities cannot be permanently trusted. Trust is explicit; no clean scan or zero VirusTotal result auto-whitelists content.

Records contain SHA256 fingerprint, origin, kind and creation time only. Raw text, passwords, field values and full URLs are never stored. Local fingerprints include complete bounded visible text, resolved link/form/submitter destinations, associated external form controls, field metadata/state and labels. Typed values are excluded. Matching content skips backend detection; local metadata is still fingerprinted to detect changes. Changed content/destinations require a fresh check. This is trust of an HTML/content signature, not proof that remote file bytes, scripts or site ownership cannot change. Plain HTTP pages lacking the secure crypto API cannot create trust decisions.

Trust entries persist across reloads/browser restarts in that extension profile until individually revoked or cleared. Browser profile/extension removal deletes them. Keep the same unpacked extension folder/ID when updating. Capacity5000 rejects additional decisions without silently evicting earlier ones. Revoke clears cached bypasses immediately; older async checks cannot reinstall them. Manage entries in the toolbar. Opting into continuous local monitoring never opts into VirusTotal for new sites.
