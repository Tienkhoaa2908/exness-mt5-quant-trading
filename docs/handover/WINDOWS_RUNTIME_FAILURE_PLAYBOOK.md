# Windows / MT5 Runtime Failure Playbook

Date: 2026-08-22

Mandatory recovery context. Read before changing any Windows runner.

## Current project policy

Project-wide live-trading policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Historical tester/paper milestones may have `LIVE_AUTHORIZED=0`, no-order source contracts or DEMO-only guards. Those are phase-specific runtime/evidence constraints, not a permanent prohibition on researching or preparing production/live trading with real capital.

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

Terminal rc alone is not completion evidence. Require a new `LATEST`, a new run folder, non-empty expected ledgers/manifests, and milestone-appropriate experiment markers. Checkpoint the run folder immediately.

## Incident 7 — MSYS sha256sum manifest format

Git Bash/MSYS can emit `<hash> *filename`. Never parse platform-specific `sha256sum` rendering for internal bundle manifests. Use the portable Python manifest packager.

## Incident 8 — packaging-only failure

V42 completed MT5 and analysis but failed ZIP creation. Correct response: package completed evidence only. Every expensive campaign must provide package-only recovery.

## Incident 9 — historical state look-ahead

The accepted restart state was from 2025-08. Injecting it into a 2022 test leaks future realized-R router information. V45 backs up Common Files state, deletes it before tester launch, cold-starts from reset adaptive scores, uses warm-up months, saves post-run state only as evidence, and restores pre-run state afterward.

## Incident 10 — V45 rc=100018 confirmed disk exhaustion

First V45 attempt on 2026-08-22 compiled cleanly and initialized the EA successfully but produced no accepted tester evidence. Diagnostic ZIP SHA256:
`3af2ab70f02920ad6fbd0eb5b3fd67ef66a550bf2db08bd523ee4b63372e8b1f`.

Confirmed terminal/tester sequence:
- MT5 startup reported only `3 / 136 Gb disk` free;
- XAUUSDm synchronized through the requested historical range;
- `V45_MULTIYEAR_VALIDATION START` printed at 2022-01-01;
- tester then logged `cannot generate history data, check disk space`;
- `0 ticks, 0 bars generated`;
- terminal exited with rc `100018`.

This was not strategy/config/state/history-start failure. Do not shorten the range because of this failure.

Detailed incident: `docs/research/v45_mt5_disk_failure_diagnosis.md`.

## Incident 11 — move MetaTester storage to D via junction

Heavy per-agent tick/history copies live under:
`%APPDATA%\MetaQuotes\Tester\<terminal-id>\Agent-127.0.0.1-<port>\bases`.

For terminal id `D0E8209F77C8CF37AD8BF550E51FF075`, V45 moved heavy tester storage to a dedicated D-drive target via verified NTFS directory junction.

Migration contract:
1. MT5, MetaEditor and MetaTester closed;
2. copy current storage to dedicated D target;
3. verify source/target file count and bytes;
4. rename original C directory to temporary same-volume backup;
5. create `mklink /J` from original path to D target;
6. verify junction target;
7. delete backup only after verification;
8. on failure, remove partial junction and restore original directory.

Do not move/delete terminal broker history, Common Files state/tapes, project evidence, repo files or compiled EAs.

## V44 checkpoint policy

V44 had 19 exact windows. Valid compile checkpoint means MetaEditor must not rerun. `MT5_DONE.txt` permits collection-only. `DONE.txt` means that window must not rerun MT5. Packaging failure after completed evidence is package-only.

## V45 checkpoint policy

V45 had exactly one expensive 2022-01-01 -> 2026-08-01 tester invocation.

- D-drive MetaTester migration/junction verifies first;
- disk preflight PASS before tester launch;
- valid compile checkpoint -> MetaEditor must not rerun;
- `OUTPUT_V45/checkpoint/MT5_DONE.json` -> collection-only;
- `OUTPUT_V45/checkpoint/DONE.txt` -> analysis/package only;
- completed bundle + packaging failure -> package existing output only.

Never use `git clean`; accepted ZIPs, `.venv`, state backups, compiled artifacts and checkpoints may be untracked recovery assets.

## Current safety semantics

Permanent engineering invariants:
- no Martingale;
- no uncontrolled grid;
- no doubling after loss;
- no credentials/secrets in Git;
- preserve strategy identity during a validation campaign;
- use milestone-appropriate account/order ownership checks;
- prevent duplicate execution;
- reconcile broker/runtime state;
- preserve evidence and resume only failed stages.

Historical V44/V45 `LIVE_AUTHORIZED=0` markers remain historical evidence only. They do not override ADR-049, which explicitly allows live-trading research and targets production/live deployment after readiness evidence.
