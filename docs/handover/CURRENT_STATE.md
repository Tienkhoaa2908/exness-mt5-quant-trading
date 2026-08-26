# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-26

## Project objective

The project targets production/live deployment after sufficient evidence. Broker-DEMO execution plumbing is qualified; the active candidate-development problem is increasing signal frequency without giving back the drawdown/stability benefit of breadth4.

## Accepted execution plumbing

V50 recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Authoritative result:
`EXECUTION_PIPELINE_PASS`

Evidence: three completed XAUUSDm DEMO round trips, six requests, zero rejects, final flat/no halt. Do not rerun V50 plumbing probes.

## Accepted V51 historical result

ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Formal result:
`V51_KEEP_BREADTH4`

Breadth4 baseline: 825 eval trades, AvgR +0.1443R, PF 1.2817, annualized +21.34%, max MTM DD 16.60%, worst rolling12 -1.95%.

V51 broad/average-health breadth3 expansion increased frequency by roughly 27%-35% but raised DD to roughly 25%-29% and breached rolling-stability guardrails. Post-run diagnostic decomposition found positive incremental breadth3 edge in `TREND20_H1` and `BOS_FVG_H1`, negative incremental edge in EMA/MACD/SLOW_MOM. That diagnostic motivated V52 source-aware research.

## V52 generated-tick run — INVALID

Uploaded V52 ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Archive integrity passed, but `trades.csv` contained pathological XAUUSDm generated prices near 30,000 while surrounding prices were near 1,900. Maximum absolute trade result exceeded 13,000R and the supposedly unchanged breadth4 baseline fell from 825 to 795 eval trades due contaminated adaptive state.

Formal classification:
`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not promote any candidate from the generated-tick V52 ZIP.

## V52R real-tick reproducibility — ACCEPTED

Accepted ZIP SHA256:
`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Integrity:
- ZIP CRC PASS;
- manifest 20/20 PASS;
- run HEAD `718eb8c11dc801108695c73a58c692f55a108772`;
- exact V52 source SHA256 `676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`;
- MetaEditor `0 errors, 0 warnings`;
- tester `Model=4` real ticks;
- cold start, six-month warm-up, XAUUSDm M15, 2021-01-03 -> 2026-08-01.

Data-integrity gate:
- 263,052 trade rows checked;
- 0 anomaly rows;
- max entry/exit price ratio 1.079739 <= 1.25;
- max absolute trade result 4.98223R <= 10R.

Real-tick breadth4 baseline is materially reproducible versus V51: 819 eval trades versus 825 (`-0.73%`), AvgR +0.1480R, PF 1.2894, annualized +21.47%, max MTM DD 16.60%, worst rolling12 -1.95%.

Formal result:
`V52R_CHALLENGER_SELECTED`

Selected research candidate:
`v52_b4_or_b3_trend_bos`

Clean real-tick comparison:
- breadth4 baseline: 819 trades, PF 1.2894, annualized 21.47%, DD 16.60%, stress SumR +80.28R;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, DD 16.10%, stress SumR +80.30R, worst rolling12 -4.68%.

TREND+BOS passes all preregistered ADR-052 challenger guardrails and is selected by the frozen utility rule. The claim is specifically **higher frequency without giving back DD**; friction-stressed SumR is essentially flat versus breadth4, so do not describe this as a large friction-adjusted return improvement.

See `docs/research/v52r_real_tick_results_2026-08-26.md`.

## Next milestone

Promote `v52_b4_or_b3_trend_bos` to a short broker-DEMO confirmation only.

Constraints:
- no new alpha threshold tuning;
- no V50 plumbing-probe rerun;
- preserve DEMO-only account guard and fail-closed reconciliation;
- use the already-qualified broker execution adapter semantics;
- confirm natural virtual intent from the selected candidate can open/close and reconcile at the broker;
- keep breadth4 as fallback if forward confirmation exposes execution/signal mismatch.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`NEXT=SHORT_BROKER_DEMO_CONFIRMATION`
