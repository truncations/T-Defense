# T-Defense Page Guard

Chrome/Edge ManifestV3 developer extension. Requires the local Python backend at http://127.0.0.1:8000.

1. Extract the ZIP. Open chrome://extensions or edge://extensions, enable Developer mode, then Load unpacked. Select the folder containing manifest.json.
2. Open http://127.0.0.1:8000 and copy the current pairing code. Paste it into the extension popup and click Pair backend. Pairing is held in browser-session memory and expires when the backend or browser restarts.
3. Visit a normal HTTP/HTTPS website, click the T-Defense toolbar icon and Start monitoring this page. activeTab gives temporary access after this user action; no broad all-sites permission is requested.
4. Checks run about every 8 seconds while visible, after DOM changes, on manual checks and around concerning interactions. A pink overlay and independent toolbar count show findings. Hover a flagged element for reasons. Known concerning clicks/submissions can be paused; Continue once is an explicit override.
5. Stop/Pause removes monitoring and the overlay. Same-origin reloads can be reinjected while permission remains; moving to a different site requires activating again. Browser-internal/protected pages are unsupported.

Use the live test lab at /extension-lab to add synthetic messages, forms and attachment links and watch real backend scan IDs change. The lab separately prevents outbound navigation/submission, even after an override.

Privacy: structural flags and origins go only to the fixed loopback backend. No page HTML, message text, passwords, typed/input values, cookies or full query strings are sent. The backend does not fetch real URLs, fill real forms or store page snapshots. Pairing codes never enter content scripts. The manifest's loopback host permission supports the backend; website inspection relies on user-invoked activeTab.

Limits: rule-based indicators are not proof of phishing. Legitimate logins/downloads can trigger warnings. Scans are bounded; embedded frames, closed shadow trees and attachment contents are not inspected. Programmatic navigation/form.submit, earlier page event handlers, middle/context-menu clicks and unsupported frames may evade action interception. Background-tab throttling can delay checks. A hostile page can interfere with an injected overlay, so also check the genuine extension popup/toolbar badge. This is an unpacked prototype, not a store-reviewed production security product.

## Version0.2 update

Reload this unpacked extension, then refresh each website tab so old injected code is replaced. Start monitoring before enabling the VirusTotal checkbox. Configure VIRUSTOTAL_API_KEY only in the backend project's ignored .env or environment. The setup dashboard reports whether it is configured. Pairing code and provider API key are different; never put the provider key in this popup.

Domain reports require explicit opt-in per monitored origin. Queried public hostnames (including subdomains) are shared with VirusTotal and added to its community dataset; avoid confidential hostnames. No full links, messages, HTML or input values are sent. Four requests/minute and500/day are budgeted per backend process; quota/missing/old/failed reports stay incomplete. No reported detections does not establish safety of an exact URL. Consult provider usage terms before deploying commercially.

Rendered email links now take priority over page navigation, and supported Google query wrappers are decoded locally. Hover/focus checks the chosen link. Up to199 candidates plus the page itself fit each snapshot; other content remains partial. No Gmail account/API access is used. Show element/right-click Inspect pins a finding through rechecks; removed elements are clearly labeled historical until closed.
