# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current state

Accepted V46 evidence commit:
`655bf2f77503d91d0749d2f5c99cc0ad8678c388`.

Accepted V46 ZIP SHA256:
`ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.

Formal V46 result: `HOLD`.

Current follow-up branch:
`agent/v47-forward-regime-shadow`.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v46_expert_breadth_results.md`
3. `docs/research/v46_expert_breadth_walkforward_plan.md`
4. `docs/research/v46_posthoc_regime_diagnostics.md`
5. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

Never `git clean`.

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Research stop-risk <=1.00%/trade. No Martingale/grid/doubling. Native/external broker orders remain forbidden. Exact historical tests use `AllowLiveTrading=0`, `AllowDllImport=0`. `LIVE_AUTHORIZED=0`.

## V46 accepted evidence

One exact XAUUSDm M15 Strategy Tester run, 2021-01-03 -> 2026-08-01, $40 USD, 1:200, cold-start, first six months warm-up.

Integrity/provenance PASS:
- CRC PASS;
- internal SHA manifest 24/24 PASS;
- run HEAD `655bf2f77503d91d0749d2f5c99cc0ad8678c388`;
- V38 parent SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- compile 0/0;
- MT5 rc=0;
- tester-only/no-order/live guards PASS.

Preregistered primary `v46_hl10_thr0p05_breadth4`:
- full cold-start $40 -> $106.947120 (+167.37%);
- max MTM DD 16.5983%;
- annualized 21.3449%;
- PF 1.281739;
- 825 evaluation trades;
- AvgR 0.144313R;
- SumR 119.05819R;
- worst full year -0.8102%;
- worst rolling-12m -1.9470%;
- -0.05R/trade stress +77.80819R.

Years:
- 2022 -0.7442%;
- 2023 -0.8102%;
- 2024 +5.1793%;
- 2025 +42.7860%;
- 2026 Jan-Jul +80.8297%.

Formal HOLD is caused only by the preregistered `>=75% full years nonnegative` gate: 2/4 full years were nonnegative. The other 13 readiness checks passed. Do not rewrite the formal result after the fact.

Engineering interpretation: breadth4 successfully converts weak regimes from large drawdowns into near-flat years while preserving substantial 2025-2026 edge. Another same-sample breadth/threshold sweep is not justified.

## Important comparison

Common 2022-07 -> 2026-07 window:
- V45 HL10: +105.79%, DD 56.30%, PF 1.133, 1,556 trades;
- V46 breadth4: about +169.37%, DD 16.60%, PF 1.282, 793 trades.

Breadth4 is the frozen leading mechanism for future validation.

## Market-regime interpretation

Do not exclude crisis years and do not hard-code war/news dates.

2022 can legitimately be a low-exposure crisis/transition year. 2024 cannot be excused as untradeable because gold was strongly directional; V46 repaired the 2024 loss while reducing exposure in weak periods.

Post-hoc V45 ADX/DI findings are research-only. They may be logged in shadow form during V47 but must not control the primary breadth4 decision until fresh evidence exists.

## Observability bug

V46 MQL correctly defines 26 candidates, but inherited manifest metadata is stale:
- `candidate_count=23`;
- `source_file=V38FastHarvestLab.mq5`.

Fix this before the next evidence-producing run. Do not rerun V46 merely to fix metadata.

## V47 direction

Use fresh forward/shadow evidence, not another optimization on 2021-2026.

Freeze:
- breadth4;
- HL10;
- selected score threshold 0.05;
- breadth health threshold 0.05;
- entry/exit/risk geometry.

V47 should:
- correct manifest identity/count;
- log ensemble breadth and selected score at each opportunity;
- shadow-log ADX<=30 and DI direction-alignment decisions without using them to gate primary trades;
- keep paper/research only;
- make no real broker orders;
- preserve exact recovery/checkpoint discipline.

## Runtime

Workspace: `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.
