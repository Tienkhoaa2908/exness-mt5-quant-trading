# V30 causal ML/DL tournament V2 — strict calibration, duplication audit, sequence controls

Date: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

This V30 checkpoint was offline/tester-only research. Current project-wide live policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V30's tester-only/no-broker-order semantics were phase-specific and are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Purpose

This checkpoint extends the accepted V30 18-month feature lake after the causal availability correction. The objective is not to maximize AUC; the gate is whether a model can causally reduce low-quality opportunities while preserving enough realized R, with chronological walk-forward validation and without test-month threshold peeking.

## Causal data contract

Offline availability:
`feature_available_time = bar_features.time + 15 minutes`.

A trade may only use the latest feature row with `feature_available_time <= entry_time`. Incomplete future labels remain missing values.

Canonical data:
- 35,344 causal M15 rows across 2025-02 through 2026-07;
- 136 raw V30 fields;
- 7,483 norm-book trades;
- 7,473 trades with complete 64-bar causal sequence;
- zero causal join violations.

## Engineered state features

V2 adds low-dimensional causal state-change features: expert fast/slow differences, observation confidence, cross-expert state, volatility/range context, tick-path state, DI spread, signal activity and causal clock encodings. Constant/non-informative fields are excluded.

## Strict walk-forward protocol

There are 12 OOS test months after six-month warm-up. For each month, the previous month is score calibration, training labels end before calibration-month start, threshold derives from frozen-model calibration scores, and the absolute threshold is applied unchanged to the next test month. No random K-fold or test-month quantile selection.

Baseline across OOS months: 5,066 candidate-trades, pooled AvgR 0.189049R, pooled SumR 957.72205R.

## Findings

Unweighted catalog-level ExtraTrees and HistGradientBoosting initially showed attractive expected-R filtering. Linear/static neural/market-only controls were weaker. Tail-loss classification remained weak.

True-sequence GRU/TCN/PatchTransformer did not beat stronger tabular controls under the same causal protocol, so DL escalation was rejected on the current evidence.

## Critical duplicate-opportunity confound

The norm-book catalog contained 7,483 candidate-trades but only 1,972 unique `(entry_time,direction)` opportunity groups over the full lake. In OOS, 5,066 candidate-trades represented only 1,347 unique opportunities.

This duplication materially overweights repeated catalog opportunities during training and economic aggregation. Unweighted candidate-trade results therefore cannot serve as promotion evidence by themselves.

Inverse-opportunity weighting materially weakened the initial ExtraTrees claim. A unique-opportunity-group model also failed to establish a universal common market-quality model because paired-month intervals crossed zero.

## Interpretation

The evidence does not support a universal ML market-quality filter. The stronger signal appears to require family/candidate-specific entry context and is partially amplified by repeated catalog opportunities.

## Tests

Local deterministic research tests passed, covering missing future labels, causal joins, target exclusion, chronology and sequence forward shapes.

## Decision

1. V30 feature lake remains ACCEPTED for offline research.
2. Causal availability `bar timestamp + 15 minutes` is mandatory.
3. Win/loss/tail classification remains REJECTED for promotion.
4. Sequence DL escalation is REJECTED on current evidence.
5. Unweighted catalog-level ExtraTrees uplift is not promotion evidence because duplication materially inflates robustness.
6. A weaker expected-R signal survives inverse-opportunity weighting, but unique-opportunity common-state models do not clear the robustness gate.
7. No universal ML gate is promoted.
8. Next historical research direction was family-specific expected-R filtering with explicit controls.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence. The historical V30 tester-only phase does not impose a project-wide live prohibition.
