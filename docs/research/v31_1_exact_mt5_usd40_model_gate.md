# V31.1 — exact MT5 Strategy Tester model gate on continuous USD40 capital

Date: 2026-08-20
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

V31.1 was Strategy Tester / virtual-book research only. Current project-wide policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The absence of native/external broker orders in V31.1 was a phase-specific tester contract, not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Objective

Evaluate whether causal ML / neural / SVM gating can move the existing XAUUSDm system materially toward an aspirational 15% monthly return target when starting from USD40, without increasing the research risk ceiling above 1.00% per trade.

The final economic evidence must come from MT5 Strategy Tester outputs, not Python-reconstructed PnL.

## Capital contract

V31.1 changes only the target continuous USD40 / 1.00%-risk virtual book:
- MT5 tester Deposit=40 USD, leverage assumption 1:200;
- book `usd40_r1p0_cent_continuous`;
- capital carries month-to-month;
- risk target remains 1.00% of current virtual balance per trade;
- volume-step and margin-rejection logic remain active;
- month-end liquidation remains enabled;
- full-period peak/max-MTM-DD state carries across months.

V31.1 itself remains a virtual-order Strategy Tester research build.

## Model gate

The frozen V29/V30 candidate catalog is used. V31.1 inserts a causal accept/reject model gate after normal signal/session/feature checks and before virtual `OpenBook()`.

Modes include baseline, CatBoost expected-R, ExtraTrees expected-R, deep MLP, linear SVM/SVR and selected ensembles.

## Causal timing contract

Historical V30 feature rows use:
`feature_available_time = bar_features.time + 15 minutes`.

Trade training joins use the latest row with `feature_available_time <= entry_time`. MT5 gate inference is keyed to actual current M15 bar starts, including session/weekend gaps.

Pinned V31.1 reference tape SHA-256:
`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`.

## Walk-forward protocol

- accepted historical V30 lake: 2025-02 through 2026-07;
- six-month warm-up;
- previous month is calibration month;
- fit labels only from trades exiting before calibration-month start;
- derive threshold from frozen-model calibration scores;
- apply unchanged to next test month;
- no test-month quantile peeking;
- no random K-fold.

## Exact MT5 comparison period

All modes start from the same accepted adaptive state after 2026-01 and run:
`2026-02-01 -> 2026-08-01`.

Before every mode, adaptive state is restored to the same checkpoint.

## Primary decision candidate

Primary same-candidate comparison:
`adaptive_ewma_hl8_thr0`.

Best-candidate-per-mode tables are exploratory only and cannot replace the primary comparison.

## Required exact metrics

From MT5 output only: starting/ending capital, total/monthly return, months >=15%, positive months, worst/best month, max MTM DD, trade count, AvgR, PF, volume/margin rejects and turnover.

The 15% monthly target is evidence, not a promise; risk is not increased merely to force the target.

## Historical runtime

One-shot runner:
`runtime/v31_mt5_model_gate/RUN_V31_1_EXACT_MT5_USD40_GIT_BASH.sh`.

Expected V31.1 source SHA-256:
`45ace4bd7465dbfb8a1b5670b67d372643b1eea057b1d7a44d80b91caf2b7c3e`.

Accepted starting state SHA-256:
`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`.

## Promotion rule

Do not promote a model because of AUC, expected-R score or offline PnL alone. Exact MT5 economics, drawdown, turnover and opportunity breadth control the V31.1 decision.

Current production/live research and deployment target is governed by ADR-049 and the later V49 readiness process, not by the historical V31.1 tester-only contract.
