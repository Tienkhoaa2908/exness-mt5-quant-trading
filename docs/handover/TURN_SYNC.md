# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 16:40 (+07)

## User input

User ran the preregistered one-pass V72 EURUSD untouched validation. Build, source hash, compile and MT5 tester process completed, but the launcher failed after MT5 exited because `V64_ENTRY_EVAL.csv` was not found in the collector root. User explicitly noted that the tester appeared to finish but no output was produced.

## State read before work

Fresh-resolved pre-turn remote HEAD on `agent/v72-eurusd-independent-validation`:

`e22da3f4ec24840db4eb735a14a3725921e944a1`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent branch state and exact-head CI. Pre-turn exact-head CI was green.

## Operator evidence inspected

The V72 run showed:

- exact branch/HEAD guard PASS;
- Python 3.12 selected;
- V72 static tests PASS count=4;
- secret scan PASS;
- MT5 locator PASS;
- exact V71 source generated with SHA256 `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- MetaEditor compile `0 errors, 0 warnings`;
- tester config `EURUSDm`, M15, Model=4, `2024.09.01 -> 2025.09.01`;
- MT5 tester process returned `rc=0`;
- failure occurred only afterward in `copy_run()` because the expected root was empty:
  `V64 run v72_eurusdm_untouched_long missing V64_ENTRY_EVAL.csv; root_listing=`.

## Root cause

This is a harness/telemetry path mismatch, not strategy evidence and not a broker/tester failure.

The exact hash-pinned V71 strategy source hardcodes FILE_COMMON telemetry root:

`mt5_quant\\v71_fx_portability`

The original V72 runner incorrectly set the reused V64 collector root to:

`mt5_quant\\v72_eurusd_independent_validation`

Therefore the tester wrote to the V71 root while Python inspected the empty V72 root.

## Fix implemented

Updated V72 runner so `runner.COMMON_DIR` is derived from:

`SOURCE_COMMON_DIR = "v71_fx_portability"`

This preserves the exact pinned V71 source SHA and does not alter strategy semantics.

Added fail-closed recovery before any new tester launch:

1. inspect `Common/Files/mt5_quant/v71_fx_portability`;
2. require primary `V64_ENTRY_EVAL.csv`, `V64_EVENTS.csv`, `V64_DEALS.csv`;
3. parse timestamped rows;
4. recover only if all timestamps fall inside the preregistered `2024.09.01 -> 2025.09.01` validation period;
5. if valid, copy/analyze the existing completed run and print `V72_EURUSD_TEST_RERUN=0`;
6. if stale V71 Sep-2025+ or mixed-period evidence is found, reject recovery, archive that source root and then run one fresh tester pass automatically.

Regression tests were expanded from 4 to 6 and now guard:

- pinned V71 source root and V72 collector-root alignment;
- successful recovery of valid untouched-period evidence without tester rerun;
- rejection of stale V71-period evidence.

V72-specific CI passed on the code/test fix commit before documentation sync.

## Economic status

No V72 PASS/FAIL/INSUFFICIENT_SAMPLE classification is recorded yet. The first tester process completed, but its raw evidence still needs to be recovered/analyzed by the corrected launcher.

The preregistered acceptance gate remains unchanged:

- <8 trades -> `INSUFFICIENT_SAMPLE`;
- otherwise PASS requires net >0, PF >=1.25, DD <=$5.00, >=2 positive months, ex-best-trade net >0;
- otherwise `FAIL`.

No threshold was altered after seeing the failed collector output.

## Safety

`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`V72_SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next operator action

After final exact-head CI is green, run the corrected V72 launcher once. It should recover the already-completed run and avoid tester rerun if the source-root timestamps match the preregistered period. Only if recovery is rejected as stale/mixed should it perform a fresh tester pass.
