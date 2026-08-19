# V30 August-2026 fresh holdout preregistration

Frozen: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: tester-only/offline research. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Reason for freezing now

The accepted 18-month lake and subsequent causal ML/DL tournament have now been analyzed extensively through July 2026. Additional slicing/tuning on the same 2025-08 through 2026-07 OOS months would increase research-overfitting risk.

The next meaningful evidence is a genuinely unseen month. This document freezes the August-2026 expected-R gate **before August outcomes are imported into the research dataset**.

A complete August month is preferred. A partial-month Strategy Tester run is not valid promotion evidence because V30 `OnDeinit()` calls `FinalizeMonth()` and closes the active month with synthetic end-of-test/EOM exits.

## Frozen model specification

Primary model:

- `ExtraTreesRegressor`
- expected-R target: `r_multiple`
- engineered-expert feature set
- candidate-aware one-hot context
- 80 estimators
- `min_samples_leaf=12`
- `max_features=0.65`
- `random_state=29`

Preprocessing is train-only:

- median imputation;
- 0.5% / 99.5% winsorization;
- standardization;
- 163 numeric/model features;
- ordered feature-name SHA-256: `be37a63a994d7b4b949c76b10cda6a8789157163ceb072ab597fb4fcecaaf44f`.

Training sample is frozen to trades with:

`exit_time < 2026-07-01 00:00:00`

Training size:

- 7,113 candidate-trades;
- 1,903 unique `(entry_time,direction)` opportunities.

Training weight per trade:

`1 / count(entry_time,direction)`

normalized to mean weight 1.

## Frozen July score calibration

Calibration month: July 2026.

July outcomes are not used to tune the score threshold; only the frozen model's July score distribution is used.

July calibration contains 370 candidate-trades.

Primary gate is the family-aware **40%-keep target**, corresponding to the 60th percentile of July model scores.

Frozen thresholds:

- global fallback: `0.8053741939364688`
- adaptive shadow-expert router: `0.8130452224988163`
- EMA pullback: `0.9300156984255423`
- router EMA+BOS: `0.9202902130866898`
- slow multi-horizon momentum: `0.6853211821069352`

July family calibration counts below 20 use the frozen global fallback:

- Trend20 breakout
- BOS/FVG
- MACD

No August threshold recomputation is allowed.

## Predeclared subgroup

The only predeclared secondary subgroup is `ema_pullback_h1`, because it was the strongest threshold-stable family in the already-completed robustness analysis.

Other family slices may be reported descriptively, but must not be treated as independent confirmation claims.

## Fresh August evaluation

When the complete August-2026 MT5 feature/trade output exists:

1. stitch/trim it causally without modifying the frozen historical lake;
2. enforce `feature_available_time = bar time + 15 minutes`;
3. reconstruct the frozen model deterministically from pre-July labels only;
4. apply the exact thresholds above to August without recalibration;
5. report all norm-book candidate trades;
6. additionally collapse/report unique `(entry_time,direction)` opportunities so duplicate catalog variants cannot hide failure;
7. report coverage, AvgR, sumR, sumR retention, win rate, tail-loss rate and realized-R drawdown proxy;
8. report the predeclared EMA subgroup separately;
9. no August-driven feature, hyperparameter, family allowlist or threshold changes.

## Decision rule

August is a fresh falsification/confirmation checkpoint, not an automatic promotion gate.

- Material failure on August rejects or materially downgrades the current family-threshold hypothesis.
- A pass permits only the next validation stage; it does not authorize PAPER/DEMO by itself.
- Any strategy change still requires tick-level re-simulation after offline evidence survives.
- REAL-MONEY LIVE TRADING remains forbidden regardless of result.

Frozen machine-readable specification:

`experiments/v30_aug2026_holdout/frozen_gate.json`

State checkpoint after July:

`experiments/v30_aug2026_holdout/state_after_2026_07.csv`

State file SHA-256 from the accepted runtime bundle:

`63e3e8e652fab73a1e2f9494117b3e4afe199100d504f9db6077c24e610e0c47`
