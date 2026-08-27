# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V52R real-tick reproducibility is accepted. V53 short broker-DEMO confirmation is active/timeboxed.

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

Normal confirmation gate:
- at least 2 distinct market days;
- at least 1 broker-confirmed natural round trip;
- EA hard calendar stop 7 days;
- final flat state;
- inherited reject/duplicate/direction-mismatch/pending-timeout reconciliation checks.

Possible EA final verdicts:
- `DEMO_CONFIRMATION_PASS`;
- `HOLD`;
- `INSUFFICIENT_EXECUTION_SAMPLE`.

## Timebox waiver rule

Operator decision dated 2026-08-27:

If no natural V53 round trip has occurred by the end of 2026-08-28 user-local date, do not extend the wait solely to obtain a sparse event.

Close the milestone as:
`V53_NO_SIGNAL_TIMEBOX_WAIVER`

Only do this if runtime evidence remains healthy and flat:
- heartbeat/status updating;
- `halted=0`;
- duplicate events = 0;
- direction mismatches = 0;
- open/close pending = 0;
- owned broker positions = 0;
- no reject attributable to a natural strategy request.

Do **not** call this `DEMO_CONFIRMATION_PASS`; no natural candidate-to-broker round trip was observed.

The waiver preserves these accepted facts:
- V52R selected `v52_b4_or_b3_trend_bos` on clean real ticks;
- V50 proved generic broker-DEMO open/close/reconciliation plumbing;
- the selected research candidate remains unchanged;
- the missing evidence is specifically the natural V53 integration event.

Do not restart V53, do not add V50-style synthetic probes, and do not retune alpha to force an entry.

If a natural round trip arrives before timebox closure and all checks are clean, use the normal `DEMO_CONFIRMATION_PASS` path.

Safety:
- DEMO only;
- non-DEMO fails closed;
- DLL permission must be off;
- `real_money_authorized=0`;
- no execution-probe trades;
- no Martingale/grid/doubling/risk increase.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`V53_TIMEBOX_DATE=2026-08-28`
`V53_DEMO_CONFIRMATION=RUNNING_OR_TIMEBOX_PENDING`
