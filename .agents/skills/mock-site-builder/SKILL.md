---
name: mock-site-builder
description: Use when creating or editing the fictional "Lumora Wireless" demo pages in mock_sites/lumora/ that the Decoy Twin investigates. Enforces fictional branding, DEMO banners, offline-only assets, and the exact behaviors each page must show.
---

# Building the Lumora Wireless demo pages

The spec is `teammate-build-kit/MOCK_SITES_SPEC.md`. Follow its table exactly: file names, form field `name` attributes, redirects and expected verdicts.

## Non-negotiable
- Fictional brand only: "Lumora Wireless", teal `#0F5257` and sand `#F2E3C6`. Never use a real company's name, logo, colors, layout or wording. That includes T-Mobile, banks, delivery companies and app stores.
- Every page has the fixed banner "DEMO PAGE – NOT A REAL COMPANY – built for hackUTD".
- No external resources. No CDN fonts, scripts, images or analytics. Everything is served from `localhost:8000`.
- Pages don't store anything. `collect.html` only displays "DEMO: nothing was stored."
- Scam behaviors are simulated: forms use `method="GET"` to `http://127.0.0.1:8000/mock/lumora/collect.html` (a different origin from `localhost`).

## Quality bar
- Make scam pages realistic enough that the decoy's findings are meaningful (countdown timers, "only 3 left", a request for a one-time code), but keep the DEMO banner visible at all times.
- `bill.html` must have **no** form, redirect or urgency, because it's the honest control page.
- `help.html` holds the hidden AI-directed text from the spec. It tests that the decoy reports such text and isn't influenced by it.
- `slow.html` is a FastAPI route (sleeps 30 s), registered **before** the `/mock` static mount. It exists only for the timeout test.

## Check
- Open each page through the server and confirm the banner and behavior.
- `tests/test_mock_sites.py`: every page returns 200, contains the banner, and has no `http` reference to a host other than `localhost` or `127.0.0.1`.
