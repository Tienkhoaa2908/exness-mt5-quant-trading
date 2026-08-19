# V30 family-threshold expected-R gate V2

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: offline/tester-only research. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Why this gate exists

The strict V30 ML/DL tournament found that unweighted catalog-level ExtraTrees uplift was materially amplified by repeated `(entry_time, direction)` opportunities. A weaker signal survived inverse-opportunity weighting, while unique-opportunity common-state models failed the robustness gate.

This follow-up asks a narrower question: can the weighted shared expected-R model be calibrated at the **strategy-family level** rather than forcing one score threshold across heterogeneous families?

This is still the same 12-month OOS sample already inspected in prior research. Therefore this gate is a robustness/diagnostic step, not a fresh confirmation sample.

## Protocol

The core monthly chronology is unchanged:

1. six-month warm-up;
2. previous month is score-calibration month;
3. training labels only from trades with `exit_time < calibration_month_start`;
4. inverse `(entry_time, direction)` multiplicity sample weighting;
5. frozen ExtraTrees expected-R model;
6. family-specific threshold derived from previous-month **scores only**, with a global fallback when family calibration count is below 20;
7. absolute threshold applied to the next month;
8. no test-month quantile peeking.

Keep targets tested: 40%, 50%, 60%.

Two feature-identity variants were run:

- candidate-aware: candidate one-hot appended to the engineered causal state;
- candidate-blind: no candidate identity.

## Aggregate family-threshold results

### Candidate-aware

| Keep target | Actual coverage | Selected AvgR | SumR retention | Positive selected months | Worst selected month AvgR | 95% paired-month uplift CI |
|---|---:|---:|---:|---:|---:|---:|
| 40% | 50.14% | 0.2758R | 73.14% | 8/12 | -0.2841R | [+0.0169R, +0.1640R] |
| 50% | 58.86% | 0.2523R | 78.56% | 8/12 | -0.2743R | [+0.0005R, +0.1188R] |
| 60% | 64.49% | 0.2397R | 81.76% | 9/12 | -0.2375R | [+0.0086R, +0.1054R] |

Family-score calibration improves the weighted 40%-target aggregate relative to the global weighted threshold, whose paired-month interval crossed zero.

### Candidate-blind

| Keep target | Actual coverage | Selected AvgR | SumR retention | 95% paired-month uplift CI |
|---|---:|---:|---:|---:|
| 40% | 47.57% | 0.2531R | 63.69% | [-0.0175R, +0.1911R] |
| 50% | 56.89% | 0.2457R | 73.93% | [-0.0182R, +0.1487R] |
| 60% | 63.96% | 0.2222R | 75.16% | [-0.0259R, +0.0820R] |

All candidate-blind intervals cross zero. Thus the stronger family-threshold result is not a clean universal market-state effect; it depends at least partly on candidate/family-specific context.

This is consistent with the unique-opportunity control from the previous tournament, which also failed to establish a universal common-opportunity model.

## Candidate-aware family diagnostics

### EMA pullback family

This is the cleanest current lead.

- 409 OOS trades.
- 40%-target: 46.45% actual coverage, selected AvgR 0.2724R vs 0.1701R baseline, 74.38% sumR retained, paired-month CI about [+0.0168R, +0.3161R].
- 50%-target: 54.28% coverage, selected AvgR 0.2692R, 85.91% sumR retained, CI about [+0.0171R, +0.3195R].
- 60%-target: 59.41% coverage, selected AvgR 0.2707R, 94.56% sumR retained, CI about [+0.0181R, +0.2891R].

The result is threshold-stable across 40/50/60, but still comes from the same 12 OOS months and has a poor worst selected month around -0.45R to -0.56R depending on threshold.

### Adaptive shadow-expert router family

- 2,798 OOS trades.
- 40%-target is positive: ~49.96% coverage, selected AvgR 0.2924R vs 0.2085R baseline, 70.08% sumR retained, CI about [+0.0165R, +0.1458R].
- 50% and 60% intervals cross zero.

This is a narrower lead than the initial unweighted adaptive result.

### Router EMA+BOS family

- 479 OOS trades.
- 40% and 50% intervals cross zero.
- 60%-target is only marginally positive, with CI lower bound around +0.0005R and a worst selected month near -0.475R.

Not robust enough for promotion.

### Slow multi-horizon momentum family

- 804 OOS trades.
- Selected AvgR improves at several thresholds and sumR retention can exceed 100%, but all paired-month uplift intervals cross zero.
- Worst selected months remain poor.

Not robust enough for promotion.

### MACD family

- only 172 OOS trades;
- some bootstrap intervals are positive, but monthly prediction Spearman is negative and several months contain very few or zero selected trades;
- worst selected month reaches roughly -1R.

Treat as sample-size/instability noise, not a positive gate.

### BOS/FVG and Trend20 families

Neither family clears a stable family-specific robustness gate. BOS/FVG remains a useful negative/control family because the filter frequently destroys substantial baseline sumR.

## Interpretation

Family-level threshold calibration is better than one global score threshold for the candidate-aware weighted model, but the candidate-blind control fails. Combined with the failed unique-opportunity common-state models, this means the evidence does **not** support a universal ML market-quality filter.

The most credible current hypothesis is narrower:

- engineered market + adaptive expert state contains some expected-R information;
- that information is useful only in interaction with particular strategy-family/candidate context;
- EMA pullback is the strongest current family lead;
- adaptive router is a secondary lead at a tighter threshold;
- other families are heterogeneous or unstable.

Because these hypotheses have now been inspected on the full 2025-08 through 2026-07 OOS sample, more slicing of the same 12 months would increase research overfitting rather than add confirmation evidence.

## Decision

- Family-specific gate: **PROMISING BUT NOT CONFIRMED**.
- EMA pullback: strongest lead, not promotion-ready.
- Adaptive router: secondary lead, not promotion-ready.
- Router/slow momentum: insufficient robustness.
- MACD: insufficient sample/stability.
- BOS/FVG and Trend20: no family gate.
- Candidate-blind common-state hypothesis: not established.
- No universal ML filter is promoted.
- No DL model is promoted.

## Next meaningful evidence

Stop tuning the same 12 OOS months.

The next useful test must be a genuinely fresh chronological holdout after 2026-08-01. The frozen research procedure should be:

1. train only on history available before July 2026 calibration;
2. use July 2026 scores to freeze the candidate-aware family thresholds;
3. apply those frozen rules to the next unseen month without re-tuning;
4. report both candidate-trade and unique-opportunity economics;
5. keep forced end-of-test/EOM artifacts out of any partial-month interpretation.

A full August-2026 month is preferable to a partial-month test. Until that fresh holdout exists, do not return the filter to Strategy Tester as a new strategy variant and do not claim promotion.
