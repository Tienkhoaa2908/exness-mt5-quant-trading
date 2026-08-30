# V64 MT5 Locator Fix Recovery State

Last updated: 2026-08-30.

Read this file together with `docs/handoff/V64_RECOVERY_STATE.md`.

## Failure observed on Windows

The operator ran exact V64 head `dda48ea1d90fc352141d4a2d62260f25eb972286`.

The run passed:

- exact branch/head verification;
- V64 static tests 12/12;
- secret scan;
- LONG/SHORT/SCREEN source generation.

It failed before MetaEditor compile and before Strategy Tester with:

`AttributeError: module 'v45_base_for_v48' has no attribute 'find_mt5_data_dir'`

The original V64 runner called stale/nonexistent helpers:

- `base.find_mt5_data_dir()`
- `base.find_common_files_dir(data)`

The canonical inherited V45 helper is `base.locate_mt5()`, which returns `(data, common, expert_dir, inputs)`. V63 already used that canonical API successfully.

This failure is runner orchestration/API drift, not a strategy, MQL, MetaEditor, MT5 data, or Model=4 result.

## Fixed layer

A compatibility owning layer was added:

- `runtime/v64_microstructure_trigger_shadow/RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py`
- `tests/test_v64_mt5_locator_compat_static.py`

The V64 Git Bash launcher now invokes the fixed runner.

The adapter:

1. requires callable `base.locate_mt5`;
2. caches one canonical `(data, common, expert_dir, inputs)` tuple;
3. maps the stale V64 names to that same tuple;
4. rejects a data/common pairing mismatch;
5. leaves the substantive V64 signal/execution engine unchanged.

Regression tests use a fake base and require a single canonical locator call for both data/common lookups. The launcher is also required to invoke the fixed runner.

## Safety and next step

- Do not rerun V63/V62 merely to recover this failure.
- Do not `git clean`.
- Do not `stash pop` while tester work is active.
- Do not activate REAL-money trading.
- Resolve latest exact head of `agent/v64-microstructure-trigger-shadow-research` and require GitHub Actions quality success on that exact head before Windows rerun.
- On rerun, require `V64_MT5_LOCATOR_COMPAT=PASS` before accepting any later compile/tester evidence.
- Windows V64 is still NOT PASS until LONG, SHORT and screen compile 0/0 and all tester phases package fresh evidence.
