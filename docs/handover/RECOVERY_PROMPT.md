# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V52R real-tick reproducibility is accepted. The selected research candidate is `v52_b4_or_b3_trend_bos`; next task is short broker-DEMO confirmation only.

Authoritative branch for accepted V52R evidence:
`agent/v52r-real-tick-repro`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v50_execution_probe_results_2026-08-25.md`
3. `docs/research/v51_higher_frequency_results_2026-08-26.md`
4. `docs/research/v52_source_aware_results_2026-08-26.md`
5. `docs/research/v52r_real_tick_results_2026-08-26.md`
6. `docs/adr/ADR-052-source-aware-breadth3-opportunity-lane.md`
7. `docs/adr/ADR-053-real-tick-reproducibility-gate.md`

## Accepted V50 execution evidence

ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Result:
`EXECUTION_PIPELINE_PASS`

Three broker-DEMO round trips, six requests, zero rejects, final flat/no halt. Do not rerun plumbing probes.

## Accepted V51 evidence

ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Result:
`V51_KEEP_BREADTH4`

Broad/average-health breadth3 expansion increased frequency but failed DD/rolling guardrails.

## Invalid V52 generated-tick evidence

ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Classification:
`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not use its raw challenger selection as evidence.

## Accepted V52R real-tick evidence

ZIP SHA256:
`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Integrity:
- ZIP CRC PASS;
- manifest 20/20 PASS;
- run HEAD `718eb8c11dc801108695c73a58c692f55a108772`;
- source SHA256 `676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`;
- MetaEditor 0 errors / 0 warnings;
- tester `Model=4` real ticks;
- data integrity PASS: 263,052 rows, zero anomalies, max price ratio 1.079739, max absolute R 4.98223R.

Formal result:
`V52R_CHALLENGER_SELECTED`

Selected:
`v52_b4_or_b3_trend_bos`

Clean real-tick evaluation:
- breadth4: 819 trades, PF 1.2894, annualized 21.47%, DD 16.60%, stress SumR +80.28R;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, DD 16.10%, stress SumR +80.30R, worst rolling12 -4.68%.

Interpretation: candidate increases frequency materially without increasing DD. Friction-stressed SumR is essentially unchanged versus breadth4, so the promotion claim is frequency/robustness, not a large net-return uplift.

## Next task

Implement/run a short broker-DEMO confirmation of `v52_b4_or_b3_trend_bos` using inherited V50/V49 broker-adapter semantics.

Rules:
- DEMO account only;
- fail closed on non-DEMO, duplicate owned position, direction mismatch, pending timeout or reconciliation error;
- no alpha retuning;
- no V50 probe trades;
- broker orders only when the selected candidate creates natural virtual intent;
- collect status/events/transactions and one final ZIP;
- use the selected candidate as candidate under confirmation, while breadth4 remains historical fallback/reference.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`NEXT=SHORT_BROKER_DEMO_CONFIRMATION`
