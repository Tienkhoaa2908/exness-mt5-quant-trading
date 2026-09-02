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
4. distinguish upstream strategy gating from an order-path integration defect;
5. automatically relaunch frozen V69 after probe PASS;
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

## Verified live runtime

The Windows DEMO dashboard has previously achieved and the latest operator screenshot again visibly shows:

- `V69FrozenForwardSmokeDashboardLong` attached on `XAUUSDm M15`;
- live tick heartbeat;
- telemetry active;
- `SYSTEM HEALTH: READY`;
- `BROKER PREFLIGHT: READY`;
- fixed lot `0.01` with broker min/step `0.01`;
- position FLAT;
- `Closed 0 / 2` on the legacy smoke dashboard.

This proves the frozen dashboard/runtime is currently alive and broker dry-run health is READY. It still does not by itself prove the integrated V69 natural `g_trade.Buy()` path.

### Important UI correction

The dashboard text `Closed 0/2` and `wait until 48h cap` is now **obsolete as a project gate**. It belongs to the earlier short forward-smoke design. The project has already replaced passive `2 trades or 48h` waiting with the immediate signal-funnel + actual DEMO execution-probe gate.

Do not instruct the operator to keep waiting for two natural trades merely because the current frozen dashboard still displays that legacy progress text.

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

## First Windows probe attempt and fix

Operator ran checkpoint `40115f1aa741720afa360b4cad4216dd0e2ab27e`. Repository preflight, Python discovery, static tests and secret scan passed, but the runner failed before MT5 execution because the new launcher exported `V69_REAL_READINESS_EXPECTED_HEAD` while inherited `forward.base.ensure_repo()` required `V69_ONE_SHOT_EXPECTED_HEAD`.

This was a harness-only failure before signal snapshot, MetaEditor compile, MT5 probe startup or any DEMO order.

The active branch fixed this by bridging both expected-head names in both the Git Bash launcher and Python runner. Regression tests now require that bridge. Exact-head CI for corrected checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` passed `v69-forward-quality`, `v69-quality`, `v68-quality`, and full `quality`.

## Latest operator-visible state

Latest screenshot supplied after the corrected code became available shows the frozen V69 dashboard running again with:

- `SYSTEM HEALTH: READY`;
- `BROKER PREFLIGHT: READY`;
- position FLAT;
- live tick heartbeat;
- zero closed V69 strategy trades.

However the chat does **not yet contain the corrected real-readiness terminal output or `V69_REAL_READINESS_PROBE_RESULT.json`**. Therefore actual probe PASS/FAIL and the pre-probe signal funnel must still be treated as unverified until that output is supplied or the corrected launcher is run to completion.

Do not infer execution-probe PASS from the chart alone. The chart can be relaunched independently.

## Session-volatility successor research

`docs/research/SESSION_VOLATILITY_RESEARCH.md` defines a separate development track inspired by public volatility tools such as MarketMilk.

Research goal: learn symbol/session-specific volatility, spread efficiency and continuation expectancy from our own MT5 history with DST-aware London/New York labels. This is successor research, not a modification to frozen V69 and not a claim that New York always has positive expectancy.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_CURRENT_DASHBOARD_RUNTIME=READY`

`V69_BROKER_PREFLIGHT=READY`

`V69_NATURAL_CLOSED_TRADES=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`V69_FIRST_REAL_READINESS_WINDOWS_ATTEMPT=HARNESS_FAIL_BEFORE_RUNTIME`

`V69_EXPECTED_HEAD_BRIDGE_FIX=CODED_AND_EXACT_HEAD_CI_PASS`

`V69_CORRECTED_EXECUTION_PROBE_RESULT=NOT_YET_VERIFIED_IN_CHAT`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`SESSION_VOLATILITY_RESEARCH=DEVELOPMENT_ONLY`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Do not wait for `2 closed trades` or the old `48h cap`.
2. If the corrected `614d68e...` real-readiness probe has not been run to completion, close MT5/MetaEditor once and run only `START_V69_REAL_READINESS_PROBE_GIT_BASH.sh` on the exact corrected HEAD.
3. Require `V69_ONE_SHOT_EXPECTED_HEAD_BRIDGED=`.
4. Require MetaEditor `0 errors, 0 warnings` for the execution-probe EA.
5. Require actual DEMO BUY + immediate probe-owned close PASS or capture the first exact broker failure.
6. Read the pre-probe signal funnel and classify gating vs order-path integration.
7. If the corrected probe already completed and this dashboard is its automatic frozen-V69 relaunch, obtain the terminal output/result file immediately; no further natural-trade waiting is required.
8. REAL remains a separate fail-closed deployment/risk decision.
