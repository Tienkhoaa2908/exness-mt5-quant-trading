# Windows MT5 / Exness — V45 multi-year single-run workflow

Broker research environment: Exness Technologies Ltd.; symbol `XAUUSDm`; timeframe M15. REAL-MONEY LIVE TRADING is forbidden and `LIVE_AUTHORIZED=0`.

Canonical branch: `agent/v45-multiyear-single-run-validation`.
One-shot Git Bash bootstrap: `runtime/v45_multiyear_validation/BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh`.
Tracked Windows orchestrator: `runtime/v45_multiyear_validation/RUN_V45_MULTIYEAR_ONE_SHOT.py`.
Package-only recovery: `runtime/v45_multiyear_validation/PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh`.

## Purpose

V44 passed broad 2025-08 -> 2026-08 restart validation. V45 does not add alpha or retune parameters. It tests older regimes in one continuous exact Strategy Tester run while retaining monthly output for later analysis.

Frozen candidates:

- primary `adaptive_ewma_hl10_thr0p05`;
- return shadow `adaptive_ewma_hl8_thr0p05`;
- control `adaptive_ewma_hl8_thr0`.

## Tester protocol

One Strategy Tester invocation only:

- XAUUSDm;
- M15;
- Model=0;
- FromDate=2022.01.01;
- ToDate=2026.08.01;
- Deposit=40 USD;
- leverage 1:200;
- non-visual;
- `AllowLiveTrading=0`;
- `AllowDllImport=0`;
- terminal shutdown after completion.

The EA writes one continuous `monthly_summary.csv`, `trades.csv`, and `manifest.txt`. The analyzer later produces monthly, calendar-year, rolling 3/6/12-month, drawdown, PF and execution-friction reports. First six observed months are warm-up.

## Historical state / anti-look-ahead

Do not copy the accepted 2025-08 adaptive state into this 2022 run.

The tracked V45 orchestrator:

1. backs up the existing Common Files `v30_ml_dl_feature_lake_state.csv` if present;
2. deletes that state before tester launch;
3. starts from reset/cold adaptive scores;
4. preserves the post-run state as evidence;
5. restores the original pre-V45 state in a `finally` path.

Accepted V38 source was inspected: `LoadAdaptiveState()` calls `ResetAdaptiveScores()` before opening the state file; missing state returns false and initialization continues. Thus state-file absence is valid cold-start behavior.

## Source provenance

Accepted V38 ZIP SHA256:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Accepted V38 source SHA256:
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`

Frozen generated V45 source SHA256:
`36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`

V45 changes validation/output markers and expensive telemetry defaults only. Candidate catalog, entry/exit geometry, sizing and risk remain unchanged.

## Compile contract

MetaEditor return code is diagnostic only. Compile acceptance requires:

- installed source SHA = frozen V45 source SHA;
- final compiler summary `Result: 0 errors, 0 warnings`;
- non-empty EX5;
- compile-source hash marker or compile artifacts no older than installed source.

Valid compile artifacts are reused before any recompile.

## Recovery contract

Before a fresh run, close manually opened MetaTrader 5 and MetaEditor. Never use `git clean`.

Recovery ladder:
`provenance -> source -> compile -> MT5 -> collection -> analysis -> packaging`

V45 has one expensive tester invocation:

- `OUTPUT_V45/checkpoint/MT5_DONE.json` => tester already finished; collection-only, MT5 must not rerun;
- `OUTPUT_V45/checkpoint/DONE.txt` => tester outputs already collected; analysis/package only, MT5 must not rerun;
- completed bundle + ZIP failure => run package-only recovery.

MT5 completion requires a new `LATEST` run id plus complete `monthly_summary.csv`, `trades.csv`, `manifest.txt` and V45/tester/no-order safety markers. Terminal process return code alone is not completion evidence.

Packaging uses `scripts/package_research_bundle_portable.py`; never parse Git Bash/MSYS `sha256sum` manifest rendering.

## Interpretation

V45 analyzer can return `MULTIYEAR_ROBUSTNESS_PASS` or `HOLD` for the primary HL10 threshold0.05 candidate.

A V45 PASS advances paper/demo deployment validation and tester-vs-demo reconciliation. It does not authorize real-money live capital.

Expected ZIP:
`runtime/v45_multiyear_validation/OUTPUT_V45/v45_multiyear_single_run_validation.zip`

Upload only that ZIP for acceptance analysis.
