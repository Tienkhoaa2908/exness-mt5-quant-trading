# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-28

## Project objective

The project targets production/live deployment after sufficient evidence. Current work is candidate qualification and operational evidence. No current artifact authorizes real-money execution.

## Accepted evidence chain

### V50 execution plumbing — PASS
Accepted recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Authoritative result:
`EXECUTION_PIPELINE_PASS`

Three completed XAUUSDm DEMO round trips, six requests, zero rejects, final flat/no halt. Do not rerun V50 probe trades.

### V51 higher-frequency tournament — KEEP BREADTH4
Accepted ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Formal result:
`V51_KEEP_BREADTH4`

Broad breadth3 expansion increased frequency but violated drawdown/rolling-stability guardrails. Same-sample diagnostics motivated a source-aware TREND/BOS lane.

### V52 generated-tick run — INVALID DATA
ZIP SHA256:
`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Formal classification:
`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not use its raw challenger selection.

### V52R real-tick reproducibility — PASS
Accepted ZIP SHA256:
`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Formal result:
`V52R_CHALLENGER_SELECTED`

Selected research candidate:
`v52_b4_or_b3_trend_bos`

Clean real-tick comparison:
- breadth4: 819 trades, PF 1.2894, annualized 21.47%, max MTM DD 16.60%, stress SumR +80.28R;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, max MTM DD 16.10%, stress SumR +80.30R, worst rolling12 -4.68%.

Interpretation: selected candidate increases frequency materially without giving back drawdown. Friction-stressed return is essentially flat versus breadth4, so do not describe it as a large net-return improvement.

## V53 natural broker-DEMO confirmation — CLOSED BY WAIVER

Run id:
`v53_trend_bos_demo_confirmation_v1__XAUUSDm__PERIOD_M15__2026-08-27_04-06-43__708359`

Original waiver ZIP SHA256:
`b6118b928cafc5528b0dab04cf01f3022cc21a0df693e4acbfcd04048c80da8a`

The original ZIP CRC passed, but its manifest was 16/17 because the live status file updated during the packaging window. This was an artifact-generation race, not an execution/strategy failure.

Coordinator-recovered accepted ZIP SHA256:
`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

Recovered integrity:
- ZIP CRC PASS;
- manifest 19/19 PASS;
- original manifest retained;
- runtime evidence bytes unchanged;
- recovery provenance explicit.

Observed V53 status at waiver:
- DEMO account;
- real money authorized 0;
- market days 2;
- round trips 0;
- requests 0;
- rejects 0;
- duplicate events 0;
- direction mismatches 0;
- open/close pending 0;
- halted 0;
- owned broker positions 0;
- virtual position flat;
- DLL permission off;
- MetaEditor compile 0 errors / 0 warnings.

Formal classification:
`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

This is **not** `DEMO_CONFIRMATION_PASS`. Natural selected-candidate broker mapping was not observed because no qualifying natural signal occurred within the timebox.

Accepted interpretation:
- generic broker-DEMO execution plumbing remains PASS from V50;
- selected alpha candidate remains accepted from V52R;
- V53 showed no execution fault but produced no natural order attempt;
- the waiting gate is closed and must not be extended merely to obtain a rare event;
- breadth4 remains historical fallback/reference.

See:
- `docs/research/v53_timebox_waiver_results_2026-08-28.md`;
- `docs/adr/ADR-055-immutable-snapshot-evidence-packaging.md`.

## Current classification

`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`
`V52R_REAL_TICK_REPRO=PASS`
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`
`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`
`V53_NATURAL_MAPPING=NOT_OBSERVED`

## Next milestone

Freeze `v52_b4_or_b3_trend_bos` as the current research/DEMO candidate and stop threshold tuning. Any next runtime should inherit immutable snapshot packaging and should not rerun V50 synthetic execution probes. Natural broker mapping remains an explicit evidence gap rather than a reason to keep an idle qualification campaign open indefinitely.
