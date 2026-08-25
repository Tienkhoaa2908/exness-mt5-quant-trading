# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V52 source-aware higher-frequency challenger tournament.

Authoritative branch:
`agent/v52-source-aware-challenger`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v50_execution_probe_results_2026-08-25.md`
3. `docs/research/v51_higher_frequency_results_2026-08-26.md`
4. `docs/adr/ADR-052-source-aware-breadth3-opportunity-lane.md`
5. `docs/research/v52_source_aware_plan.md`
6. `runtime/v52_source_aware/START_V52_SOURCE_AWARE_GIT_BASH.sh`

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

V51 average-health challengers increased trade frequency materially but failed drawdown and rolling-12-month stability guardrails.

## V52 design

Accepted V51 source parent SHA256:
`927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6`

Baseline:
`v46_hl10_thr0p05_breadth4`

Challengers:
- `v52_b4_or_b3_trend`;
- `v52_b4_or_b3_bos`;
- `v52_b4_or_b3_trend_bos`.

At breadth>=4 the inherited path is preserved. At exactly breadth3, V52 filters the selected expert by source mask. V52 does not add another average-health threshold.

Guardrails:
- >=5% trade-count increase;
- max MTM DD <=20%;
- DD increase <=3 points;
- PF >=1.20 and >=95% baseline;
- AvgR >=0.10R and >=75% baseline;
- annualized >=10%;
- friction-stressed SumR positive;
- worst full year >=-10%;
- worst rolling12 >=-10%.

Possible result:
- `V52_CHALLENGER_SELECTED`;
- `V52_KEEP_BREADTH4`.

## User workflow

Close MT5 and MetaEditor before the tester run. Run the canonical V52 Git Bash block supplied by the coordinator.

After completion upload one file only:
`runtime/v52_source_aware/OUTPUT_V52/v52_source_aware_tournament.zip`

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=IMPLEMENTED_PENDING_WINDOWS_RUN`
