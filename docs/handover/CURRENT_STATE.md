# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-26

## Project objective

The project targets production/live deployment after sufficient evidence. Broker-DEMO execution plumbing is already qualified; the active research problem is increasing signal frequency without giving back the drawdown/stability benefit of breadth4.

## Inherited baseline

Current reference candidate:
`v46_hl10_thr0p05_breadth4`

Accepted V46 evidence remains historical `STATUS=HOLD` because one preregistered full-year sign gate failed, but breadth4 materially improved drawdown/PF versus the previous router and remains the baseline for challenger research.

## V50 execution qualification — ACCEPTED

Accepted recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Authoritative raw EA FINAL:
- `verdict=EXECUTION_PIPELINE_PASS`;
- `probe_round_trips=3`;
- `probe_requests=6`;
- `probe_rejects=0`;
- final flat / no halt.

Conclusion:
`V50_EXECUTION_PIPELINE=PASS`

Do not repeat V50 plumbing probes.

## V51 higher-frequency tournament — ACCEPTED

Accepted ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Integrity:
- ZIP CRC PASS;
- manifest 17/17 PASS;
- run HEAD `8c211b27e6676f3176e089a619679e6af263e3fd`;
- source SHA256 `927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6`;
- MetaEditor `0 errors, 0 warnings`.

Formal result:
`V51_KEEP_BREADTH4`

Baseline breadth4:
- 825 eval trades;
- AvgR +0.1443R;
- PF 1.2817;
- annualized +21.34%;
- max MTM DD 16.60%;
- worst rolling12 -1.95%.

V51 average-health challengers increased trade count materially but failed DD/rolling-stability guardrails. Diagnostic decomposition found the incremental breadth3 lane positive for `TREND20_H1` and `BOS_FVG_H1`, negative for EMA/MACD/SLOW_MOM. This same-sample diagnostic motivated V52.

See `docs/research/v51_higher_frequency_results_2026-08-26.md`.

## V52 generated-tick run — INVALID DATA

Uploaded V52 ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Archive integrity itself:
- ZIP CRC PASS;
- manifest 18/18 PASS;
- run HEAD `1ee7bd4de885335f3728b1e60b0c19929fbc04cb`;
- exact generated V52 source SHA256 `676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`;
- MetaEditor compile `0 errors, 0 warnings`.

The raw analyzer printed:
`V52_CHALLENGER_SELECTED / v52_b4_or_b3_trend_bos`

This selection is **rejected** because `trades.csv` contains pathological XAUUSDm prices around 30,000 while surrounding entries are around 1,900:
- 2023-01-13 exit `30363.760` — 12 anomalous rows;
- 2023-09-29 exit `29846.016` — 53 anomalous rows;
- 2023-10-18 exit `30836.912` — 9 anomalous rows.

Maximum absolute trade result exceeds 13,000R. Accepted V51 had zero >2x entry/exit price-ratio anomalies and max absolute R below 5R.

The September bad tick catastrophically affects EMA/MACD/SLOW control experts and therefore contaminates adaptive health. Evidence of downstream contamination: the supposedly unchanged breadth4 baseline falls from 825 eval trades in V51 to 795 in V52, with 30 previously present breadth4 trades missing.

Formal classification:
`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not promote any V52 candidate from that ZIP.

See `docs/research/v52_source_aware_results_2026-08-26.md`.

## Current milestone — V52R real-tick reproducibility

Branch:
`agent/v52r-real-tick-repro`

V52R is **not a new alpha search**. It reuses the exact V52 source SHA:
`676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`

Only the tester data model changes:
- prior V52: `Model=0` simulated Every Tick;
- V52R: `Model=4` Every tick based on real ticks.

The source-aware candidate catalog and ADR-052 guardrails remain frozen.

V52R adds a fail-closed data-integrity gate before any selection:
- finite positive entry/exit;
- max entry/exit price ratio <=1.25;
- max absolute trade result <=10R;
- zero violating rows.

Possible statuses:
- `V52R_CHALLENGER_SELECTED`;
- `V52R_KEEP_BREADTH4`;
- `V52R_DATA_INTEGRITY_FAIL`.

A data-integrity failure is not an alpha failure and must not trigger threshold tuning.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`
`V52R_REAL_TICK_REPRO=IMPLEMENTED_PENDING_WINDOWS_RUN`
