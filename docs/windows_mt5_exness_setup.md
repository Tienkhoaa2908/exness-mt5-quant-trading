# Windows MT5 / Exness — V44 baseline robustness workflow

Broker research environment: Exness Technologies Ltd.; symbol `XAUUSDm`; timeframe M15. REAL-MONEY LIVE TRADING is forbidden.

Canonical branch: `agent/v44-baseline-robustness-validation`.
One-shot bootstrap: `runtime/v44_baseline_validation/BOOTSTRAP_V44_BASELINE_VALIDATION_ONE_SHOT_GIT_BASH.sh`.
Package-only recovery: `runtime/v44_baseline_validation/PACKAGE_V44_EXISTING_OUTPUT_GIT_BASH.sh`.

## V44 purpose

V44 does not add a new alpha layer and does not retune parameters. It broadly validates the frozen baseline family before deployment escalation:

- `adaptive_ewma_hl8_thr0`;
- `adaptive_ewma_hl8_thr0p05`;
- `adaptive_ewma_hl10_thr0p05`.

The campaign runs 19 exact Strategy Tester windows: 12 independent months, 4 quarter blocks, 2 half-years and 1 annual window. Each window restarts from the accepted 2025-08 state. The annual window runs first and must exactly reproduce the accepted control before the other 18 windows are allowed to execute.

## Exact annual reproduction gate

The annual 2025-08-01 -> 2026-08-01 run must reproduce:

- end `$107.432645`;
- 563 control trades;
- the accepted 12-month trade-count vector;
- the accepted 12-month final-balance vector.

V44 uses XAUUSDm / M15 / Model=0 / Deposit=$40 / leverage 1:200 / non-visual Strategy Tester.

## Source and compile rules

V44 is built only from accepted V38 exact bundle SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b` and accepted V38 parent source SHA256 `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

Frozen generated V44 source SHA256:

`cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3`

V44 changes output/release markers and disables expensive telemetry only. Strategy catalog, entry/exit logic, sizing and risk are unchanged.

Compile success is determined by exact source SHA + final `Result: 0 errors, 0 warnings` + non-empty EX5. MetaEditor process return code alone is not acceptance evidence.

## Windows recovery rules

Before a new clean execution, close manually opened MT5 and MetaEditor.

Do not use `git clean`.

Use the recovery ladder in `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`:

`provenance -> source -> compile -> MT5 -> collection -> analysis -> packaging`

Important invariants:

- explicit UTF-8 (`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`);
- no runtime-generated/self-modifying shell runner;
- no `set +e` under the global `ERR` trap;
- Windows process rc is captured with `if command; then rc=0; else rc=$?; fi`;
- MT5 completion requires a new `LATEST` run plus complete manifested outputs;
- `MT5_DONE.txt` permits collection-only recovery;
- `DONE.txt` means that window must not rerun MT5;
- packaging uses `scripts/package_research_bundle_portable.py`, not platform-specific `sha256sum` manifest parsing;
- if all exact evidence already exists and packaging alone fails, use package-only recovery. MT5 must not rerun.

## Readiness interpretation

V44 analyzer can return `PAPER_DEMO_READY` or `HOLD`.

A `PAPER_DEMO_READY` result permits the next paper/demo deployment-validation stage only. It does not authorize live capital. `LIVE_AUTHORIZED=0` remains mandatory and research risk remains <=1.00%/trade.

Expected output:

`runtime/v44_baseline_validation/OUTPUT_V44/v44_baseline_robustness_validation.zip`

Upload only that ZIP for acceptance analysis.
