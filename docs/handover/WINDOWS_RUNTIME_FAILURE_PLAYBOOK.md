# Windows / MT5 Runtime Failure Playbook

Date: 2026-08-22

Mandatory recovery context. Read before changing any Windows runner.

## Core recovery ladder

`provenance -> source -> compile -> MT5 -> collection -> analysis -> packaging`

Resume only the failed stage. Do not rerun MT5 when Strategy Tester already completed and only collection, analysis or packaging failed.

## Incident 1 — historical source-builder drift

V42 rebuilt V34 to a different SHA than the historical accepted contract. Rule: never bless a newly rebuilt historical hash merely to pass a runner. Use immutable accepted V38 ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b` and accepted V38 source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

## Incident 2 — Windows CP1252 vs UTF-8

Bare `Path.read_text()` used the Windows default codec and failed on UTF-8 punctuation. Repository text I/O must be explicit UTF-8. Runners export `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.

## Incident 3 — global ERR trap with `set +e`

`set +e` does not disable a global Bash `ERR` trap. Never use that pattern around MetaEditor/MT5. Prefer tracked Python orchestration for long campaigns.

## Incident 4 — runtime shell patcher complexity

Runtime-generated/self-modifying shell runners created avoidable failure surfaces. Prohibited. Use tracked direct runners/orchestrators.

## Incident 5 — MetaEditor artifact race / rc semantics

MetaEditor can return rc=1 while valid `.log` and `.ex5` appear. Compile success is: exact source SHA + final `Result: 0 errors, 0 warnings` + non-empty current EX5. Launcher rc alone is not acceptance evidence.

## Incident 6 — MT5 completion semantics

Terminal rc alone is not completion evidence. Require a new `LATEST`, a new run folder, non-empty `monthly_summary.csv`, `trades.csv`, `manifest.txt`, and tester/no-order experiment markers. Checkpoint the run folder immediately.

## Incident 7 — MSYS sha256sum manifest format

Git Bash/MSYS can emit `<hash> *filename`. Never parse platform-specific `sha256sum` rendering for internal bundle manifests. Use `scripts/package_research_bundle_portable.py`.

## Incident 8 — packaging-only failure

V42 completed MT5 and analysis but failed ZIP creation. Correct response: package completed evidence only. Every expensive campaign must provide package-only recovery.

## Incident 9 — historical state look-ahead

The accepted restart state is from 2025-08. Injecting it into a 2022 test leaks future realized-R router information. V45 must back up Common Files state, delete it before tester launch, cold-start from reset adaptive scores, use six warm-up months, save post-run state only as evidence, and restore the pre-V45 state afterward. Accepted V38 `LoadAdaptiveState()` resets scores before attempting file load and permits missing-state initialization.

## Incident 10 — V45 rc=100018 confirmed disk exhaustion

First V45 attempt on 2026-08-22 compiled cleanly and initialized the EA successfully but produced no accepted tester evidence. Diagnostic ZIP SHA256:

`3af2ab70f02920ad6fbd0eb5b3fd67ef66a550bf2db08bd523ee4b63372e8b1f`

Confirmed terminal/tester sequence:

- MT5 startup reported only `3 / 136 Gb disk` free;
- XAUUSDm synchronized through the requested historical range; M15/H1 history began in 2021;
- `V45_MULTIYEAR_VALIDATION START` printed at 2022-01-01;
- tester then logged `XAUUSDm: cannot generate history data, check disk space`;
- `0 ticks, 0 bars generated`;
- last test result `no disk space in ticks generating function`;
- terminal exited with process rc `100018`.

Therefore this incident is not a strategy/config/state/history-start failure. The 2022 range was available and EA initialization succeeded. Do not shorten the range because of this failure.

Detailed incident record: `docs/research/v45_mt5_disk_failure_diagnosis.md`.

## Incident 11 — move MetaTester storage to D via junction

The heavy per-agent tick/history copies live under:

`%APPDATA%\MetaQuotes\Tester\<terminal-id>\Agent-127.0.0.1-<port>\bases`

For the current terminal id:

`D0E8209F77C8CF37AD8BF550E51FF075`

V45 now runs `runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py` before disk preflight.

Default physical target:

`D:\MT5TesterCache\<terminal-id>`

The original C path remains visible to MetaTrader as an NTFS directory junction. Migration contract:

1. MT5, MetaEditor and MetaTester must all be closed;
2. Robocopy current MetaTester storage from C to the dedicated D target;
3. verify source/target file count and total bytes;
4. rename the original C directory to a temporary same-volume backup;
5. create `mklink /J` from the original C path to the D target;
6. verify the junction resolves to the exact target;
7. only after verification delete the C backup;
8. if junction creation or verification fails, remove the partial junction and restore the original C directory.

The migration must not move/delete terminal broker history under `%APPDATA%\MetaQuotes\Terminal\<terminal-id>\bases`, Common Files state/tapes, project evidence, repo files, or compiled EAs.

Migration is idempotent. If the exact junction already exists, it reports `V45_TESTER_STORAGE_ON_D=1 already_migrated=1` and changes nothing.

After migration the disk gate is volume-aware:

- terminal volume (normally C:) needs >=2 GiB for terminal config/log/temp activity;
- physical MetaTester storage volume (normally D:) needs >=12 GiB for the 2022-2026 tick run.

Do not reintroduce a blanket 12-GiB requirement on C after the heavy tester storage is redirected to D.

## V44 checkpoint policy

V44 has 19 exact windows. Valid compile checkpoint means MetaEditor must not rerun. `checkpoint/<tag>/MT5_DONE.txt` permits collection-only. `checkpoint/<tag>/DONE.txt` means that window must not rerun MT5. Annual control reproduction precedes the other 18 windows. Packaging failure after completed evidence is package-only.

## V45 checkpoint policy

V45 has exactly one expensive 2022-01-01 -> 2026-08-01 tester invocation.

- D-drive MetaTester migration/junction must verify first;
- junction-aware disk preflight PASS is required before tester launch;
- valid compile checkpoint -> MetaEditor must not rerun;
- `OUTPUT_V45/checkpoint/MT5_DONE.json` -> collection-only, MT5 MUST NOT RERUN;
- `OUTPUT_V45/checkpoint/DONE.txt` -> analysis/package only, MT5 MUST NOT RERUN;
- completed bundle + packaging failure -> `PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh` only.

Never use `git clean`; accepted ZIPs, `.venv`, state backups, compiled artifacts and checkpoints may be untracked recovery assets.

## Safety

REAL-MONEY LIVE TRADING is forbidden in this research workflow. Risk ceiling remains <=1.00%/trade. No Martingale, uncontrolled grid or doubling. V44/V45 readiness PASS means paper/demo deployment validation only; `LIVE_AUTHORIZED=0`.
