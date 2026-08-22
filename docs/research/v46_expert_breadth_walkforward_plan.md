# V46 Expert-Breadth Walkforward Plan

Date: 2026-08-22

## Policy note

V46 was a historical/forward-validation milestone. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V46 tester-only/no-broker-order restrictions describe V46 itself. They are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Motivation

V45 exact evidence is HOLD across 2022-2026. The frozen HL10p05 router remained strong in 2025-2026 but lost materially in 2022 and 2024. Selected-source decomposition showed weak periods were broad ensemble failures while the router only required the selected expert's own EWMA score to exceed 0.05.

V46 tests one structural hypothesis: keep the existing causal HL10p05 expert router, but stay in cash unless the shadow-expert ensemble has sufficient health breadth.

## Preregistered primary

`v46_hl10_thr0p05_breadth4`

Rules:
- use the existing HL10 EWMA expert scores;
- selected expert must still satisfy `adaptive_min_score=0.05`;
- before opening new risk, at least 4 of all 5 shadow experts must have HL10 EWMA score >=0.05;
- expert scores remain updated only from realized-R of the independent norm-book shadow experts;
- no future data, no price look-ahead, no later state injection.

The breadth count is a causal portfolio-level cash/off gate. It does not change the underlying expert signals or trade exits.

## Sensitivity only

Two additional candidates run in the same tester invocation:
- `v46_hl10_thr0p05_breadth3_sensitivity`;
- `v46_hl10_thr0p05_breadth5_sensitivity`.

They are diagnostic comparators only and are not eligible to replace the preregistered breadth4 primary by same-sample ranking.

## Exact protocol

One MT5 Strategy Tester invocation only:
- symbol XAUUSDm;
- timeframe M15;
- Model=0;
- Deposit=$40 USD;
- leverage 1:200;
- FromDate=2021.01.03;
- ToDate=2026.08.01;
- cold-start adaptive state;
- first six observed months warm-up;
- monthly summary and full trade ledger retained.

2021 is included because broker history begins in early 2021 and V45 did not use it.

## What does not change in V46

- stop/risk geometry;
- 1.00% research stop-risk ceiling;
- expert entry logic;
- HL10 half-life;
- selected-expert threshold 0.05;
- exits;
- V46 tester-only execution path;
- no native/external broker orders in V46.

V46 `strategy_logic_changed=1` only because the portfolio-level breadth/cash gate is new. `risk_changed=0`.

## Primary readiness gate

Only breadth4 can pass. The preregistered gate covers evaluation length, full-run DD, PF, annualized return, full-year/rolling stability, active-month breadth, trade count and -0.05R/trade stress.

These gates are fixed before the exact V46 run and must not be loosened after observing results.

## Canonical source identity correction

The canonical deterministic V46 source SHA is:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

No MQL logic bytes were changed to create the hash correction and no V46 tester run had started at the time of correction.

Canonical entrypoint:
`runtime/v46_expert_breadth/BOOTSTRAP_V46_CANONICAL_GIT_BASH.sh`.

## Interpretation

A V46 primary pass supported progression to the next execution-reconciliation phase in the historical workflow. V46 itself did not constitute final production/live deployment evidence.

Current live-trading research/deployment target is governed by ADR-049 and later V49 readiness evidence.
