---
name: starter-inspector
description: Use in Stage 0 or whenever T-Mobile's starter files (synthetic message set, scam taxonomy, baseline classifier in starter/) need to be inspected, run, wrapped or measured. Produces STARTER_FILES_REPORT.md and finalizes CONTRACTS.md.
---

# Inspecting the T-Mobile starter files

The whole plan rests on guesses about these files. Your job is to replace the guesses with facts. **Never invent a fact about them.**

## Rules
- Never modify anything in `starter/`. Copy it if you need to experiment.
- Label every fact in the report **observed** (you saw or ran it) or **guessed**.
- Install starter dependencies only into `.venv`. Ask the human first if one is large (over about 100 MB) or global.

## Steps
1. Inventory: every file with its size and type. Open the readmes first.
2. Message set: format, row count, columns, label values with counts, and how many messages contain a URL (regex `https?://`). Include 5 example rows (synthetic, so it's fine to show them).
3. Taxonomy: every category with its description. Map it to the `category` strings used in `CONTRACTS.md`.
4. Baseline classifier: language, entry point, inputs, outputs (label only, or score/probability?), dependencies, and how long it takes per message.
5. Run the baseline unchanged on the full set. Compute accuracy, and precision, recall and F1 for the scam class, plus a confusion matrix. Save the raw predictions to `eval/baseline_predictions.csv`.
6. Write `STARTER_FILES_REPORT.md` with sections: Inventory, Messages, Taxonomy, Baseline, Baseline results, Wrong assumptions, Recommended changes.
7. Compare with the Assumed rows in `teammate-build-kit/BUILD_OVERVIEW.md` section 10. Then:
   - Update `teammate-build-kit/CONTRACTS.md` (label values, category names, whether `score` can be null) and mark it "finalized after Stage 0".
   - Pick the abstain rule: a gray band on the score if one exists, otherwise disagreement between the baseline and the rules.
   - If messages have no URLs, note that team scenarios provide the Lumora links.

## Wrapping the baseline (for Stage 1)
Wrap it behind a single function in `app/triage.py`. If the classifier isn't Python, call it as a subprocess with a timeout and parse its output. If it needs a GPU or is very slow, stop and tell the human, because the plan assumes it runs on a laptop CPU.
