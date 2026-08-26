# V52 Source-Aware Tournament — Invalidated Run

Date: 2026-08-26

## Uploaded bundle

ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Integrity of the archive itself is good:
- ZIP CRC PASS;
- internal SHA256 manifest 18/18 PASS;
- run HEAD `1ee7bd4de885335f3728b1e60b0c19929fbc04cb`;
- generated V52 source SHA256 `676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`;
- MetaEditor compile `0 errors, 0 warnings`.

The raw analyzer printed `V52_CHALLENGER_SELECTED` with `v52_b4_or_b3_trend_bos`. That selection is **not accepted** because the historical price stream is contaminated.

## Data anomaly

`trades.csv` contains impossible XAUUSDm exit prices around 30,000 while surrounding entries are around 1,865-1,897. Three distinct anomalous timestamps are present:

- `2023.01.13 00:48:32`, exit `30363.760`, affecting 12 rows;
- `2023.09.29 01:27:03`, exit `29846.016`, affecting 53 rows;
- `2023.10.18 01:04:18`, exit `30836.912`, affecting 9 rows.

The largest absolute trade result is about `13479R`. By contrast, the accepted V51 bundle contains zero trade price-ratio anomalies above 2x and its largest absolute trade result is below 5R.

The September anomaly directly destroys several control-expert books. Examples in the USD40 1% book include:
- EMA short around 1865.857 exiting at 29846.016: about `-13058R`;
- MACD short around 1865.276 exiting at 29846.016: about `-11721R`;
- slow momentum short around 1866.695 exiting at 29846.016: about `-13479R`.

## Why this invalidates V52 selection

Adaptive expert health is learned from control-expert trade outcomes. The impossible September tick therefore drives EMA/MACD/SLOW expert health sharply negative and changes the later breadth state.

This is visible in the supposedly unchanged breadth4 baseline:
- accepted V51 breadth4 evaluation trades: `825`;
- contaminated V52 breadth4 evaluation trades: `795`.

The V52 baseline is a strict subset of the V51 baseline with 30 trades missing, including all 24 breadth4 trades in October 2023 and all 5 in March 2024. Therefore the claim that V52 preserved the breadth4 path is not empirically satisfied in this run.

The source-aware candidates are also evaluated under the contaminated adaptive state, so the apparent `trend_bos` selection is biased and cannot be promoted.

## Decision

`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not promote any V52 candidate from this ZIP.

Do not change the source-aware hypothesis. The next action is a reproducibility rerun using the exact same V52 source under MetaTrader 5 `Model=4` (Every tick based on real ticks) plus an explicit post-run data-integrity gate. The rerun is called V52R and is not a new alpha search.
