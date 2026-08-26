# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V52R real-tick reproducibility is accepted. V53 short broker-DEMO confirmation is implemented and pending Windows compile/start.

Authoritative branch:
`agent/v53-trend-bos-demo-confirmation`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v52r_real_tick_results_2026-08-26.md`
3. `docs/adr/ADR-054-v53-selected-candidate-demo-confirmation.md`
4. `scripts/build_v53_trend_bos_demo_confirmation_source.py`
5. `runtime/v53_trend_bos_demo/RUN_V53_TREND_BOS_DEMO.py`
6. `runtime/v53_trend_bos_demo/SUPERVISE_V53_TREND_BOS_DEMO.py`
7. `runtime/v53_trend_bos_demo/START_V53_TREND_BOS_DEMO_GIT_BASH.sh`

## Accepted evidence

V50 execution plumbing ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`
Result: `EXECUTION_PIPELINE_PASS`.

V51 historical ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`
Result: `V51_KEEP_BREADTH4`.

Invalid generated-tick V52 ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`
Classification: `V52_RESULT=INVALID_DATA_CONTAMINATION`.

Accepted V52R real-tick ZIP SHA256:
`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`
Result: `V52R_CHALLENGER_SELECTED`.
Selected candidate: `v52_b4_or_b3_trend_bos`.

Clean V52R comparison:
- breadth4: 819 trades, PF 1.2894, annualized 21.47%, DD 16.60%, stress SumR +80.28R;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, DD 16.10%, stress SumR +80.30R.

## V53 contract

V53 confirms only the selected candidate on Exness DEMO using natural virtual intent. It does not run plumbing probes and does not retune alpha.

Generated forward candidate semantics:
- candidate index 26 in the V48 forward lineage;
- breadth >=4 path admitted;
- exactly breadth3 path admitted only when selected expert source mask contains TREND20_H1 or BOS_FVG_H1;
- book index 3 (`usd40_r1p0_cent_continuous`);
- magic `530053`.

Confirmation gate:
- at least 2 distinct market days;
- at least 1 broker-confirmed natural round trip;
- hard calendar stop 7 days;
- final flat state;
- inherited reject/duplicate/direction-mismatch/pending-timeout reconciliation checks.

Possible final verdicts:
- `DEMO_CONFIRMATION_PASS`;
- `HOLD`;
- `INSUFFICIENT_EXECUTION_SAMPLE`.

Safety:
- DEMO only;
- non-DEMO fails closed;
- DLL permission must be off;
- `real_money_authorized=0`;
- no execution-probe trades;
- no Martingale/grid/doubling/risk increase.

After Windows startup succeeds, do not run START again. Keep PC/Internet/MT5 running. Detached supervisor packages one ZIP under `runtime/v53_trend_bos_demo/OUTPUT_V53/` and records `LATEST_V53_ZIP.txt` after FINAL.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`V53_DEMO_CONFIRMATION=IMPLEMENTED_PENDING_WINDOWS_START`
