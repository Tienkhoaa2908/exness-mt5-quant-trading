# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Strategy Tester only for exact historical validation; `AllowLiveTrading=0`, `AllowDllImport=0`.
- Native/external broker orders remain forbidden.
- `LIVE_AUTHORIZED=0`.
- Never use `git clean`.

## Repository / campaign

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Current follow-up branch: `agent/v47-forward-regime-shadow`.

Read first:
1. `docs/research/v46_expert_breadth_results.md`
2. `docs/research/v46_expert_breadth_walkforward_plan.md`
3. `docs/research/v46_posthoc_regime_diagnostics.md`
4. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

## Accepted V45 baseline diagnosis

Accepted V45 ZIP SHA256:
`490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`.

Primary HL10p05, 2022-07 -> 2026-07:
- compounded +105.786638%;
- annualized +19.331535%;
- max MTM DD 56.2976%;
- PF 1.132725;
- 1,556 trades;
- worst full year -25.749354%;
- worst rolling-12m -30.690805%.

V45 proved the recent edge was real but strongly regime-dependent.

## Accepted V46 result — FORMAL HOLD, MECHANISM STRONGLY VALIDATED

Accepted V46 ZIP SHA256:
`ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.

Integrity/provenance:
- ZIP CRC PASS;
- internal SHA manifest 24/24 PASS;
- evidence HEAD `655bf2f77503d91d0749d2f5c99cc0ad8678c388`;
- accepted V38 parent SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- canonical V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- compile `0 errors, 0 warnings`;
- MT5 launch rc=0;
- one exact run `2021-01-03 -> 2026-08-01`, cold-start, first six months warm-up;
- tester-only/no-order/live guards PASS.

Preregistered primary:
`v46_hl10_thr0p05_breadth4`.

Breadth4 full cold-start:
- $40 -> $106.947120;
- +167.3678%;
- max MTM DD 16.5983%.

Evaluation:
- +167.367657% compounded;
- +21.344869% annualized;
- 825 trades;
- AvgR +0.144313R;
- SumR +119.05819R;
- PF 1.281739;
- 30 active months / 61;
- positive active-month ratio 66.67%;
- -0.05R/trade stress +77.80819R.

Calendar decomposition:
- 2021 Jul-Dec: 0.0%, 0 trades;
- 2022: -0.744202%, 32 trades;
- 2023: -0.810156%, 67 trades;
- 2024: +5.179345%, 83 trades;
- 2025: +42.785951%, 417 trades;
- 2026 Jan-Jul: +80.829731%, 226 trades.

Risk stability:
- worst full year -0.810156%;
- worst rolling-12m -1.946983%;
- 50/50 rolling-12m windows were not worse than -5%.

Formal analyzer status remains `HOLD` because the preregistered gate required >=75% of full calendar years to be nonnegative; breadth4 had 2/4 nonnegative full years. Do not retroactively relabel V46 as PASS.

However breadth4 passed the other 13/14 readiness checks. The two negative full years were only -0.74% and -0.81%, which is consistent with the preregistered crisis-regime objective of preserving capital rather than forcing positive PnL in every regime.

Common-window comparison, 2022-07 -> 2026-07:
- V45 HL10: +105.79%, DD 56.30%, PF 1.133, 1,556 trades, turnover 7267.77x start-$40;
- V46 breadth4: about +169.37%, DD 16.60%, PF 1.282, 793 trades, turnover about 6193.53x start-$40.

Breadth4 therefore reduced DD by about 70.5%, trade count by about 49.0%, turnover by about 14.8%, roughly doubled AvgR, and improved common-window compounded return.

Recent edge retention: 2025-08 -> 2026-07 breadth4 about +95.50% versus V45 about +138.29%. This is an acceptable return sacrifice relative to the large reduction in tail drawdown.

## Interpretation

Do not remove 2022/2024 from validation and do not hard-code war dates.

2022 was a conflicting-force crisis/transition regime; standing aside is acceptable. 2024 was a strong gold bull year, so V45's loss there represented a real routing weakness. Breadth4 repaired both in the desired way: almost no exposure in weak regimes, positive return in 2024, and strong participation in 2025-2026.

The correct objective is not positive PnL every year. It is capital preservation when internal ensemble health is weak plus strong edge capture when ensemble health is broad.

## Sensitivity

Breadth3 was too permissive: DD 31.91%, PF 1.194, worst year -13.19%, worst rolling-12m -16.42%.

Breadth5 was too restrictive: DD 15.14%, PF 1.236, no losing full years, but only +9.83% annualized and 20 active months.

This coherent sensitivity curve supports breadth4 as the frozen mechanism. Do not retune breadth count on the accepted V46 sample.

## Observability bug to fix before next run

V46 generated source defines `CANDIDATE_COUNT 26` and all V46 candidate ledgers are present, but the inherited manifest writer still reports stale metadata:
- `candidate_count=23`;
- `source_file=V38FastHarvestLab.mq5`.

This does not invalidate V46 economics, but it must be corrected before the next campaign.

## Next campaign

Do not run another same-sample breadth/threshold sweep.

V47 direction:
- freeze breadth4, HL10 and 0.05 thresholds;
- fix manifest identity/count metadata;
- collect fresh forward/shadow evidence;
- shadow-log post-hoc ADX/DI hypotheses without letting them control the primary decision;
- require a later fresh-evidence decision before any ADX/DI gate can become active;
- remain paper/research only, no real-money authorization.

Workspace: `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.
