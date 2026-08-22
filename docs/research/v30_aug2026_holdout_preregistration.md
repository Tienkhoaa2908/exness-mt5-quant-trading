# V30 August-2026 fresh holdout preregistration

Frozen: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

This preregistration was a tester-only/offline V30 research artifact. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Its tester-only execution scope was phase-specific and does not prohibit later production/live research or real-capital deployment engineering.

## Reason for freezing

The accepted 18-month lake and causal ML/DL tournament had been analyzed extensively through July 2026. Additional tuning on the same OOS months would increase overfitting risk, so the next meaningful evidence was a genuinely unseen month.

A complete August month was preferred because a partial-month Strategy Tester run could create synthetic end-of-test/EOM exits.

## Frozen model specification

Primary model:
- `ExtraTreesRegressor`;
- expected-R target `r_multiple`;
- engineered-expert feature set;
- candidate-aware one-hot context;
- 80 estimators;
- `min_samples_leaf=12`;
- `max_features=0.65`;
- `random_state=29`.

Preprocessing is train-only: median imputation, 0.5%/99.5% winsorization and standardization.

Ordered feature-name SHA-256:
`be37a63a994d7b4b949c76b10cda6a8789157163ceb072ab597fb4fcecaaf44f`.

Training sample is frozen to trades with `exit_time < 2026-07-01 00:00:00`, with inverse opportunity-multiplicity weights.

## Frozen July score calibration

Calibration month: July 2026. July outcomes are not used to tune the score threshold; only the frozen model's July score distribution is used.

Primary gate is the family-aware 40%-keep target. Frozen thresholds and family fallbacks are part of the machine-readable specification and cannot be recomputed from August outcomes.

## Fresh August evaluation

When complete August output exists:
1. stitch/trim causally without modifying the frozen historical lake;
2. enforce `feature_available_time = bar time + 15 minutes`;
3. reconstruct the frozen model from pre-July labels only;
4. apply exact frozen thresholds without August recalibration;
5. report all norm-book candidate trades;
6. report unique `(entry_time,direction)` opportunities;
7. report coverage, AvgR, SumR retention, win rate, tail-loss rate and realized-R drawdown proxy;
8. report only preregistered subgroups as confirmation evidence;
9. make no August-driven feature/hyperparameter/allowlist/threshold changes.

## Decision rule

August is a fresh falsification/confirmation checkpoint, not an automatic promotion gate.

Material failure rejects or downgrades the historical family-threshold hypothesis. A pass permits the next validation stage; any strategy change still requires tick-level re-simulation after offline evidence survives.

The historical V30 phase itself does not determine current project-wide live readiness. ADR-049 and the later V49 execution evidence govern production/live research and deployment progression.

Frozen machine-readable specification:
`experiments/v30_aug2026_holdout/frozen_gate.json`.

State checkpoint after July:
`experiments/v30_aug2026_holdout/state_after_2026_07.csv`.

State file SHA-256:
`63e3e8e652fab73a1e2f9494117b3e4afe199100d504f9db6077c24e610e0c47`.
