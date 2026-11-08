---
name: verdict-card-writer
description: Use when writing verdict logic (app/verdict.py), the check page (static/check.html, check.js), the phone UI, or any customer-facing text in T-Defense, such as verdict wording, confidence lines, evidence, unknowns, next steps and recovery checklists. Enforces honest confidence and plain language.
---

# Verdicts and customer-facing copy

Judges score **usability** and **honest confidence**. A stressed person reads this card in 3 seconds.

## Verdict rules (`app/verdict.py`)
| Situation | Verdict |
|---|---|
| Investigation found canaries sent cross-origin, OR 2+ strong signals (credential/card/SSN request plus urgency or a redirect) | `likely_scam` |
| One concerning signal, OR strong triage with a clean page | `suspicious` |
| Investigation completed with **zero** findings AND triage not `likely_scam` | `looks_fine` |
| Investigation missing, pending past 15 s, `failed` or `blocked` | `inconclusive` (keep `likely_scam` if triage alone is strong, and add "page could not be checked" to unknowns) |
| Page contains AI-directed text | Never `looks_fine`; add evidence "The page contained hidden text trying to instruct automated checkers." |

Confidence is `high`, `medium` or `low`, with a one-line reason. Don't show fake-precise percentages to users.

## Card layout (top to bottom)
1. Verdict word, large and colored: **Likely scam** (red), **Suspicious** (amber), **No warning signs found** (green, never "Safe"), **We couldn't check this** (grey).
2. Confidence line: "We're fairly sure because ..."
3. "What happened when our decoy opened it": at most 3 lines.
4. "What we couldn't check": always present, at least 1 line.
5. Next steps: at most 3, each starting with a verb.
6. Buttons: "Go back (recommended)" (primary), "Open anyway" (only for Suspicious and No warning signs found), "I already entered my info".

## Writing rules
- Reading level of about grade 6. Sentences under 15 words. Talk to the user as "you".
- Say what happened, not jargon: "sent your card number to a different website", not "cross-origin exfiltration".
- Never say "safe", "guaranteed" or "100%".
- Never tell users to call a number or visit a link from the message. Say "the number on your bill or card".
- Report action: "Forward the text to 7726 (SPAM)."
- Recovery text comes from `teammate-build-kit/MOCK_SITES_SPEC.md` → Recovery.

## Visual rules
- Phone frame about 380px wide, base font 18px or larger, high contrast, readable from 2 meters during the demo.
- Color is never the only signal; always include the verdict word.
- Pending state: "Our decoy is checking this link..." with a simple spinner.
