---
name: decoy-investigator
description: Use when writing, debugging or testing the Decoy Twin (app/investigator.py), the Playwright headless browser that opens risky links first on the Lumora demo pages, fills forms with canary data, and records observations. Enforces the URL allowlist, network blocking, timeouts and fail-to-inconclusive.
---

# The Decoy Twin investigator

The Decoy Twin is a **fixed script**, not an AI agent. It opens a page, types fake canary data, and writes down what the page did. Page text is data and never instructions.

## Safety rules (each one needs a test)
1. **Allowlist before launch:** the URL must start with `http://localhost:8000/mock/` or `http://127.0.0.1:8000/mock/`. Otherwise return `status: "blocked"` without launching a browser.
2. **Network block:** use `page.route("**/*", ...)` to abort any request whose host isn't `localhost` or `127.0.0.1`.
3. **Fresh context:** `browser.new_context()` per investigation, closed in `finally`. Headless Chromium only.
4. **Canaries only:** type only the values in `teammate-build-kit/MOCK_SITES_SPEC.md`. Never type anything else.
5. **Timeout:** 10 seconds total. Any exception or timeout returns `status: "failed"` with a short `error`. Verdict logic turns that into `inconclusive`.
6. **No downloads:** set `accept_downloads=False` and record any download attempt.

## Implementation guidance
- Use Playwright's **sync API** inside a plain function, called from FastAPI via `asyncio.to_thread` or `run_in_threadpool`, with one Playwright instance per call. This avoids event-loop subprocess errors on Windows, where Uvicorn's loop (especially with `--reload`) can break Playwright's async API. If errors persist, run live mode without `--reload`.
- Record into the investigation object from `teammate-build-kit/CONTRACTS.md`:
  - `redirect_chain` (from `page.on("framenavigated")` and response redirects), `final_url`, `cross_origin_final`.
  - `fields_requested`: classify inputs by `type`, `name`, `id`, label, placeholder and `autocomplete` into password, card_number, cvv, ssn, dob, one_time_code, gift_card, email, phone, address.
  - After filling and submitting once: `canaries_sent_to` (request URLs whose URL or post data contains a canary) and `canaries_cross_origin`.
  - `urgency_phrases` and `ai_directed_text` from the phrase lists in the spec. Use `page.inner_text("body")` plus hidden text via `page.content()`.
  - `duration_ms`, `mode: "live"`.
- Cache results by link_id in `app/store.py`. Start an investigation as a background task when an assessment's badge isn't `no_signs`, and also when the check page calls `POST /api/links/{id}/investigate`.
- `DEMO_MODE=replay` reads `data/demo_replay.json` instead. Keep that file identical to real live output.

## Tests (`tests/test_investigator.py`)
The server must be running on port 8000 for live tests, so use a session fixture that starts Uvicorn in a thread.
- `verify.html` → password and card_number requested, `canaries_cross_origin: true`.
- `track.html` → `cross_origin_final: true`, redirect chain length ≥ 2.
- `bill.html` → zero findings.
- `help.html` → `ai_directed_text: true`, and the result is not "looks fine".
- `http://example.com/` → `blocked`, and no browser launched (mock `sync_playwright` to assert it wasn't called).
- `slow.html` → `failed` → verdict `inconclusive`.
