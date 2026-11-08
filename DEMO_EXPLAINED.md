# Current demo: browser Page Guard

The primary demo is now the actual Chrome/Edge extension. Open the root dashboard, load the unpacked extension, pair with the backend and activate monitoring on a website. The extension observes DOM changes and periodically sends structural signals to `/api/page/assess`. Python applies explicit rules and returns warning evidence and next steps. No recorded verdict drives this flow.

Use `/extension-lab` for repeatable synthetic risks. Add a message, sensitive form or attachment: the on-page pink warning expands without changing tabs. Hover a flagged element, use Show element, or try its link/form to see the review pause. The lab independently cancels outbound actions even after Continue once. The dashboard count and overlay scan ID/time demonstrate actual backend work. You can activate the same extension on a regular public website yourself; it may produce no warning if no rule matches.

This is structural risk detection, not comprehensive phishing detection. The sponsor classifier is still missing. No accuracy metrics are claimed. No typed values or raw messages are sent, and the backend does not browse real sites. Permission is per activated origin. See README and extension/README for installation and limits.

---

The following describes the previous SMS concept, now at `/sms-demo`.

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
