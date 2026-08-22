# V31 — USD40 ML/DL/SVM MT5 economic gate

Date: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

V31 was a Strategy Tester / virtual-book research milestone. Current project-wide policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The V31 no-native-order/tester-only rules below describe V31 itself, not a permanent prohibition on researching or preparing production/live trading with real capital.

## Objective

The research objective was a USD40 starting balance and an aspirational 15% monthly return without increasing per-trade research risk above 1.00%.

The model gate is judged by exact MT5 economics rather than AUC alone: monthly/geometric returns, months >=15%, positive months, worst month, maximum MTM drawdown, rejects, turnover and opportunity breadth.

## Existing exact MT5 baseline

Across the accepted 18-month V30 Strategy Tester lake, the strongest USD40/1% baseline candidate was `adaptive_ewma_hl8_thr0`, with mean monthly return around 7.45%, geometric around 7.15%, 13/18 positive months, 5/18 months >=15%, worst month around -3.98%, and maximum monthly MTM DD around 10.56%.

Therefore that historical system did not meet the 15%/month research objective. The gap was an edge/opportunity-efficiency problem, not a reason to increase risk.

## Model-capacity finding before MT5 integration

Causal holdout work showed RBF-SVR, linear SVM/SVR and static/deeper MLP variants did not create robust economic uplift. ExtraTrees and CatBoost were materially stronger but still did not establish a stable 15%-per-month system offline.

This reinforced the finding that adding model capacity does not manufacture edge when target/state information is weak.

## V31 MT5 model-gate architecture

The exact gate is an MT5 Strategy Tester comparison. `V31ModelGateLabV1` keeps strategy/risk/execution semantics and inserts a causal model gate before virtual `OpenBook()`.

A precomputed score tape stores frozen-model pass bits per M15 bar, candidate and direction for CatBoost, ExtraTrees, MLP, linear SVM/SVR and selected ensembles.

## Causal score-tape protocol

For each OOS test month:
1. previous month is calibration month;
2. model fit uses only outcomes available before calibration-month start;
3. frozen model scores calibration month;
4. absolute threshold is derived from those scores;
5. threshold is applied unchanged to next test month;
6. no test-month label/quantile peeking.

## Exact MT5 comparison block

Historical comparison period:
`2026-02-01 -> 2026-08-01`.

Every model run resets to the same accepted adaptive-state checkpoint. Target book is `usd40_r1p0_cent`.

## Promotion criteria

A V31 model is not promoted merely because average return improves. Evidence must show material same-period exact-MT5 improvement without unacceptable drawdown/turnover deterioration or opportunity collapse, and not be carried by a single exceptional month.

The aspirational 15%-monthly target is reported explicitly; risk is not increased to manufacture it.

## Historical V31 execution contract

- V31 contains no native broker-order path.
- `MQL_TESTER` guard is mandatory for V31.
- No Martingale/grid/doubling.
- USD40 is a virtual Strategy Tester research book.

Those are V31 phase semantics. Current project-wide production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
