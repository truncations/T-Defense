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
