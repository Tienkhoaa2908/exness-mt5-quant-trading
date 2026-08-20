# V31 — USD40 ML/DL/SVM MT5 economic gate

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: Strategy Tester / virtual-book research only. REAL-MONEY LIVE TRADING IS FORBIDDEN. Research stop-risk ceiling remains 1.00% per trade.

## Objective

The user-level research objective is a USD 40 starting balance and an aspirational 15% monthly return. This is a research target, not a guarantee and not a reason to increase per-trade risk above 1.00%.

The model gate is judged by exact MT5 economics, not by AUC alone:

- monthly return on `usd40_r1p0_cent`;
- geometric monthly return;
- months >= 15%;
- positive months;
- worst month;
- maximum MTM drawdown;
- volume/margin rejects;
- turnover and opportunity breadth.

## Existing exact MT5 baseline

Across the accepted 18-month V30 Strategy Tester lake, the strongest USD40/1% baseline candidate is `adaptive_ewma_hl8_thr0`:

- arithmetic mean monthly return: about 7.45%;
- geometric mean monthly return: about 7.15%;
- 13/18 positive months;
- 5/18 months reached 15%;
- worst month about -3.98%;
- maximum monthly MTM DD about 10.56%;
- 68 volume rejects.

Therefore the present system does **not** meet the 15%/month objective. The gap is roughly a doubling of economic edge/opportunity efficiency, not a small model-tuning issue.

For the most recent six-month block (2026-02 through 2026-07), exact MT5 USD40/1% results for `adaptive_ewma_hl8_thr0` are:

- Feb -0.6979%
- Mar -3.9798%
- Apr +0.5548%
- May +11.2547%
- Jun +20.5404%
- Jul +17.9437%

Mean = 7.6027%, geometric mean = 7.1869%, 4/6 positive months, 2/6 months >=15%, max monthly MTM DD = 6.8702%.

## Model-capacity finding before MT5 integration

A new USD40-specific temporal holdout was built using only causal bar state (`feature_available_time = bar open timestamp + 15 minutes`), candidate identity and direction. Training uses inverse `(entry_time,direction)` opportunity multiplicity weighting.

Frozen-development protocol for a six-month diagnostic:

- fit outcomes ending before 2026-01-01;
- use January-2026 score distribution to freeze the gate threshold;
- evaluate Feb-2026 through Jul-2026;
- threshold calibration does not use Feb-Jul outcomes.

Approximate R-based diagnostics on the existing MT5 trade ledger show:

- RBF-SVR: fails badly; very low coverage and negative selected R for the main families.
- Linear SVM/SVR: no robust economic uplift.
- static MLP neural network: no robust economic uplift; some variants actively degrade expected R.
- deeper MLP variants do not solve the problem and are unstable.
- ExtraTrees and CatBoost remain materially stronger than SVM/MLP on this dataset.
- CatBoost / ExtraTrees signals are strongest for slow-momentum and some adaptive/EMA/router contexts, but still do not establish a stable 15%-per-month system offline.

This reinforces the prior V30 finding: adding neural-network capacity does not manufacture edge when the causal target/state information is weak.

## V31 MT5 model-gate architecture

The next exact gate is built as an MT5 Strategy Tester comparison, not an offline equity-curve claim.

A new tester-only EA, `V31ModelGateLabV1`, keeps the V30 strategy/risk/execution semantics and inserts one causal model gate immediately after all normal candidate filters and before `OpenBook()`.

The gate source is a precomputed causal score tape. For every current M15 bar, every one of the 12 candidates and both LONG/SHORT directions, the tape stores a bit mask indicating whether each model passes its frozen score threshold.

Model bits:

- bit 0: CatBoost expected-R gate;
- bit 1: ExtraTrees expected-R gate;
- bit 2: MLP neural-network gate;
- bit 3: Linear SVM/SVR gate;
- bit 4: CatBoost AND ExtraTrees ensemble;
- bit 5: majority-2-of-4 ensemble.

The initial exact MT5 run compares baseline plus bits 0..3. Ensembles are reserved for a second run only if the first comparison justifies them.

## Causal score-tape protocol

For each OOS test month from 2025-08 through 2026-07:

1. previous month is the score-calibration month;
2. fit data includes only trades whose exit time is before the calibration-month start;
3. sample weights are inverse duplicate-opportunity multiplicity;
4. the fitted model scores calibration-month trades;
5. threshold = median calibration score (50% nominal keep target);
6. the same frozen threshold is used to score every bar/candidate/direction in the next test month;
7. no test-month labels are used to create that month's score tape.

The tape is therefore a deterministic walk-forward model output, not a hindsight pass/fail table.

## Exact MT5 comparison block

The first V31 exact comparison is intentionally only six months:

`2026-02-01 -> 2026-08-01`

Every model run is reset to the exact accepted adaptive state after January 2026 (`state_after_chunk2.csv`) so baseline and model gates start from identical shadow-expert state.

Runs:

1. baseline, no ML gate;
2. CatBoost gate;
3. ExtraTrees gate;
4. MLP neural-network gate;
5. Linear SVM/SVR gate.

Target book for decision: `usd40_r1p0_cent`.

All normal 10k and lower-risk virtual books may still be emitted for diagnostics, but they do not determine the USD40 objective gate.

## Promotion criteria

A V31 model is not promoted merely because it increases average return. Minimum evidence required before a broader 12-month/fresh holdout run:

- meaningful improvement over the exact same-period MT5 baseline;
- no risk/trade above 1.00%;
- no material worsening of maximum monthly MTM DD;
- no collapse in opportunity breadth;
- improvement is not carried by one exceptional month only;
- volume rejects remain quantified;
- all model-gated outputs come from Strategy Tester, not reconstructed offline PnL.

The aspirational 15%-monthly target is recorded explicitly as `months >= 15%` and mean/geometric monthly return. Failure to reach it is reported as failure; risk is not increased to force the number.

## Safety

- No `OrderSend`, `OrderSendAsync`, `CTrade`, external broker API or live path is introduced.
- `MQL_TESTER` guard remains mandatory.
- No Martingale/grid/doubling.
- USD40 is a virtual Strategy Tester research book.
- LIVE trading remains forbidden.
