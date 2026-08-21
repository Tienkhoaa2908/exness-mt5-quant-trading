# V39 Selective Harvest — Stage A result

Ngày chốt evidence: 2026-08-21.

## Bundle integrity

Accepted uploaded ZIP SHA-256:

`27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`

Bundle CRC PASS. `bundle_manifest_sha256.txt` có 9 entries và toàn bộ hash nội bộ PASS.

Evidence head:

`399a8dede123da525fec6d5242ca78e6f33cf085`

Branch:

`agent/v39-selective-harvest`

Accepted V38 evidence SHA được bundle xác nhận:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

V38 control coverage trong V39: 563/563 trades, 129,311 filtered M1 rows, 29,514 +1R-zone rows, 283 +1R-zone trades.

V36 predictions SHA trong run:

`a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`

V36 Transformer recomputation reproduced the accepted diagnostic almost exactly:

- future-delta Spearman: 0.0402942362;
- final-R Spearman: 0.5148120045;
- Hold AUC: 0.6756834959;
- Protect AUC: 0.6770656378;
- Hold/Protect AUC >0.5 in 6/6 months.

This confirms the V36 recovery path is reproducible; the V39 HOLD is not explained by a failed V36 recomputation.

## Preregistered Stage-A result

Primary lane: `fusion_v36_m1`.

Final status: **STAGE_A_HOLD**.

| Gate | Observed | Requirement | Result |
|---|---:|---:|---|
| folds | 6 | >=4 | PASS |
| first triggers | 17 | >=30 | FAIL |
| coverage | 14.655% | 3%-35% | PASS |
| positive avoided-giveback months | 3/6 | >=5/6 (75%, min 3) | FAIL |
| mean monthly avoided giveback | +0.120864R | >0 | PASS |
| mean monthly false-big-winner rate | 32.0% | <=20% | FAIL |

No discretionary threshold/model sweep is allowed to convert this HOLD into a PASS.

The `m1_only` lane is also HOLD: 7 folds, 59 triggers, 38.31% coverage, only 2 positive avoided-giveback months, mean monthly avoided giveback -0.14491R, false-big-winner rate 39.72%.

## Additional diagnostics

The preregistered monthly-average metric is positive for fusion, but the 17-trigger pooled mean is still slightly negative (`trigger_r - final_r = -0.04524R`) and pooled false-big-winner rate is 41.18%. This is not a replacement gate; it is a warning that the apparent monthly mean improvement is not broad-based.

Fusion monthly avoided giveback:

- 2026-02: +0.9231R, 2 triggers;
- 2026-03: +0.4012R, 1 trigger;
- 2026-04: 0 triggers;
- 2026-05: +0.1045R, 6 triggers;
- 2026-06: -0.5850R, 5 triggers;
- 2026-07: -0.2395R, 3 triggers.

The failure becomes concentrated in June-July, when giveback AUC falls below 0.5 while tail AUC remains only moderate.

Fusion trigger concentration is also narrow:

- SLOW_MOM: 9/17 triggers;
- EMA: 7/17;
- MACD: 1/17;
- SHORT: 12/17; LONG: 5/17.

This sample is too small to justify a source- or direction-specific production gate. Do not convert these diagnostics into source filters on the same sample.

## Root-cause interpretation

V39 predicts eventual giveback and future maximum as separate labels. Several rejected trigger examples were eventually giveback-prone but first extended substantially to the right tail. That means the label does not directly answer the action question: **which event happens first from the current mark — a protective giveback boundary or a tail-extension boundary?**

The largest false-big-winner misses have low predicted tail probability / low V36 `p_hold` despite subsequent +0.75R-or-more extension. This is evidence that threshold tightening alone is not the correct repair.

## Decision

- V39 Stage A: HOLD / do not promote to exact-MT5 Stage B.
- Baseline control: KEEP.
- V36 Transformer: KEEP as reproducible sequence-state evidence.
- V38 universal fast exits: remain REJECTED.
- Do not tune V39 `p_hold`, score quantile, source filters or risk to force a PASS.
- Next research should change the target formulation, not merely the threshold: model first-passage / competing-risk event ordering from the +1R state.

This result is diagnostic only and is not an exact-MT5 PnL claim. REAL-MONEY LIVE TRADING remains FORBIDDEN and stop-risk research ceiling remains <=1.00%.
