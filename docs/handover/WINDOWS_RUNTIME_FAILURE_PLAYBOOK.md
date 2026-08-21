# Windows / MT5 Runtime Failure Playbook

Date: 2026-08-21

This file is mandatory recovery context for future coordinators. Read it before changing any Windows runner.

## Core recovery ladder

Always identify the last completed stage:

`provenance -> source -> compile -> MT5 -> collection -> analysis -> packaging`

Resume only the failed stage. **Do not rerun MT5** when Strategy Tester already completed and the remaining problem is collection, analysis or packaging.

## Incident 1 — historical source-builder drift

V42 initially rebuilt V34 and obtained SHA `228b3ec7...` while an older accepted constant expected `8bae2c56...`. Do not bless a newly rebuilt historical hash just to pass a runner.

Rule: use immutable accepted V38 ZIP SHA
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`
and accepted V38 source SHA
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

## Incident 2 — Windows CP1252 vs UTF-8

A static test used bare `Path.read_text()` and Windows default CP1252 failed on UTF-8 punctuation.

Rules:

- repository text reads/writes use explicit UTF-8;
- runners export `PYTHONUTF8=1`;
- runners export `PYTHONIOENCODING=utf-8`.

## Incident 3 — global ERR trap with `set +e`

`set +e` does not disable a global Bash `ERR` trap. A Windows process returning non-zero killed a runner before `$?` could be captured.

Rule: never use `set +e` around MetaEditor/MT5. Use:

`if command; then rc=0; else rc=$?; fi`

## Incident 4 — runtime shell patcher complexity

V42 temporarily used a Python script to patch/generate the actual shell runner at runtime. This multiplied encoding/control-flow failure surfaces.

Rule: no generated/self-modifying shell runner. Use tracked direct runners.

## Incident 5 — MetaEditor artifact race / rc semantics

MetaEditor returned rc=1 while `.mq5`, `.log` and `.ex5` appeared successfully. A fixed wait incorrectly declared failure.

Compile success is not launcher rc. Accept only when all are true:

1. installed source SHA is the intended frozen SHA;
2. final compiler summary is `Result: 0 errors, 0 warnings`;
3. non-empty EX5 exists;
4. compile artifacts are current for that source.

Check valid compile artifacts before deleting or recompiling.

## Incident 6 — MT5 completion semantics

Terminal process rc alone is not completion evidence.

Require:

- a new `LATEST` run id;
- a new run folder;
- non-empty `monthly_summary.csv`, `trades.csv`, `manifest.txt`;
- `tester_only=1`;
- `native_broker_orders=0`;
- `external_broker_orders=0`;
- experiment-specific manifest markers.

Checkpoint the run folder immediately. If MT5 finished but copy/collection failed, use collection-only recovery.

## Incident 7 — MSYS sha256sum manifest format

Git Bash/MSYS emitted `<hash> *filename`, while an inline Python parser assumed `<hash><two spaces>filename` and crashed after a successful MT5 run.

Rule: never parse platform-specific `sha256sum` rendering for internal bundle manifests. Use `scripts/package_research_bundle_portable.py`, which computes hashes in Python and writes canonical `<hash><two spaces>filename`.

## Incident 8 — packaging-only failure

The V42 exact run completed and analysis completed, but ZIP creation failed. The correct response was package-only recovery from completed evidence, not another backtest.

Every expensive exact campaign must provide a package-only entrypoint.

## V44 checkpoint policy

V44 has 19 exact windows.

- compile checkpoint valid -> MetaEditor must not rerun;
- `checkpoint/<tag>/MT5_DONE.txt` + source run folder -> collect only;
- `checkpoint/<tag>/DONE.txt` -> that window must not rerun MT5;
- annual control reproduction happens before the remaining 18 windows;
- when all 19 `DONE.txt` files and aggregate analysis exist, a bootstrap failure may only invoke package-only recovery.

Never use `git clean` in Windows recovery because accepted evidence, `.venv`, compiled EA files, state and checkpoints may be untracked.

## Safety

REAL-MONEY LIVE TRADING is forbidden in this research repository workflow. Risk ceiling remains <=1.00%/trade. No Martingale, uncontrolled grid or doubling. A V44 readiness PASS means paper/demo only.
