# V31.1 — exact MT5 Strategy Tester model gate on continuous USD40 capital

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: Strategy Tester / virtual-book research only. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Objective

Evaluate whether causal ML / neural / SVM gating can move the existing XAUUSDm system materially toward an aspirational 15% monthly return target when starting from **USD 40**, without increasing the research risk ceiling above 1.00% per trade.

The final economic evidence must come from the MT5 Strategy Tester outputs (`monthly_summary.csv`, `trades.csv`, manifest), not from a Python-reconstructed PnL curve.

## Capital contract

V30 USD40 books reset to USD40 at every month boundary. That is useful for month-by-month comparability but is not a continuous USD40 account.

V31.1 changes only the target `b==3` USD40 / 1.00%-risk book:

- MT5 tester `Deposit=40`, `Currency=USD`, leverage assumption 1:200.
- Book name: `usd40_r1p0_cent_continuous`.
- Initial capital: USD40.
- Capital carries month-to-month.
- Risk target remains 1.00% of current book balance per trade.
- Existing volume-step and 1:200 margin rejection logic remains active.
- Existing month-end liquidation is retained so the monthly 15% target can be measured consistently.
- Full-period peak/max-MTM-DD state is carried across month boundaries.

This is still a virtual-order Strategy Tester research book; no native/external broker order is permitted.

## Model gate

The same frozen V29/V30 12-candidate catalog is used. V31.1 inserts a causal accept/reject gate after the normal signal/session/feature checks and before virtual `OpenBook()`.

Gate bits:

- -1: baseline, no model gate.
- 0: CatBoost expected-R.
- 1: ExtraTrees expected-R.
- 2: deep tabular MLP, hidden layers 64-32-16.
- 3: linear SVM/SVR control (`LinearSVR`).
- 4: CatBoost AND ExtraTrees.
- 5: majority 2-of-4.

Training target remains realized `r_multiple`. Duplicate candidate opportunities are inverse-weighted by `(entry_time,direction)` multiplicity.

## Causal timing contract

Historical V30 feature rows are available at:

`feature_available_time = bar_features.time + 15 minutes`

Trade training joins use the latest row with `feature_available_time <= entry_time`.

For MT5 gate inference, the tape is keyed by **actual current M15 bar start T**, including session/weekend gaps, and model state is the latest feature row satisfying:

`feature_available_time <= T`

The older method that simply wrote `bar_open + 15 minutes` as the next gate timestamp is invalid across session gaps and must not be reused.

Linux pinned reference for the V31.1 DeepMLP tape:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

Expected rows: 23,616 data rows plus header.

## Walk-forward model protocol

- Accepted historical V30 lake: 2025-02 through 2026-07.
- Six-month warm-up.
- For every OOS test month, previous month is calibration month.
- Fit labels only from trades whose `exit_time` is before calibration-month start.
- Threshold is the median of frozen-model scores on calibration-month samples.
- The absolute threshold is applied to the next test month.
- No test-month quantile peeking.
- No random K-fold.

Pinned Python dependencies for deterministic local tape generation:

- numpy 2.3.5
- pandas 2.2.3
- scikit-learn 1.8.0
- catboost 1.2.8

## Exact MT5 comparison period

All modes start from the same accepted adaptive state after 2026-01 and run:

`2026-02-01 -> 2026-08-01`

Before every mode, the adaptive state is restored to the same checkpoint. This prevents one model pass from inheriting another pass's adaptive updates.

Modes:

- baseline
- catboost
- extratrees
- deep_mlp
- linear_svm
- catboost_and_extratrees
- majority_2of4

## Primary decision candidate

Primary same-candidate comparison is:

`adaptive_ewma_hl8_thr0`

Best-candidate-per-mode tables are exploratory only. They cannot substitute for the primary comparison because selecting a different candidate after seeing the same backtest is a multiple-comparison bias.

## Required exact metrics

From MT5 output only:

- starting capital USD
- ending capital USD
- total return
- arithmetic and geometric monthly return
- count of months >= 15%
- positive months
- worst/best month
- full-period max MTM drawdown
- trade count
- AvgR and profit factor from the trade ledger
- volume and margin rejects
- gross turnover / starting capital

The 15% monthly target is pass/fail evidence, not a promise. Risk is not increased above 1.00% merely to force the target.

## Runtime

One-shot runner:

`runtime/v31_mt5_model_gate/RUN_V31_1_EXACT_MT5_USD40_GIT_BASH.sh`

It rebuilds the causal tape from the accepted MT5 V30 run folders, builds the V31.1 EA deterministically from the accepted V30 source SHA, compiles each mode with a 0-error/0-warning gate, launches MT5 Strategy Tester for each mode, collects exact outputs, analyzes them, and emits one ZIP.

Source builder expected V31.1 SHA-256:

`45ace4bd7465dbfb8a1b5670b67d372643b1eea057b1d7a44d80b91caf2b7c3e`

Accepted starting adaptive-state SHA-256:

`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`

## Promotion rule

Do not promote any model because it has higher AUC, higher expected-R score, or a better Python backtest.

A model advances only if the exact MT5 continuous-USD40 evidence improves the primary candidate economically without an unacceptable drawdown/turnover deterioration. If no model approaches the 15% target at <=1.00% risk/trade, the next research direction is opportunity generation / strategy-family design / allocation, not leverage escalation.
