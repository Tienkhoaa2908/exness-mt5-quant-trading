# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Current source of truth

Branch: `agent/v42-baseline-router-exact-mt5`.
Base: V41 implementation `60cd93ad9eefd07447f65b2e6909a20edf60f3ae`. V41 is closed HOLD; user ZIP SHA `f7e508816f96cb033f327582013fc0cf3c8583693b820c445de9c7156f469f7f`.
Use explicit Windows refspec and reset to remote. Never `git clean`; V30/V34/V36/V38 evidence, compiled EA artifacts, checkpoints, state and `.venv` may be untracked.

## Safety

REAL-MONEY LIVE TRADING forbidden. Research risk <=1.00%/trade. No Martingale/grid/doubling. V42 uses Strategy Tester config with `AllowLiveTrading=0`, `AllowDllImport=0`, Model=0 and shutdown-on-completion. No native/external broker orders.

## Baseline

Exact accepted `adaptive_ewma_hl8_thr0`: USD40 continuous, 2025-08-01 -> 2026-08-01, $40 -> $107.432645, about 8.58% geometric/month, DD about 9.90%, 563 trades. Target 15%/month remains unmet.
Hard reproduction vectors in `scripts/analyze_v42_baseline_router_mt5.py` must not be weakened: all 12 monthly trade counts and 12 final balances from V38.

## V42 design

Do not add V41 overlays or retune old router half-lives/thresholds. Existing exact router variants are historical comparators.
New candidates only: `v42_hl8_switch15m`, `v42_hl8_switch30m`, `v42_hl8_thr0p05_switch15m`, `v42_hl10_thr0p05_switch15m`, `v42_hl12_thr0p05_switch15m`, `v42_cp_fast5_slow20_switch15m`.
Builder clones exact parent `SetupAdaptiveRouter` arguments and adds direction-switch hysteresis only. Expert signals, entry/exit geometry, USD40 accounting and risk remain frozen. V38 M1/M15 telemetry defaults are disabled for runtime efficiency.

## Immutable V38 parent rule

Do not reconstruct V42 parent source through V30 -> V34 -> V38. Historical builder byte identity drift was observed on 2026-08-21: current V34 reconstruction produced `228b3ec7...`, while a stale V42 runner expected `8bae2c56...`. The safe fix is not to bless the new hash.

Use only accepted V38 exact-MT5 bundle:

`runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`

Expected SHA256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Runner must verify outer SHA, CRC-test ZIP, extract exactly one `V38FastHarvestLab.base.a.mq5`, validate V38 release/tester/router markers, then build V42 from those bytes. V34 specialist tape SHA and frozen state SHA remain mandatory runtime dependencies.

## Historical runner defects already diagnosed

### Windows UTF-8

A retry stopped because Windows Python decoded UTF-8 shell source with CP1252. All V42 static-test text reads are explicit UTF-8. Bootstrap/direct/resume export `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.

### Bash ERR trap

A retry stopped because `set +e` does not suppress a global Bash `ERR` trap. Do not reintroduce `set +e` around MetaEditor or MT5. Capture Windows process rc only in `if command; then rc=0; else rc=$?; fi` conditional context.

### Runtime patcher architecture removed

Do not recreate `scripts/patch_v42_metaeditor_runner.py`, generated shell runners, or self-modifying runtime shell. Successful V32/V34/V38 workflows use a direct tracked runner. V42 now follows that structure directly and static tests compare the V42 runner shape against those successful historical runners.

### MetaEditor compile artifact race — latest incident

The 2026-08-21 20:12 retry passed all 15 static gates, accepted V38 parent checks, deterministic V42 source generation and generated-MQL lint. MetaEditor launch returned rc=1. The then-current runner waited for an adjacent compile log, decided it was missing, then diagnostic `ls` immediately showed:

- `V42BaselineRouterLab.mq5` size 98214;
- `V42BaselineRouterLab.log` size 3298;
- `V42BaselineRouterLab.ex5` size 97958.

This proves compile artifacts were created and the failure was a fixed-deadline race in the runner, not a strategy failure. Strategy Tester had not launched, so there is still no V42 PnL.

## Canonical full-run architecture

`runtime/v42_baseline_router_exact_mt5/BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh`

Bootstrap now syntax-checks and executes the tracked direct runner. No runtime patch generation.

`runtime/v42_baseline_router_exact_mt5/RUN_V42_BASELINE_ROUTER_EXACT_MT5_GIT_BASH.sh`

Compile behavior:

- preserve installed V42 `.mq5` when its SHA already equals newly generated V42 source SHA;
- before deleting anything, attempt `compile_checkpoint_valid` using source SHA + compiler final `Result: 0 errors, 0 warnings` + EX5;
- accept a prior source-hash marker, or for one-time recovery require `.log` and `.ex5` timestamps not older than the exact source;
- on fresh compile, poll the combined log + final Result + EX5 postcondition rather than a single file-existence deadline;
- never define compile success from MetaEditor launcher rc alone.

MT5 behavior:

- conditional rc capture, no `set +e`;
- new `LATEST` run id/folder is the execution postcondition, not launcher rc alone;
- output collection must wait for complete monthly summary, trades and manifest safety markers before analysis.

Static test suite runs `bash -n` on bootstrap, direct runner and resume runner before any MetaEditor/MT5 execution in a clean full run.

## Immediate recovery: reuse the already compiled V42 EA

For the current machine state, do **not** compile V42 again first.

Use:

`runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`

Resume contract:

- does not reference or launch MetaEditor at all;
- installed source must hash exactly to `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`;
- existing `V42BaselineRouterLab.log` must end with `Result: 0 errors, 0 warnings`;
- existing `V42BaselineRouterLab.ex5` must be non-empty and not older than installed exact source;
- accepted V38 ZIP, V34 tape and state are reverified;
- exact MT5 Strategy Tester launches only after those checks;
- run completion waits for new `LATEST` id/folder and complete `monthly_summary.csv`, `trades.csv`, `manifest.txt` with tester/no-order markers;
- analyzer still hard-reproduces accepted V38 control before any challenger result is accepted;
- final output remains one SHA-manifested, CRC-tested ZIP.

If compile log is not 0/0, resume must print the real compiler evidence and stop. Do not automatically recompile inside resume.

## Required QA invariants

Preserve:

- pinned V31 Python version/dependencies;
- explicit UTF-8 text handling;
- `bash -n` gate for all three V42 shell entrypoints;
- accepted V38 ZIP SHA/CRC/source extraction;
- V42 deterministic source SHA and no-order/tester MQL lint;
- no runtime shell patcher;
- no `set +e`;
- direct compile artifact checkpoint for clean runs;
- compiled-EA resume for the current recovery;
- MT5 `LATEST` + complete manifested output as execution/collection postcondition;
- no `git clean`;
- one ZIP with internal SHA manifest and CRC verification.

## Output

For current recovery run `runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh` after closing MT5. MetaEditor need not be opened and resume never launches it.

Upload only `runtime/v42_baseline_router_exact_mt5/OUTPUT_V42/v42_baseline_router_exact_mt5.zip`.
After upload verify integrity and exact control reproduction first. Report exact metrics for control, historical adaptive variants and all V42 challengers. A development PASS only permits freezing one challenger for genuinely fresh chronological confirmation; never call same-window V42 production-ready or live-authorized.
