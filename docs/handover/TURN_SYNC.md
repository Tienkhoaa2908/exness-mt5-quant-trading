# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 01:xx (+07)

## User input

Operator ran the immediate V69 real-readiness probe from exact checkpoint `40115f1aa741720afa360b4cad4216dd0e2ab27e`.

Observed output:

- repo exact-state preflight PASS;
- Python 3.12.10 selected after broken `py.exe -3` was rejected;
- all six then-existing real-readiness static tests PASS;
- secret scan PASS;
- first Python runner call failed immediately with:
  `RuntimeError: V69_ONE_SHOT_EXPECTED_HEAD is required`.

## Mandatory state inspection

Before changing code, re-resolved active branch remote HEAD and read:

- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- previous `docs/handover/TURN_SYNC.md`;
- real-readiness Git Bash launcher;
- real-readiness Python runner;
- inherited one-shot `ensure_repo()` implementation;
- real-readiness static regression tests.

## Root cause

This was a harness-only contract mismatch.

`START_V69_REAL_READINESS_PROBE_GIT_BASH.sh` validated and read:

`V69_REAL_READINESS_EXPECTED_HEAD`

but `RUN_V69_REAL_READINESS_PROBE.py` immediately reused `forward.base.ensure_repo()`, whose inherited contract requires:

`V69_ONE_SHOT_EXPECTED_HEAD`

The runner later also calls `forward.main()` to relaunch frozen V69, so the inherited variable must remain available through the entire diagnostic.

The previous static launcher test checked only that the new variable was required; it did not assert that the new contract was bridged into the inherited runtime. Therefore CI passed while the first Windows execution failed.

## Impact classification

The failure occurred before:

- `configure_runtime()`;
- live telemetry snapshot/analyzer execution;
- MetaEditor compilation of `V69DemoExecutionProbe`;
- MT5 probe startup;
- actual DEMO order send;
- automatic frozen-V69 relaunch.

Therefore this attempt provides no new broker/execution evidence and no strategy evidence.

Because the operator had closed MT5/MetaEditor as instructed and the runner failed before relaunch, frozen V69 should be considered not relaunched until the corrected retry finishes.

## Code changes

### Launcher bridge

`runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`

After exact branch/HEAD/clean-worktree validation it now exports:

`V69_ONE_SHOT_EXPECTED_HEAD="$EXPECTED_HEAD"`

and prints:

`V69_ONE_SHOT_EXPECTED_HEAD_BRIDGED=...`

### Runner bridge

`runtime/v69_real_readiness_probe/RUN_V69_REAL_READINESS_PROBE.py`

Added `bridge_expected_head()` which:

- reads canonical `V69_REAL_READINESS_EXPECTED_HEAD`;
- permits inherited `V69_ONE_SHOT_EXPECTED_HEAD` only as a fallback for direct compatibility;
- requires an expected HEAD if neither exists;
- normalizes both variables to the same SHA;
- runs before inherited `forward.base.ensure_repo()`;
- leaves the inherited variable available for the final `forward.main()` relaunch.

### Regression test

`tests/test_v69_real_readiness_probe_static.py`

Added a dedicated test requiring:

- launcher export of the inherited expected-head variable;
- launcher bridge marker;
- runner normalization of `V69_ONE_SHOT_EXPECTED_HEAD`;
- runner call to `bridge_expected_head()`.

No V69 strategy logic, symbol, lot, direction, probe magic, DEMO guard, or REAL authorization semantics changed.

## Documentation sync

Updated:

- `CURRENT_STATE.md` — first Windows attempt classified as harness failure before runtime;
- `KNOWN_FAILURES.md` — new expected-head cross-module contract regression recorded;
- this `TURN_SYNC.md`.

## Current blocker

Actual DEMO execution remains untested because the first attempt failed before MT5 launch.

The corrected branch must pass exact-HEAD CI, then the operator should retry only the same real-readiness launcher. No historical replay and no additional waiting for a natural trade is required.

## Safety status

Unchanged:

- XAUUSDm only;
- 0.01 lot;
- DEMO-only execution probe;
- unique magic `699901`;
- LONG BUY probe only;
- frozen V69 strategy unchanged;
- SHORT rejected/disabled;
- REAL authorization remains false.

## Next operator action

1. Verify exact corrected remote HEAD and CI.
2. Keep MT5 and MetaEditor closed.
3. Fast-forward active branch to exact corrected HEAD.
4. Export `V69_REAL_READINESS_EXPECTED_HEAD` to that corrected HEAD.
5. Run only `runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`.
6. Return output from `V69_ONE_SHOT_EXPECTED_HEAD_BRIDGED=` onward or the first `FATAL`.
7. Do not rerun historical research and do not wait another day for a natural signal.
