# V46 Expert-Breadth Walkforward Plan

Date: 2026-08-22

## Motivation

V45 exact evidence is HOLD across 2022-2026. The frozen HL10p05 router remains very strong in 2025-2026 but loses materially in 2022 and 2024. Selected-source decomposition shows the weak periods are broad ensemble failures: EMA, SlowMom and Trend are simultaneously negative, while the current router only requires the selected expert's own EWMA score to exceed 0.05.

Market context matters, but it must not be hard-coded as a calendar/news exception. 2022 was a genuine crisis/transition regime with opposing safe-haven, inflation, rate and USD forces; standing aside can be correct. 2024 was a strong gold trend year, so the router's large loss there is still evidence of a regime/routing weakness. V46 therefore tests whether internal expert-health breadth can decide when to remain in cash without knowing event labels such as war dates.

V46 tests one structural hypothesis: keep the existing causal HL10p05 expert router, but stay in cash unless the shadow-expert ensemble has sufficient health breadth.

## Preregistered primary

`v46_hl10_thr0p05_breadth4`

Rules:
- use the existing HL10 EWMA expert scores;
- selected expert must still satisfy the inherited `adaptive_min_score=0.05`;
- before opening new risk, at least 4 of all 5 shadow experts must have HL10 EWMA score >=0.05;
- expert scores remain updated only from realized-R of the independent norm-book shadow experts, exactly as before;
- no future data, no price look-ahead, no later state injection.

The breadth count is a causal portfolio-level cash/off gate. It does not change the underlying expert signals or trade exits.

## Sensitivity only

Two additional candidates run in the same tester invocation:
- `v46_hl10_thr0p05_breadth3_sensitivity`;
- `v46_hl10_thr0p05_breadth5_sensitivity`.

They are diagnostic sensitivity comparators only. `sensitivity_candidates_eligible_to_promote=false`. Breadth3 or breadth5 must not become the promoted result because they look better on this same sample.

Post-hoc V45 price-feature diagnostics, including an ADX upper-bound observation and DI direction-alignment observation, are explicitly excluded from the V46 primary. They can only be tested later under a new preregistered campaign if V46 breadth is insufficient.

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

2021 is included because diagnostic terminal evidence showed XAUUSDm history begins in early 2021 and V45 did not use 2021. The post-warm-up 2021 segment is therefore a specifically tracked unseen historical holdout for the V46 mechanism.

## What does not change

- stop/risk geometry;
- 1.00% research stop-risk ceiling;
- expert entry logic;
- HL10 half-life;
- selected-expert threshold 0.05;
- exits;
- no native/external broker orders;
- Strategy Tester guards;
- live trading remains forbidden.

V46 `strategy_logic_changed=1` only because the portfolio-level breadth/cash gate is new. `risk_changed=0`.

## Crisis-regime interpretation

V46 is not required to make money in every crisis year. A robust result may deliberately be flat or slightly negative when the ensemble is unhealthy. The acceptance objective is capital preservation plus retention of enough edge in healthy regimes.

Accordingly, the generic gates are used instead of event-specific exclusions: full-run DD, worst full year, rolling-12m loss floor, activity floor, PF, return and friction stress. No calendar label such as "war year" is used in trading logic or readiness logic.

## Primary readiness gate

Only breadth4 can pass. All must hold:
- >=60 evaluation months;
- full cold-start max MTM DD <=20%;
- PF >=1.20 after warm-up;
- annualized return >=10% after warm-up;
- >=4 full calendar evaluation years;
- >=75% full years nonnegative;
- worst full year >=-10%;
- >=75% rolling-12m windows not worse than -5%;
- worst rolling-12m >=-10%;
- >=24 active months;
- >=50% of active months positive;
- post-warm-up 2021 holdout return >=-10%;
- >=400 evaluation trades;
- SumR remains positive after -0.05R/trade stress.

These gates are fixed before the exact V46 run. Do not loosen them after observing results.

## Canonical source identity correction

The original preregistration recorded V46 SHA `3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13`. The first Windows build stopped before MetaEditor/MT5 because the generated source SHA was instead `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

This was independently reproduced from the accepted V45 evidence ZIP source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2` using the tracked V46 transformation. Therefore the canonical deterministic V46 source SHA is:

`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`

No MQL logic bytes were changed to create this correction and no V46 tester run had started. The correction changes only the expected hash identity used by the harness.

Canonical entrypoint:
`runtime/v46_expert_breadth/BOOTSTRAP_V46_CANONICAL_GIT_BASH.sh`.

## Interpretation

`V46_BREADTH_PRIMARY_PASS` permits the next paper/demo execution-reconciliation phase only. It does not authorize real-money trading.

`HOLD` means the breadth hypothesis is not strong enough; do not promote a sensitivity variant by ranking it on the same evidence.
