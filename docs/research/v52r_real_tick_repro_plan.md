# V52R Real-Tick Reproducibility Plan

Date: 2026-08-26

## Purpose

V52R is a data-quality/reproducibility rerun, not a new alpha experiment.

The first V52 generated-tick run is invalid because three pathological XAUUSDm price excursions around 30,000 contaminated control-expert outcomes and adaptive health. V52R keeps the exact V52 source and candidate catalog frozen while changing only the MetaTrader 5 tester tick model from simulated Every Tick to Every tick based on real ticks (`Model=4`).

## Frozen source

Expected V52 source SHA256:
`676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`

Candidates remain:
- baseline `v46_hl10_thr0p05_breadth4`;
- `v52_b4_or_b3_trend`;
- `v52_b4_or_b3_bos`;
- `v52_b4_or_b3_trend_bos`.

No V52 threshold, source mask, exit rule, risk or sizing rule changes in V52R.

## Tester protocol

One exact MT5 run:
- XAUUSDm M15;
- 2021-01-03 -> 2026-08-01;
- cold start;
- first 6 months warm-up;
- USD40 continuous 1% virtual-risk book;
- leverage 1:200;
- `Model=4` real ticks;
- native/external broker orders disabled;
- one final ZIP.

The first real-tick download may take materially longer than prior generated-tick runs.

## Data-integrity gate

Before interpreting alpha, scan every trade row.

Require:
- finite positive entry and exit prices;
- `max(entry/exit, exit/entry) <= 1.25`;
- `abs(r_multiple) <= 10`;
- zero violating rows.

Accepted V51 was comfortably inside these sentinels (max price ratio about 1.08; max absolute R below 5). The invalid V52 generated-tick run reached about 16x and more than 13,000R.

If any anomaly remains:
`STATUS=V52R_DATA_INTEGRITY_FAIL`

No candidate may be selected from such a run.

## Selection

If data integrity passes, apply the existing ADR-052 V52 guardrails relative to the breadth4 baseline from this same real-tick run.

Possible results:
- `V52R_CHALLENGER_SELECTED`;
- `V52R_KEEP_BREADTH4`;
- `V52R_DATA_INTEGRITY_FAIL`.

If a challenger is selected, perform only a short broker-DEMO confirmation next; do not rerun V50 plumbing probes.
