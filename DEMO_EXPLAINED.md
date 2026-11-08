# What T-Defense does now

The phone is a simulated SMS inbox, not your real messages. Choose Obvious scam, Hidden risk, or Plain bill notice. Hover/focus/tap a badge for text reasons. Follow the check link to see page evidence and limits.

## Working backend

- FastAPI/Uvicorn serves the app and APIs on one loopback server.
- GET /api/scenarios loads 12 source=placeholder messages; POST /api/assess calls temporary triage rules, creates random link tokens and hashes, and schedules concerning links.
- POST /api/links/{id}/investigate starts or reuses a bounded job. Live jobs run a fixed Playwright script in a fresh context on local fictional pages only. Up to two run at once; results are cached in memory by exact URL/mode.
- The decoy observes redirects, sensitive fields, form targets, urgency, hidden checker-directed text and download attempts. It fills only the kit's fake canary values, submits once and cancels downloads.
- Strict completed-evidence validation rejects incomplete results. The verdict combines text/page signals into likely scam, suspicious, no warning signs found, or inconclusive.
- Page cards prominently warn against attachments and sharing passwords, payment details or codes. Download results cannot use Open anyway. Attachments are not opened or scanned.
- Store reset/restart clears tokens/cache and prevents old jobs restoring cleared state. Health/UI API calls remain responsive during slow browser checks.

## Live versus replay

LIVE DECOY CHECK means a local browser investigation completed now. RECORDED REPLAY means evidence captured from a prior local run is being reused, without revisiting the page. Any hand-written fixture retains a SIMULATED REPLAY label. The historical GATE video shows the earlier replay UI.

## Still pending

The provided classifier, message set and taxonomy are not present. Text scores remain null, categories provisional, and no accuracy numbers are calculated on placeholders. Stage0 waits for starter-inspector. Category recovery and an evaluation runner are implemented; actual sponsor-data evaluation remains deferred. The recovery button shows independent-contact, password, two-step/PIN and reporting steps, plus category-specific advice. Real SMS/app integration and real-website investigations are outside this prototype.

## Honest boundaries

Only local demo URLs are investigated. Other hosts, ports and API paths are blocked. WebSockets and service workers are blocked; extra popup/frame content fails closed. A short fixed script cannot establish that a real site is trustworthy or detect every delayed behavior. Confidence wording reflects rules and observed evidence, not calibrated model certainty.

The user approved the replay GATE and continued building. The reviewed source is published at https://github.com/truncations/T-Defense. Native terminal Git credentials remain unavailable in this session; publication used the authenticated GitHub connection. Original local stage commits and generated media are preserved on local/stage-history-2026-11-07.
