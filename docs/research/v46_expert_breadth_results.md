# V46 Expert-Breadth Walkforward Results

Date: 2026-08-22

## Evidence identity

Accepted uploaded ZIP SHA256:
`ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.

Bundle integrity:
- ZIP CRC PASS;
- internal SHA manifest 24/24 PASS;
- run HEAD `655bf2f77503d91d0749d2f5c99cc0ad8678c388`;
- branch `agent/v46-expert-breadth-walkforward`;
- accepted V38 parent SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- V45 parent SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- canonical V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- compiler `Result: 0 errors, 0 warnings`;
- MT5 launch rc=0;
- exact run id `v46_expert_breadth_walkforward_v1__XAUUSDm__PERIOD_M15__2021-01-03_00-00-00__672937`;
- safety markers PASS: tester-only, native/external broker orders disabled, risk unchanged, live authorization false.

Protocol: one continuous exact MT5 run, XAUUSDm M15, 2021-01-03 -> 2026-08-01, $40 USD, leverage 1:200, cold-start state, first six months warm-up.

## Formal result

`STATUS=HOLD`

The preregistered primary `v46_hl10_thr0p05_breadth4` passed 13 of 14 readiness checks. The only failed check was `at_least_75pct_full_years_nonnegative`: 2 of 4 full years were nonnegative.

This formal HOLD must not be rewritten after seeing the result.

## Primary breadth4 economics

Full cold-start:
- $40 -> $106.947120;
- total return +167.3678%;
- max MTM DD 16.5983%.

Evaluation (2021-07 -> 2026-07):
- compounded return +167.367657%;
- geometric/month +1.625287%;
- annualized +21.344869%;
- 825 trades;
- AvgR +0.144313R;
- SumR +119.05819R;
- PF 1.281739;
- 30 active months / 61 evaluation months;
- positive active-month ratio 66.67%;
- -0.05R/trade friction stress remains +77.80819R.

Risk stability:
- worst full year -0.810156%;
- worst rolling-12m -1.946983%;
- all 50 rolling-12m observations were not worse than -5%;
- 2021 post-warm-up holdout return 0.0% because breadth4 took no trades in that segment.

Full-year decomposition:
- 2022: -0.744202%, 32 trades;
- 2023: -0.810156%, 67 trades;
- 2024: +5.179345%, 83 trades;
- 2025: +42.785951%, 417 trades;
- 2026 Jan-Jul: +80.829731%, 226 trades.

This is economically very different from V45 HL10p05. In the common 2022-07 -> 2026-07 evaluation window:
- V45 return +105.786638%, 1,556 trades, PF 1.132725, DD 56.2976%, turnover 7267.77x start-$40;
- V46 breadth4 return about +169.372330%, 793 trades, PF 1.281739, DD 16.5983%, turnover about 6193.53x start-$40.

Thus breadth4 reduced DD by about 70.5%, cut trade count by about 49.0%, reduced turnover by about 14.8%, roughly doubled AvgR, and increased common-window compounded return by about 60.1%.

The recent strong regime was still retained. For 2025-08 -> 2026-07 breadth4 returned about +95.50% versus V45 HL10p05 about +138.29%, with 407 versus 516 trades. This is a material return sacrifice, but the multi-year risk improvement is much larger.

## Crisis/regime interpretation

The result supports the intended mechanism: in weak regimes the system mostly stops opening new risk instead of forcing trades.

Examples:
- 2022: only 32 trades for the full year and -0.74%, versus the V45 router's large 2022 loss;
- 2023: -0.81% with only 67 trades; this is an opportunity-cost year rather than a capital-destruction year;
- 2024: +5.18%, reversing the V45 router's -25.75% despite gold being a strong bull market;
- 2025-2026: substantial edge remains when breadth is healthy.

This is consistent with the engineering objective established before the accepted V46 run: crisis/transition regimes may be flat or mildly negative, but they must not create catastrophic drawdown.

External market context remains relevant but is not encoded in the strategy. World Gold Council characterized 2022 as a year of conflicting forces, while gold rose about 25.5% and set 40 all-time highs in 2024. No war-date or calendar exception is used by breadth4.

## Sensitivity comparators

Breadth3 (not promotable):
- $40 -> $95.774652;
- DD 31.9081%;
- PF 1.194419;
- annualized 18.7394%;
- worst full year -13.1942%;
- worst rolling-12m -16.4151%.

Breadth5 (not promotable):
- $40 -> $64.436498;
- DD 15.1449%;
- PF 1.235976;
- annualized 9.8336%;
- only 20 active months;
- no losing full calendar year.

The sensitivity curve is coherent: breadth3 trades too much and leaves too much drawdown; breadth5 protects capital but suppresses too much opportunity; preregistered breadth4 is the useful middle ground.

## Data-quality / observability issue

The generated MQL source correctly defines `CANDIDATE_COUNT 26` and the monthly/trade ledgers contain all three V46 candidates. However the inherited manifest writer still emits stale metadata:
- `candidate_count=23`;
- `source_file=V38FastHarvestLab.mq5`.

This does not invalidate the accepted V46 trade evidence because source SHA, compiled source, candidate ledgers and analysis all identify the V46 candidates. It is nevertheless an observability bug and must be fixed before the next campaign.

## Decision

Formal status remains HOLD because the preregistered sign-count gate failed. Economically, the breadth mechanism is validated strongly enough that another same-sample parameter sweep is not justified.

Do not tune breadth count, HL10 half-life or 0.05 score threshold on this evidence.

Next campaign should freeze breadth4 and use fresh forward/shadow evidence. Post-hoc ADX/DI observations from V45 may be logged as shadow diagnostics but must not alter the primary trade decision until validated on fresh evidence.

REAL-MONEY LIVE TRADING remains forbidden.
