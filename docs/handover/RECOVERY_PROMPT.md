# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V51 accepted; next experiment is V52 source-aware higher-frequency challenger.

Authoritative accepted V51 branch:
`agent/v51-higher-frequency-challenger`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v50_execution_probe_results_2026-08-25.md`
3. `docs/research/v51_higher_frequency_results_2026-08-26.md`
4. `docs/adr/ADR-051-higher-frequency-hybrid-challenger.md`

## Accepted V50 evidence

Recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Raw EA FINAL:
`EXECUTION_PIPELINE_PASS`

Do not rerun V50 plumbing probes.

## Accepted V51 evidence

ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Integrity:
- ZIP CRC PASS;
- manifest 17/17 PASS;
- run HEAD `8c211b27e6676f3176e089a619679e6af263e3fd`;
- MetaEditor 0 errors / 0 warnings.

Formal result:
`V51_KEEP_BREADTH4`

The three average-health breadth3 challengers increased trades by ~27%-35%, but max MTM DD rose to ~25%-29% and worst rolling12 fell below -10%; none is promotable.

## Diagnostic direction for V52

Do not perform another average-health threshold sweep.

Same-sample decomposition of V51 incremental breadth3 trades shows stable source separation across the three V51 thresholds:
- positive: `TREND20_H1`, `BOS_FVG_H1`;
- negative: `EMA_H1`, `MACD_H1`, `SLOW_MOM_16H24H`.

This diagnostic is not itself promotable. Use it only to preregister one small source-aware tournament.

V52 design principle:
- preserve breadth>=4 baseline behavior;
- when healthy breadth ==3, allow only selected expert source masks corresponding to TREND20_H1 and/or BOS_FVG_H1;
- no broad tuning;
- no Martingale/grid;
- no execution-plumbing rerun;
- keep breadth4 if source-aware variants fail risk/stability guardrails.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=NEXT`
