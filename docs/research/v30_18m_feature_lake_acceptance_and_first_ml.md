# V30 18-month feature-lake acceptance + first causal ML benchmark

Date: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

V30 was tester-only data/ML research. Current project-wide policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V30's zero broker-order/tester-only markers describe that historical runtime. They are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Runtime acceptance

Uploaded Git Bash result ZIP SHA-256:
`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`.

The final Git Bash run compiled `MlDlFeatureLakeV1.mq5` with `0 errors, 0 warnings`, then completed and collected the remaining six-month chunks. Both manifests report tester-only, zero native/external broker orders, 12 candidates, 4 books, V30 bar-feature schema, and no future labels in the EA.

## Canonical 18-month lake QA

After canonical trim/stitch:
- 35,344 M15 feature rows;
- 136 raw V30 feature columns;
- coverage 2025-02 through 2026-07;
- unique timestamps, no duplicates;
- 0 NaN / 0 Inf;
- 864 summary rows;
- 28,128 trade-ledger rows across all books, 7,483 in `norm10k_r0p5_continuous`;
- summary-versus-ledger reconciliation passed within CSV rounding.

Constant/non-informative fields were excluded from model training.

## Adaptive-state continuity

State checkpoints were internally continuous. Replaying control-trade `r_multiple` through the documented EWMA equations reproduced observation counts exactly; small EWMA-value differences were attributable to rounded trade-CSV R values versus higher-precision internal updates.

## 18-month strategy evidence

Strong aggregate historical candidates included `adaptive_ewma_hl8_thr0`, `router_ema_bos8`, and `ema_h1_skip20`. These figures were research-book evidence rather than deployment promotion evidence.

## Critical offline leakage finding

A naive trade-entry join using `bar_features.time <= entry_time` was invalid because a row stamped with a just-closed bar's open timestamp was only available on the first tick of the next bar.

Correct offline availability is:
`feature_available_time = bar_features.time + 15 minutes`.

Trade entries must join to the latest row with `feature_available_time <= entry_time`.

The initial same-timestamp ML experiment was invalidated and must not be cited.

## First corrected causal expected-R benchmark

Corrected causal benchmarks found win/loss classification too weak for promotion. Expected-R regression showed a more interesting but still fragile filtering signal under chronological walk-forward validation.

The result motivated low-dimensional state-change features and stronger nonlinear/sequence controls, while retaining strict causal availability and no test-month threshold peeking.

## Decision

- V30 18-month feature lake: ACCEPTED for offline research.
- Runtime automation: ACCEPTED for the data-acquisition task.
- Win/loss classifier: REJECT for promotion.
- Linear expected-R filter: PROMISING RESEARCH LEAD, not promotion-ready at V30.
- Any ML/DL experiment using raw `bar_features.time` without the +15-minute availability shift: INVALID.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence, not by the historical V30 tester-only markers.
