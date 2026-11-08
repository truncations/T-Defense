# T-Defense 0.5.2 local update — November 8, 2026

## 0.5.2 link sensitivity correction
- A bare link such as https://www.paypal.ai/scam now gets a medium review warning: it uses a PayPal-like hostname outside the recognized PayPal domains. This is a warning sign, not proof the destination is malicious.
- Exact recognized PayPal domains/subdomains do not trigger this new rule; other evidence still applies. No blanket marketplace exemptions or broad suspicious-TLD/path rules were added.
- Link paths, raw messages, and listing labels are not sent to the local service. Existing Mercari sold-out/price and GitHub filename fixes remain unchanged.
- Restart the Python application as well as reloading the extension and refreshing monitored tabs. This narrow rule does not cover every brand or spelling variation.
- 74 targeted regressions passed, including the genuine extension warning/list/click pause and benign Mercari/GitHub controls; targeted Ruff checks passed. No real destination was visited.

## 0.5.1 corrections
- Automatic connection reuses a valid existing connection. Otherwise it opens local setup for the one-time installation approval, then retry Connect automatically. Approval never starts monitoring.
- Local setup refreshes its session after backend restart.
- Versioned scanner/page runtimes dispose and replace outdated monitors on extension reload. A new Python server alone cannot install updated browser code.
- Nonzero counts stay yellow/magenta and pulse every 1.5 seconds (static with reduced motion); the close button has a 44px target.
- Trust initiation acts on the selected finding beside Check again/Pause everywhere. Final permanent trust still requires the genuine popup.
- 37 targeted native regressions passed. Windows/long-stream checks and three legacy shutdown errors remain unresolved.

## This update
- Every fresh page starts bottom right; vertical movement is document-local and never follows other tabs. Same-page navigation resets it too.
- A compact ! count and arrow opens a sliding right-side findings drawer. Routine checking no longer occupies the collapsed control. Existing concerning clicks/submissions pause for review and open the drawer.
- The genuine popup retains up to 200 standardized evidence rows per active document for backup if on-page controls fail. Previous/out-of-batch evidence is labeled; no raw message labels or typed values are stored. Page tampering can still interfere with detection; this is not a safety guarantee.
- Automatic pairing: choose Connect automatically or Start everywhere, approve the matching installation ID once in local setup, then press Start. Approved IDs persist in ignored work/approved_extensions.json; credentials remain process/session scoped. Reconnects never enable stopped monitoring. Revoke from local setup. Manual pairing remains an optional fallback.
- Conversation preparation is documented in CONVERSATION_PREPARATION.md; no transcript capture, history storage, cloud processing, or conversation-level analysis is enabled.

## Verification
- Full native suite: 173 assertions passed; three pre-existing legacy investigator shutdown errors remain (not a clean full-suite result).
- New native flows verified on synthetic pages: independent positions/reload resets, local setup approval without code entry, popup evidence with removed page control, drawer desktop/mobile, guarded click/submission, Stop during pairing, trust security, backend credential rotation and revocation.
- Ruff checks passed. Sandbox dependencies match available tools, not the future pinned requirements; requirements.txt is unchanged.
- Windows installation, extended YouTube playback and ten-hour memory/performance remain unverified.

## Apply safely
Back up your existing folder and merge this source update, preserving .env, work/, existing dependencies, local settings and repository history. Reload the same extension folder/ID, restart the Python application, and refresh monitored tabs. Open local setup for the one-time installation approval; matching the ID in the genuine toolbar is essential. No files were applied directly to your Windows folder or pushed to GitHub.

## Changed source areas
extension/content.js, background.js, popup.js/html/css, manifest.json, README.md; app/page_guard.py; static/extension.html and extension-setup.js; new/updated regression tests; CONTRACTS.md, CONVERSATION_PREPARATION.md, PROGRESS.md and these notes. Earlier bounded-scanner and filename/price false-positive fixes remain included.
