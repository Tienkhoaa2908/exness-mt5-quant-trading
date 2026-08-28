# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V53 waiting gate is closed by a documented no-signal timebox waiver. The current research/DEMO candidate is `v52_b4_or_b3_trend_bos`.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v52r_real_tick_results_2026-08-26.md`
3. `docs/research/v53_timebox_waiver_results_2026-08-28.md`
4. `docs/adr/ADR-054-v53-selected-candidate-demo-confirmation.md`
5. `docs/adr/ADR-055-immutable-snapshot-evidence-packaging.md`

## Accepted evidence

V50 execution plumbing:
- ZIP SHA256 `587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`;
- result `EXECUTION_PIPELINE_PASS`;
- three broker-DEMO round trips, six requests, zero rejects;
- do not rerun synthetic plumbing probes.

V52R real-tick selection:
- ZIP SHA256 `4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`;
- result `V52R_CHALLENGER_SELECTED`;
- selected `v52_b4_or_b3_trend_bos`;
- 951 eval trades vs breadth4 819 (+16.12%);
- PF 1.2649;
- annualized 22.17%;
- max MTM DD 16.10%;
- data-integrity PASS on real ticks.

V53 no-signal waiver:
- run id `v53_trend_bos_demo_confirmation_v1__XAUUSDm__PERIOD_M15__2026-08-27_04-06-43__708359`;
- original waiver ZIP SHA256 `b6118b928cafc5528b0dab04cf01f3022cc21a0df693e4acbfcd04048c80da8a`;
- original ZIP CRC PASS but manifest 16/17 due one mutable-status packaging race;
- recovered accepted ZIP SHA256 `602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`;
- recovered CRC PASS and manifest 19/19 PASS;
- runtime evidence bytes unchanged; original manifest retained.

V53 waiver status:
- DEMO;
- market days 2;
- round trips 0;
- requests/rejects 0/0;
- duplicate events 0;
- direction mismatches 0;
- no pending request;
- no owned position;
- halted 0;
- final virtual/broker state flat;
- real money authorized 0.

Formal classification:
`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

Do not relabel this as `DEMO_CONFIRMATION_PASS`. The natural selected-candidate broker mapping remains unobserved. The gate is nevertheless closed: do not keep waiting or force a signal.

## Artifact rule

Future forward-runtime packagers must use immutable snapshot semantics before hashing/zipping. Do not hash live mutable status files and then ZIP them later. See ADR-055.

## Current classification

`V50_EXECUTION_PIPELINE=PASS`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`
`V53_NATURAL_MAPPING=NOT_OBSERVED`

## Next task

Freeze the selected candidate and move on from V53. Do not retune breadth/source thresholds because of the no-signal timebox. Any future DEMO forward runtime may naturally collect the missing mapping evidence as part of normal operation, but it must not be represented as already observed.
