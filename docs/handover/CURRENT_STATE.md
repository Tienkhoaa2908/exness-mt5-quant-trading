# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

Always resolve current remote HEAD and read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` before project work.

## Current objective

Passive waiting for a natural V69 trade is no longer the next diagnostic. After roughly one day of healthy DEMO runtime with zero natural fills, the project switched to immediate execution diagnosis:

1. snapshot already-collected live V69 telemetry;
2. determine the furthest signal/state-machine stage actually reached;
3. run one isolated DEMO-only 0.01 XAUUSDm actual open/close probe;
4. automatically relaunch frozen V69;
5. distinguish upstream strategy gating from an order-path integration defect;
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

The V69 Sep 2025-May 2026 replay is development evidence, not an independent holdout.

## Verified live runtime before immediate diagnostic

The previous Windows DEMO run compiled `V69FrozenForwardSmokeDashboardLong` with `0 errors, 0 warnings` and achieved:

- live tick heartbeat;
- telemetry active;
- stable broker preflight READY twice;
- lot `0.01`, broker min `0.01`, step `0.01`, max `200`;
- local OrderCheck error `0`;
- server retcode `0`, comment `Done`;
- `V69_RUNTIME_SMOKE_VERIFIED=1`;
- chart `SYSTEM HEALTH: READY` and `BROKER PREFLIGHT: READY`.

This proves attachment/runtime and dry-run broker readiness. It does not prove the actual V69 integrated `g_trade.Buy()` path.

## Immediate real-readiness execution probe

Canonical launcher:

`bash runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`

Components:

- `scripts/analyze_v69_live_signal_path.py` — signal/state funnel;
- `scripts/build_v69_demo_execution_probe_source.py` — isolated `V69DemoExecutionProbe`;
- `runtime/v69_real_readiness_probe/RUN_V69_REAL_READINESS_PROBE.py` — snapshot, actual DEMO probe, evidence, frozen-V69 relaunch;
- `tests/test_v69_real_readiness_probe_static.py` — safety/isolation/funnel/launcher-contract regressions;
- `docs/handover/IMMEDIATE_REAL_READINESS_PLAN.md` — interpretation.

Probe contract:

- DEMO account required;
- exactly `XAUUSDm`;
- exactly `0.01` lot;
- unique magic `699901`;
- dry-run `OrderCheck` then one actual DEMO BUY;
- closes only the probe-owned position immediately;
- records open/close retcode, comment, price and free margin;
- gracefully closes the probe MT5 using `TerminalClose()`;
- automatically relaunches frozen V69 after PASS;
- never authorizes REAL money.

Interpretation:

- probe PASS + no `POST_CONFIRM_ENTRY_READY`: upstream V69 gating/state selectivity prevented entry;
- probe PASS + `POST_CONFIRM_ENTRY_READY > 0` but no natural V69 deal: inspect V69 preflight/send integration immediately;
- probe FAIL: diagnose the actual broker execution retcode instead of waiting for a natural signal.

## First Windows probe attempt — harness failure before MT5 execution

Operator ran exact checkpoint `40115f1aa741720afa360b4cad4216dd0e2ab27e` at approximately 2026-09-03 00:56 (+07).

Observed:

- repository exact-state preflight PASS;
- Python 3.12.10 selected after broken `py.exe -3` was rejected;
- all six then-existing real-readiness static tests PASS;
- secret scan PASS;
- runner failed immediately at its first inherited repository guard with:
  `RuntimeError: V69_ONE_SHOT_EXPECTED_HEAD is required`.

Root cause is deterministic harness contract mismatch:

- canonical new launcher accepted/exported `V69_REAL_READINESS_EXPECTED_HEAD`;
- reused `forward.base.ensure_repo()` still required `V69_ONE_SHOT_EXPECTED_HEAD`;
- the old static launcher test did not assert the cross-module environment bridge.

This failure happened before `configure_runtime()`, before signal snapshot, before MetaEditor compile and before any MT5 execution probe was launched. It is therefore **not broker evidence and not strategy evidence**. Because MT5 had been closed for the diagnostic and the runner failed before its automatic relaunch stage, frozen V69 should be treated as not currently relaunched until the corrected probe run completes.

## Harness fix after first Windows attempt

The active branch now bridges the canonical probe expected HEAD into the inherited one-shot contract in two places:

1. Git Bash launcher exports `V69_ONE_SHOT_EXPECTED_HEAD="$EXPECTED_HEAD"` after exact-state validation;
2. Python runner `bridge_expected_head()` normalizes both environment names before calling the inherited `ensure_repo()` and before the later `forward.main()` relaunch.

A regression test now requires both bridges explicitly. Strategy logic, probe lot, symbol, magic, DEMO guard and REAL fail-closed semantics are unchanged.

Windows rerun of the corrected HEAD is still required before classifying the actual execution layer.

## Session-volatility successor research

`docs/research/SESSION_VOLATILITY_RESEARCH.md` defines a separate development track inspired by public volatility tools such as MarketMilk.

Research goal: learn symbol/session-specific volatility, spread efficiency and continuation expectancy from our own MT5 history with DST-aware London/New York labels. This is successor research, not a modification to frozen V69 and not a claim that New York always has positive expectancy.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_BROKER_PREFLIGHT=READY_STABLE_2_CHECKS_FROM_PREVIOUS_HEALTHY_RUN`

`V69_RUNTIME_SMOKE_VERIFIED=1_FROM_PREVIOUS_HEALTHY_RUN`

`V69_NATURAL_FILL_AFTER_APPROX_1_DAY=0`

`V69_FIRST_REAL_READINESS_WINDOWS_ATTEMPT=HARNESS_FAIL_BEFORE_RUNTIME`

`V69_ACTUAL_DEMO_EXECUTION_PROBE=NOT_YET_EXECUTED`

`V69_EXPECTED_HEAD_BRIDGE_FIX=CODED_AWAITING_EXACT_HEAD_CI_AND_WINDOWS_RERUN`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`SESSION_VOLATILITY_RESEARCH=DEVELOPMENT_ONLY`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Verify CI on the exact corrected remote HEAD.
2. Keep MT5 and MetaEditor closed for the retry.
3. Fast-forward only to the exact corrected HEAD.
4. Run only `START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`.
5. Require the new marker `V69_ONE_SHOT_EXPECTED_HEAD_BRIDGED=` before the runner enters runtime setup.
6. Require MetaEditor `0 errors, 0 warnings` for the execution-probe EA.
7. Require actual DEMO BUY + immediate probe-owned close PASS or capture the first exact broker failure.
8. Read the pre-probe signal funnel and classify gating vs order-path integration.
9. Frozen V69 is automatically relaunched only after the probe PASS path.
10. REAL remains a separate fail-closed deployment/risk decision.
