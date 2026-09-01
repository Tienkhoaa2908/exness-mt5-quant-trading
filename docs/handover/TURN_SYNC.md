# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-01 (+07)

## User request

The user reported the current MT5 dashboard showing:

`BROKER: BLOCKED | ordercheck_call_failed_4756`

and asked to:

- verify whether the system can actually enter orders;
- add an obvious on-chart health layer so healthy/broken runtime is visible immediately;
- save the latest project state, failures, do/do-not-repeat rules and progress to GitHub;
- remove stale recovery documents that could confuse a future chat;
- establish a mandatory protocol that every project-related turn reads current GitHub
  state first and synchronizes state back to GitHub before the final answer;
- provide a professional recovery prompt and a professional GitHub state-sync prompt.

## Evidence inspected

Latest Windows one-shot log showed:

- branch was `agent/v69-one-shot-prospective-demo`;
- Python 3.12.10 selected after broken `py.exe -3` was rejected;
- static tests passed;
- MetaEditor compiled `V69FrozenForwardSmokeDashboardLong` with `0 errors, 0 warnings`;
- fixed lot `0.01`;
- broker min `0.0100`, step `0.0100`, max `200.0000`;
- symbol trade mode `4`;
- filling flags `3`;
- first broker `OrderCheck()` returned false with local error `4756`;
- the runner failed the startup gate.

MQL5 reference research confirmed:

- error 4756 is the generic `ERR_TRADE_SEND_FAILED`;
- `OrderCheck()` should be interpreted using both local error and
  `MqlTradeCheckResult.retcode/comment`;
- account-level `ACCOUNT_TRADE_ALLOWED` and `ACCOUNT_TRADE_EXPERT` are separate required
  permissions;
- Market/Exchange execution requests do not require a client-specified market price,
  unlike Request/Instant execution.

## Root-cause finding in the harness

The first broker-ready implementation refreshed its EA broker check every 30 seconds,
but the Python runner permanently failed after 12 seconds when the same blocked detail
remained. Therefore the runner could fail from a single startup `OrderCheck` result
before a second independent broker check ever occurred.

The implementation also discarded the server `retcode/comment` when `OrderCheck()`
returned false, leaving only generic 4756.

The latest observed broker volume contract proves this incident is **not a 0.01 lot-size
failure**.

## Code changes made this turn

Updated `scripts/build_v69_frozen_forward_demo_broker_ready_dashboard_source.py` to:

- refresh broker preflight every 5 seconds;
- publish `broker_check_seq`;
- classify fatal vs transient health failures;
- check terminal connection;
- check account trade permission;
- check account Expert Advisor permission;
- check terminal/MQL permissions;
- check symbol synchronization;
- capture trade/filling/execution modes;
- build the dry-run request according to execution mode;
- capture local `_LastError` plus server `retcode/comment`;
- initially treat bare 4756 with no server detail as transient;
- add a visible `SYSTEM HEALTH: STARTING / READY / BLOCKED` chart row;
- display preflight state and whether actual natural execution has been observed.

Updated `runtime/v69_one_shot_prospective_demo/RUN_V69_ONE_SHOT_BROKER_READY_DEMO.py` to:

- count only independent broker checks by sequence;
- require two consecutive independent READY checks before startup PASS;
- require repeated independent fatal confirmation before permanent BLOCKED;
- allow transient health checks up to 90 seconds to stabilize;
- print full local/server broker diagnostics.

Updated `tests/test_v69_one_shot_broker_ready_static.py` with regressions for:

- health fields;
- account/connection checks;
- execution-mode-aware request construction;
- stable independent checks;
- the prior 30-second-refresh / 12-second-failure bug;
- no new order-send path in the overlay;
- no background console flashing.

## Documentation changes made this turn

Created canonical docs:

- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- `docs/handover/STATE_SYNC_PROMPT.md`;
- this `docs/handover/TURN_SYNC.md`.

Replaced stale content in:

- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/RECOVERY_PROMPT.md`.

Removed superseded recovery-state duplicates:

- `docs/handoff/V61_RECOVERY_STATE.md`;
- `docs/handoff/V62_RECOVERY_STATE.md`;
- `docs/handoff/V63_RECOVERY_STATE.md`;
- `docs/handoff/V64_RECOVERY_STATE.md`;
- `docs/handoff/V64_RECOVERY_STATE_LOCATOR_FIX.md`;
- `docs/handoff/V65_RECOVERY_STATE.md`;
- `docs/handoff/V66_RECOVERY_STATE.md`;
- `docs/handoff/V67_RECOVERY_STATE.md`;
- `docs/handoff/V68_RECOVERY_STATE.md`;
- `docs/handoff/V69_FORWARD_RECOVERY_STATE.md`;
- `docs/handoff/V69_RECOVERY_STATE.md`;
- `docs/handover/RECOVERY_V31_1_EXACT_MT5.md`;
- `docs/handover/V31_1_READY_TO_RUN.md`.

Historical ADR/research evidence remains because it is provenance, not current recovery
state.

## Safety / strategy status

No V69 signal threshold, direction, stop, target or order-send path was intentionally
changed by the new health overlay.

Current boundary remains:

- LONG only;
- XAUUSDm M15;
- fixed lot 0.01;
- DEMO only;
- SHORT disabled;
- REAL authorization false.

## Unresolved blocker

The new health implementation still needs exact-HEAD CI verification and a Windows rerun.
The previous 4756 incident is not considered resolved until the new build either:

- reaches two stable independent READY checks, or
- captures a more specific deterministic account/server blocker via the new diagnostics.

## Next operator action

After exact-HEAD CI is green:

1. close MT5 and MetaEditor once;
2. rerun the canonical one-shot only;
3. require `0 errors, 0 warnings`;
4. require `SYSTEM HEALTH: READY` / two stable broker checks;
5. if READY, leave the short smoke running for 2 natural closed strategy trades or the
   48-hour cap;
6. if not READY, use the newly exposed account flags + local error + server
   retcode/comment; do not guess and do not retune strategy.
