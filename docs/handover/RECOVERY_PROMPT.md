# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V52 generated-tick result invalidated; current task is V52R real-tick reproducibility.

Authoritative branch:
`agent/v52r-real-tick-repro`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v50_execution_probe_results_2026-08-25.md`
3. `docs/research/v51_higher_frequency_results_2026-08-26.md`
4. `docs/research/v52_source_aware_results_2026-08-26.md`
5. `docs/adr/ADR-052-source-aware-breadth3-opportunity-lane.md`
6. `docs/adr/ADR-053-real-tick-reproducibility-gate.md`
7. `docs/research/v52r_real_tick_repro_plan.md`
8. `runtime/v52r_real_tick/START_V52R_REAL_TICK_GIT_BASH.sh`

## Accepted V50 evidence

Recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Raw EA FINAL:
`EXECUTION_PIPELINE_PASS`

Do not rerun V50 plumbing probes.

## Accepted V51 evidence

ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Formal result:
`V51_KEEP_BREADTH4`

Accepted V51 breadth4 evaluation trades: 825. Accepted V51 has no >2x entry/exit price-ratio anomaly and max absolute trade R is below 5R.

## Invalid V52 evidence

Uploaded ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Archive CRC/manifest/compile are valid, but the historical trade stream is not.

Pathological exits appear at:
- `2023.01.13 00:48:32` -> `30363.760`;
- `2023.09.29 01:27:03` -> `29846.016`;
- `2023.10.18 01:04:18` -> `30836.912`.

The September event produces losses above 10,000R in EMA/MACD/SLOW controls and contaminates adaptive health. The breadth4 baseline changes from 825 accepted V51 trades to 795 in V52.

Therefore:
`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not promote `v52_b4_or_b3_trend_bos` from the invalid V52 ZIP.

## V52R contract

V52R reuses the exact V52 source SHA256:
`676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`

No alpha/risk/threshold/source-mask changes are permitted.

Tester change only:
`Model=4` (Every tick based on real ticks).

Data-integrity gate before selection:
- finite positive entry/exit;
- max price ratio <=1.25;
- max absolute trade R <=10;
- zero violating rows.

Possible final statuses:
- `V52R_CHALLENGER_SELECTED`;
- `V52R_KEEP_BREADTH4`;
- `V52R_DATA_INTEGRITY_FAIL`.

If data integrity fails, do not tune alpha. Diagnose/repair history instead.

## User workflow

Close MT5 and MetaEditor, run the canonical V52R Git Bash bootstrap, then upload exactly:
`runtime/v52r_real_tick/OUTPUT_V52R/v52r_real_tick_repro.zip`

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`
`V52R_REAL_TICK_REPRO=IMPLEMENTED_PENDING_WINDOWS_RUN`
