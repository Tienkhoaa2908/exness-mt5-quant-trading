# V30 family-threshold expected-R gate V2

Date: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

This checkpoint was offline/tester-only research. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Its tester-only execution scope was phase-specific, not a permanent prohibition on researching or preparing production/live trading with real capital.

## Why this gate exists

The strict V30 ML/DL tournament found that unweighted catalog-level ExtraTrees uplift was materially amplified by repeated `(entry_time, direction)` opportunities. A weaker signal survived inverse-opportunity weighting, while unique-opportunity common-state models failed the robustness gate.

This follow-up asks whether the weighted shared expected-R model can be calibrated at the strategy-family level rather than forcing one threshold across heterogeneous families. It is the same 12-month OOS sample and therefore a robustness/diagnostic step, not fresh confirmation.

## Protocol

1. six-month warm-up;
2. previous month is score-calibration month;
3. training labels only from trades with `exit_time < calibration_month_start`;
4. inverse `(entry_time, direction)` multiplicity weighting;
5. frozen ExtraTrees expected-R model;
6. family-specific threshold from previous-month scores only, with global fallback for small family calibration counts;
7. absolute threshold applied to next month;
8. no test-month quantile peeking.

Keep targets tested: 40%, 50%, 60%. Candidate-aware and candidate-blind variants were compared.

## Findings

Candidate-aware family thresholding improved the weighted aggregate at several keep targets, while candidate-blind intervals crossed zero. This indicated the stronger signal was not a universal market-state effect and depended partly on candidate/family-specific context.

EMA pullback was the cleanest lead; adaptive router was a secondary lead at tighter threshold. Router/slow-momentum were not robust enough, MACD had insufficient sample/stability, and BOS/FVG/Trend20 did not clear a family gate.

## Interpretation

The evidence supports a narrower hypothesis: engineered market + adaptive expert state contains some expected-R information useful in interaction with particular strategy-family/candidate context. More slicing of the same OOS months would increase overfitting risk.

## Decision

- Family-specific gate: PROMISING BUT NOT CONFIRMED.
- EMA pullback: strongest lead, not promotion-ready at V30.
- Adaptive router: secondary lead.
- No universal ML filter or DL model is promoted.
- Next meaningful evidence must be genuinely fresh chronological holdout data.

Current production/live research/deployment target is governed by ADR-049 and later V49 evidence, not by this historical tester-only checkpoint.
