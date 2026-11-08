---
name: eval-reporter
description: Use when measuring T-Defense's detection accuracy, writing eval/run_eval.py or eval/results.md, or producing numbers for slides. Keeps baseline, T-Defense-on-provided-data and mock-page results strictly separate and reports the abstain rate honestly.
---

# Evaluation and reporting

Spec: `teammate-build-kit/EVALUATION_AND_DEMO.md` Part 1.

## Three groups, never mixed
1. **Baseline as-is** on T-Mobile's full message set (reuse `eval/baseline_predictions.csv` from Stage 0 if present).
2. **T-Defense triage** on the same data. If any threshold or rule was tuned, use a fixed 70/30 split (`random.seed(42)`), tune on 70% only, and report on the 30% test split. Also report the baseline on that same 30% so the comparison is fair.
3. **Decoy Twin on mock pages**: expected vs observed verdict for the 5 Lumora pages. The heading must say "Our own demo pages — not T-Mobile data, not an accuracy claim."

## Metrics
For groups 1–2: accuracy; precision, recall and F1 for the scam class; confusion matrix; and for group 2, abstain rate and accuracy on non-abstained messages. Use only the standard library or the packages already installed. Add scikit-learn only if it's already in `.venv`, and ask before installing it.

## Output: `eval/results.md`
- Date, git commit hash, and mode (live or replay) for group 3.
- One table per group, plus the filled-in slide sentence from the spec.
- If T-Defense scores lower than the baseline on any metric, say so plainly and give the reason (for example, it abstains instead of guessing).
- If the starter set has no labels, report agreement with the baseline and the abstain rate only, and say why.

## Command
`python -m eval.run_eval` must run end to end in under 2 minutes. Add `--sample 20` for a quick smoke test, which is used by `tests/test_eval.py`.
