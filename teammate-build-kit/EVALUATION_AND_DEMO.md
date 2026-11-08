# EVALUATION_AND_DEMO

## Part 1: What to measure, and why

Judges score "detection accuracy". Honest numbers beat big numbers, so we keep three groups **separate** and never mix them.

### Group 1: Provided baseline, as-is (do this first, in Stage 0)
Run T-Mobile's classifier unchanged on their full message set. This is the bar we compare against.

### Group 2: T-Defense triage on the provided data
Baseline + taxonomy + our rules + abstain. If we tuned anything, tune on a 70% split (seed 42) and report on the other 30% only. Otherwise we'd be grading our own homework.

### Group 3: Decoy Twin on our mock pages
The 5 Lumora pages, expected vs observed verdict. **Label it clearly: "our own demo pages, not T-Mobile data."** It shows the behavior layer works. It is not an accuracy claim.

### Numbers to report (in `eval/results.md`)
| Metric | Plain meaning | Groups |
|---|---|---|
| Accuracy | Share of messages labeled correctly | 1, 2 |
| Precision (scam) | Of messages we called scams, how many really were | 1, 2 |
| Recall (scam) | Of real scams, how many we caught | 1, 2 |
| F1 (scam) | One number balancing precision and recall | 1, 2 |
| Confusion matrix | Table of right and wrong by class | 1, 2 |
| **Abstain rate** | Share of messages we marked "not sure" | 2 |
| Accuracy when not abstaining | How good we are when we do commit | 2 |
| Expected vs observed verdict | Did the decoy see what the page does? | 3 |

**Slide line template (fill in from `eval/results.md`):** "On T-Mobile's synthetic set, the baseline caught X% of scams. T-Defense caught Y% while saying 'not sure' on Z% of messages instead of guessing. On our own demo pages, the Decoy Twin matched the expected verdict on N of 5." If Y is lower than X, say so and explain the trade-off (fewer false alarms, or honest abstaining). Judges reward honesty.

If the starter set has **no labels**, report only agreement with the baseline and the abstain rate, and say so.

---

## Part 2: Three-minute demo script

Setup before judges arrive: server running in **live** mode, phone open at `http://localhost:8000/`, the check page tested once, and a backup terminal ready with the replay command. Hit "Demo reset".

| Time | Show | Say (short) |
|---|---|---|
| 0:00–0:20 | Title slide | "Scam texts work because we tap first. T-Defense is protection inside your messaging app. Nothing to install, nothing to turn on." |
| 0:20–0:50 | **A.** Phone: "Lumora: line suspended today" has a red badge. Tap it → card: Likely scam, with evidence | "Every message gets scored with T-Mobile's baseline and taxonomy. This one is obvious, and the card says why and what to do." |
| 0:50–1:40 | **B.** "Your order shipped, track it" has an amber or grey badge, because the text alone looks harmless. Tap it → "Our decoy is checking..." → card: the page redirected to a different site and asked for a card number | "**Here's the twist. Something already fell for it, so you don't have to.** Our Decoy Twin, a fake customer with fake data, opened the link first in a sealed browser and caught the page sending its card number somewhere else." |
| 1:40–2:00 | **C.** Lumora "bill ready" → "No warning signs found" plus "What we couldn't check" | "We never say 'safe'. We say what we checked and what we couldn't." |
| 2:00–2:20 | **D.** On card A, tap "I already entered my info" → recovery checklist | "If you already fell for it, here are your next three steps." |
| 2:20–2:50 | Accuracy slide from `eval/results.md`, plus the privacy checklist | Baseline vs T-Defense, the abstain rate, mock pages kept separate. "The decoy only visits our own demo pages. Link IDs, not URLs. Failure means 'inconclusive', never 'safe'." |
| 2:50–3:00 | Close | "Honest about what we know, decisive about what to do next." |

**Honesty lines to have ready if asked:**
- "Can a carrier read my messages?" → "No. Encrypted chats can't be read. T-Defense runs inside the messaging app you opt into. This demo is a mock of that app."
- "Will this catch every scam site?" → "No. Real scam pages can act differently for automated visitors, which is why a clean result says 'no warning signs found', not 'safe'."
- "Did you test on real scam sites?" → "No, on purpose. We rebuilt common scam behaviors on our own fictional-brand pages."

## Part 3: Fallbacks

| What breaks | Do this | Time |
|---|---|---|
| Wi-Fi | Nothing to do; the whole demo runs on `localhost` | 0 s |
| Live decoy slow or crashing | Stop the server and restart in replay mode (`AGENTS.md` → Commands). Say "This is a recorded decoy run from earlier today" | 20 s |
| Port 8000 busy | Close the other server window, or reboot the terminal. Don't change ports: the mock links and allowlist use 8000 | 30 s |
| App won't start at all | Play the `demo_backup/` screen recording and narrate the same script | 10 s |
| Laptop dies | The planner has `demo_backup/` and the slides on their own device | — |

Rehearse once in replay mode on purpose, so switching modes doesn't feel scary on stage.
