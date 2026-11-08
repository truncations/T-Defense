# T-Defense evaluation status

Date: 2026-11-07T18:50:53-06:00 (Central standard time). Commit: d3add0e.

## Provided baseline and T-Defense on provided data

Provided baseline: unavailable. T-Defense-on-provided-data: unavailable.

Starter files and the real classifier have not been integrated. No accuracy, precision, recall, F1, confusion matrix, or abstention metrics are reported on placeholder data.

## Our own demo pages — not T-Mobile data, not an accuracy claim

The table checks expected prototype behavior on fictional pages. It is not message-classifier accuracy.

| Page | Expected | Observed | Evidence mode | Status |
|---|---|---|---|---|
| verify | likely_scam | likely_scam | live local browser | done |
| reward | likely_scam | likely_scam | live local browser | done |
| bill | looks_fine | looks_fine | live local browser | done |
| track | likely_scam | likely_scam | live local browser | done |
| help | likely_scam | likely_scam | live local browser | done |
| fee | suspicious | suspicious | live local browser | done |
| attachment | suspicious | suspicious | live local browser | done |

Attachment contents were not scanned. Real SMS integration, real-site coverage and sponsor metrics are not established by this table.

## Next action

Run starter-inspector when provided files arrive; inspect/normalize their real schema and integrate the baseline before reporting sponsor-set metrics. Mark tuned=true when rules/thresholds were changed using provided data; score only the held-out30%.
