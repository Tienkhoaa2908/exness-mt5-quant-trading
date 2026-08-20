# V37 dedicated SMC quality filter

Date: 2026-08-20

## Motivation

V34 exact-MT5 showed `v34_smc_ict_causal` is the only new specialist with material positive standalone economics, but it is weak and high-turnover relative to the adaptive baseline:

- USD40 -> USD66.83 over 12 months;
- geometric ~4.37%/month;
- max MTM DD ~15.58%;
- 1,077 trades;
- AvgR ~0.066R;
- PF ~1.108.

Its monthly return correlation with `adaptive_ewma_hl8_thr0` is low (~0.13), so it is worth preserving as an independent-alpha lane if quality can be improved without stacking uncontrolled same-symbol risk.

The generic V35 cross-expert meta-router is rejected and must not be reused as the SMC gate.

## Diagnostic protocol

Use only V34 exact-MT5 norm-book SMC trade outcomes as labels. Join each SMC entry to the latest V30 feature row satisfying:

`feature_available_time <= entry_time`

Models:

- HistGradientBoostingRegressor;
- ExtraTreesRegressor;
- MLP 48-24.

Target: exact-MT5 `r_multiple`.

Chronological folds: February-July 2026. For each test month:

- training trades must have exited before the prior calibration month starts;
- prior-month score distribution defines a fixed 40th-percentile threshold (development hypothesis: approximately keep60);
- test-month outcomes are never used to set that month's threshold.

Metrics:

- coverage;
- baseline vs selected AvgR;
- selected SumR preservation;
- score/realized-R Spearman;
- sign breadth by month.

This phase is trade-level diagnostic only. It is **not PnL evidence** because filtering changes one-position state, future opportunity availability, USD40 volume feasibility and adaptive/execution path.

## Promotion to an exact-MT5 experiment

Only if the dedicated diagnostic is stable should a single frozen rule be materialized on **all active SMC signal bars**, not only historical executed trades. The all-bar gate must use causal bar state and then return to the tester-only V34 engine.

Any combined baseline + SMC test must cap aggregate same-symbol stop-risk at <=1.00%. Do not run baseline at 1% plus SMC at another 1% simultaneously.

Fresh confirmation is required after development. LIVE remains forbidden.
