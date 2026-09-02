# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

Always resolve current remote HEAD and read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` before project work.

## Current objective

Passive waiting for a natural V69 trade is no longer the next diagnostic. After roughly one day of healthy DEMO runtime with zero natural fills, the project has switched to **immediate execution diagnosis**:

1. snapshot the already-collected live V69 telemetry;
2. determine the furthest signal/state-machine stage actually reached;
3. run one isolated DEMO-only 0.01 XAUUSDm actual open/close probe;
4. automatically relaunch frozen V69;
5. use those results to decide whether the no-trade condition is strategy gating or an order-path integration defect;
6. progress toward a separate REAL-readiness package only after this diagnostic is resolved.

REAL money remains unauthorized.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Safety/strategy contract:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only for current execution validation;
- SHORT rejected/disabled;
- REAL authorization false/fail-closed;
- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- reclaim -> separation `>= $1.30` -> later retest -> confirmation age `>=30s` -> `POST_CONFIRM_ENTRY_READY` -> `V64OrderPreflight`;
- structural stop fixed, no widening/clamp.

The `$1.30` and `30s` values are development choices, not proven universal optima.

## Development evidence

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all ten V68 winners while removing four losers, but `10/14` surviving V69 losers closed within 60 seconds. Monthly V69 replay is regime-concentrated: Sep `-$1.84`, Oct `+$9.15`, Nov `+$1.24`, Dec `-$2.28`, Jan `+$0.87`, Feb-May flat; excluding October total is `-$2.01`.

The V69 Sep 2025-May 2026 replay is development evidence, **not an independent holdout**.

## Verified live runtime before immediate diagnostic

Windows DEMO run compiled `V69FrozenForwardSmokeDashboardLong` with `0 errors, 0 warnings` and achieved:

- live tick heartbeat;
- telemetry active;
- stable broker preflight READY twice;
- lot `0.01`, broker min `0.01`, step `0.01`, max `200`;
- local OrderCheck error `0`;
- server retcode `0`, comment `Done`;
- `V69_RUNTIME_SMOKE_VERIFIED=1`;
- silent supervisor/background console suppression;
- chart `SYSTEM HEALTH: READY` and `BROKER PREFLIGHT: READY`.

This proves attachment/runtime and dry-run broker readiness. It does **not** prove the actual V69 `g_trade.Buy()` integration path.

## Immediate real-readiness execution probe

Canonical launcher:

`bash runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`

New components:

- `scripts/analyze_v69_live_signal_path.py` — reads existing `V64_EVENTS.csv` / `V64_DEALS.csv` and counts:
  - `POST_ZONE_REVERSAL_CONFIRM`;
  - `POST_CONFIRM_SEPARATION`;
  - `POST_CONFIRM_RETEST_READY`;
  - `POST_CONFIRM_ENTRY_READY`.
- `scripts/build_v69_demo_execution_probe_source.py` — builds isolated `V69DemoExecutionProbe`.
- `runtime/v69_real_readiness_probe/RUN_V69_REAL_READINESS_PROBE.py` — snapshots telemetry, runs actual DEMO probe, records result, then relaunches frozen V69.
- `tests/test_v69_real_readiness_probe_static.py` — safety/isolation/funnel tests.
- `docs/handover/IMMEDIATE_REAL_READINESS_PLAN.md` — operational interpretation.

Probe contract:

- DEMO account required;
- exactly `XAUUSDm`;
- exactly `0.01` lot;
- unique magic `699901`;
- dry-run `OrderCheck` then one actual DEMO BUY;
- closes only the probe-owned position immediately;
- writes local/server open/close diagnostics and free margin;
- gracefully closes probe MT5 using `TerminalClose()`;
- automatically relaunches frozen V69;
- does not authorize REAL money.

Interpretation:

- probe PASS + no `POST_CONFIRM_ENTRY_READY`: MT5/broker execution works; V69's upstream gates prevented entry;
- probe PASS + `POST_CONFIRM_ENTRY_READY > 0` but no natural V69 deal: escalate directly to V69 preflight/send tracing; likely strategy-order-path integration defect;
- probe FAIL: diagnose exact actual order retcode immediately rather than waiting for a natural signal.

## Session-volatility successor research

`docs/research/SESSION_VOLATILITY_RESEARCH.md` now defines a separate development track inspired by public volatility tools such as MarketMilk.

Research goal: learn symbol/session-specific volatility, spread efficiency and continuation expectancy from our own MT5 history. Candidate labels include London open, London/New York overlap, New York open/core, Asia and rollover/low-liquidity. Timing must be DST-aware.

This is a successor research feature, not a modification to frozen V69 and not a claim that New York always has positive expectancy.

## CI checkpoint

Code checkpoint `89370fcd37493f478d3fb50b218dabeea9544320` passed:

- `v69-forward-quality` run `33662678974`;
- `v69-quality`;
- `v68-quality`;
- full `quality` run `33662678989`.

The exact post-documentation HEAD must be checked again before giving the operator command.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_BROKER_PREFLIGHT=READY_STABLE_2_CHECKS`

`V69_RUNTIME_SMOKE_VERIFIED=1`

`V69_NATURAL_FILL_AFTER_APPROX_1_DAY=0`

`V69_IMMEDIATE_EXECUTION_DIAGNOSIS=READY_TO_RUN_AFTER_EXACT_HEAD_CI`

`V69_ACTUAL_DEMO_EXECUTION_PROBE=NOT_YET_RUN_ON_WINDOWS`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`SESSION_VOLATILITY_RESEARCH=DEVELOPMENT_ONLY`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Verify CI on the exact current post-sync remote HEAD.
2. Operator closes MT5 and MetaEditor once.
3. Fetch/fast-forward to that exact HEAD.
4. Run only `START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`.
5. Require MetaEditor `0 errors, 0 warnings` for the execution-probe EA.
6. Require actual DEMO BUY + immediate probe-owned close PASS.
7. Read the pre-probe signal funnel and distinguish gating vs order-path integration failure.
8. Frozen V69 is automatically relaunched after probe PASS.
9. Use the result to build the next REAL-readiness/risk package; do not auto-enable REAL.
