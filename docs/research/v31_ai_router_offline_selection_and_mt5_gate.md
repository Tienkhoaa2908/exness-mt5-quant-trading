# V31 — frozen AI router model selection and MT5 implementation gate

Date: 2026-08-20
Safety: tester-only / virtual orders. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Objective

Develop nonlinear AI controls around the accepted V30 causal feature lake and then evaluate the **actual MQL implementation** inside MT5 Strategy Tester. The economic target is a virtual `$40` starting book and an aspirational `15%/month` target, while preserving the research ceiling of **no more than 1.00% risk per trade**.

The target is a gate, not a guarantee. A model that reaches a high average by concentrating losses, excessive turnover, volume rejects, or a few lucky months must be rejected.

## Existing benchmark

The strongest existing `$40 / 1%` V30 baseline, `adaptive_ewma_hl8_thr0`, produced about `7.45%` arithmetic average monthly return over the accepted 18-month monthly-reset research book. Only 5/18 months reached 15%. It therefore does not meet the new target.

## Causal data contract

V30 bar rows are stamped with the open time of `r[1]`, the just-closed M15 bar. Offline availability remains:

`feature_available_time = bar_features.time + 15 minutes`

All V31 model samples obey that rule. Incomplete future targets remain missing. Heavy duplicated catalog opportunities are controlled in training by inverse `(entry_time,direction)` multiplicity weights.

## Frozen training / calibration split

Compact input dimension: 73.

- 42 causal bar / market / expert-state features.
- 19 safe entry-state features.
- 12 candidate one-hot features.

Frozen timeline:

- model labels: trade exits strictly before `2025-07-01`;
- score calibration: July 2025 score distribution only;
- MQL implementation gate: `2025-08-01 -> 2026-08-01`.

No threshold is recomputed inside MT5.

This 12-month MT5 run is an implementation/economic **development backtest**, not a pristine new statistical confirmation set: model research has already inspected this historical period offline. A later untouched/future holdout is still required before any paper/demo promotion.

## Models taken into MT5

### 1. Distilled deep neural network

Architecture:

`73 -> 96 -> 48 -> 24 -> 1`, ReLU hidden layers.

The network is trained to distill the score of a nonlinear RBF random-Fourier teacher. It predicts expected-R quality, not win/loss probability.

Frozen threshold:

`0.15744125843048096`

Offline candidate-trade development metrics over Aug-2025 through Jul-2026:

- selected coverage ~59.4%;
- selected AvgR ~0.318R versus ~0.189R baseline;
- selected sumR retention ~99.95%;
- paired-month uplift interval approximately `[+0.043R, +0.196R]`.

These figures remain subject to candidate duplication/book-path confounds; hence the MT5 gate.

### 2. Linear SVR control

A compact linear support-vector regression control on the exact same 73 standardized inputs.

Frozen threshold:

`-0.10337714735872365`

It is deliberately weaker/nonlinear-capacity-limited and serves as a control for whether the DNN adds useful nonlinear structure.

### 3. RBF-kernel approximation teacher

384 random Fourier features, `gamma=0.004`, followed by weighted Ridge expected-R regression. The exact frozen transform and coefficients are embedded in MQL.

Frozen threshold:

`0.16803128`

This provides a direct kernelized nonlinear control against the distilled DNN while avoiding a large exact support-vector set inside MQL.

## Router semantics

The original 12 V30 candidates remain untouched as baselines. At each causal base-candidate opportunity:

1. V31 builds the exact compact 73-input state used by training.
2. DNN, linear SVR, and RFF-kernel teacher score the opportunity.
3. Each model retains the highest-score source opportunity for that bar.
4. If its frozen score threshold is met, that synthetic AI candidate opens virtual books using the same stop/TP/protection engine.
5. The peak-lock slow-momentum variant is excluded as a routed source because its exit contract differs from the synthetic router's non-peak-lock 8h timebox semantics.

The MQL catalog therefore contains 15 candidates total: 12 base + DNN + linear SVR + RFF-kernel router, each across the same four books.

## `$40` MT5 economic gate

Primary target book:

`usd40_r1p0_cent`

The formal evaluation after MT5 upload will report, per AI model and against the best V30 baseline:

- 12 monthly returns;
- arithmetic mean and median monthly return;
- months >= 15%;
- positive months;
- worst month;
- maximum monthly MTM drawdown;
- trade count;
- profit factor / AvgR;
- volume and 1:200 margin rejects;
- gross turnover;
- return concentration by month;
- robustness at `$40` 0.5% and 0.75% books.

The target is **not passed** merely because mean return is >=15%. Tail risk, breadth and execution feasibility must also be acceptable.

## MT5 test semantics

The one-shot gate uses MT5 Strategy Tester `Every tick` generated ticks on `XAUUSDm M15`, matching the historical V30 acquisition mode. The broker does not provide 12 months of real tick history for this interval, so the result must not be called a 12-month real-tick backtest.

No native/external broker order API is present. The virtual books use `OrderCalcProfit` for sizing/PnL mechanics only.

## Local QA before Windows compile

- model deployment arrays and thresholds match frozen NPZ artifacts;
- DNN manual inference parity tested on random 73-D inputs;
- linear SVR manual inference parity tested;
- RFF transform/output parity tested against the frozen teacher formula;
- candidate one-hot mapping verified;
- source safety scan: no `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or `PositionOpen`;
- MQL source brace/parenthesis balance passes;
- 10 local artifact tests pass;
- Bash runner `bash -n` passes.

Windows MetaEditor `0 errors / 0 warnings` remains a mandatory gate before Strategy Tester starts.

## Decision before MT5 evidence

V31 is **research-candidate only**. Offline evidence justifies one MT5 implementation backtest; it does not justify risk escalation, paper/demo promotion, or any live execution. Per-trade risk remains capped at 1.00%.
