# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-01 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

Always resolve the current remote HEAD before giving an operator command. Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` before project work.

## Current objective

Run a short live-market **DEMO smoke validation** of frozen V69 LONG on Exness MT5, prove runtime/broker order-path readiness, collect a small natural forward sample, then review before any later deployment decision.

Safety boundary remains:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only;
- SHORT rejected/disabled;
- REAL authorization false and fail-closed.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Frozen LONG contract:

- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- closed-M1 reclaim cannot order immediately;
- favorable post-confirm separation `>= $1.30` from the fixed stop;
- separation tick cannot order;
- later retest into unchanged cash-risk zone required;
- confirmation age `>=30s`;
- fixed structural stop, no widening/clamp;
- ordering: `POST_ZONE_REVERSAL_CONFIRM -> return -> POST_CONFIRM_SEPARATION -> POST_CONFIRM_RETEST_READY -> POST_CONFIRM_ENTRY_READY -> V64OrderPreflight`.

The `$1.30` and `30s` values are development choices, not globally proven optima.

## Development evidence

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all 10 V68 winners while removing four losers. However, `10/14` V69 losers closed within 60 seconds. Monthly V69 LONG replay is highly regime-concentrated: Sep `-$1.84`, Oct `+$9.15`, Nov `+$1.24`, Dec `-$2.28`, Jan `+$0.87`, Feb-May flat; excluding October the total is `-$2.01`.

V69 was designed after V68 was inspected. The Sep 2025-May 2026 V69 replay is **development evidence, not an independent holdout**.

Current economic research priority remains entry/regime quality first, same-setup re-entry suppression second if cluster evidence confirms it, and harvest/exit changes only if MFE/capture diagnostics show material positive-MFE giveback.

## Current one-shot implementation

Canonical launcher:

`bash runtime/v69_one_shot_prospective_demo/START_V69_ONE_SHOT_PROSPECTIVE_DEMO_GIT_BASH.sh`

Chart EA: `V69FrozenForwardSmokeDashboardLong`

The one-shot performs exact Git-state validation, working-Python probing, static gates, deterministic source generation, MetaEditor compile, exact MQ5/EX5 byte verification, MT5 startup on `XAUUSDm M15`, live heartbeat verification, broker dry-run preflight, silent supervisor startup, and forward evidence collection.

Smoke review target: 2 naturally closed strategy trades or a 48-hour hard cap. Two trades are operational/forward sanity evidence, not statistical proof of profitability.

## Broker-health incident and implemented fix

The previous live DEMO run showed:

- lot `0.01`;
- broker min `0.0100`, step `0.0100`, max `200.0000`;
- trade mode `4`;
- filling flags `3`;
- first `OrderCheck()` false with local error `4756`.

This is **not a lot-size failure**. The old harness checked broker state every 30 seconds but could fail after 12 seconds, allowing one generic startup result to be treated as permanent. It also lost the server `retcode/comment`.

The current health layer now:

- refreshes broker preflight every 5 seconds;
- publishes monotonic `broker_check_seq`;
- checks terminal connection, account trade permission, account EA permission, terminal/MQL permissions, symbol synchronization, trade mode, volume contract, execution mode and filling mode;
- builds the dry-run request according to execution mode;
- records both local `_LastError` and server `retcode/comment`;
- treats bare `4756` with no server retcode as transient initially;
- requires two independent consecutive READY checks;
- requires repeated independent fatal confirmation before permanent BLOCKED;
- permits transient stabilization up to 90 seconds;
- displays `SYSTEM HEALTH: STARTING / READY / BLOCKED` and `BROKER PREFLIGHT` directly on chart;
- distinguishes `awaiting first natural fill` from `EXECUTION VERIFIED`.

The dry-run health layer does not add an order-send path and does not change V69 signal semantics.

## CI state

The V69 forward runtime/static suite passed on code/CI checkpoint `9c2161b937bd7c16e1293c1de295181d18b419df` (`v69-forward-quality` run `33522581398`). All frozen-forward, dashboard, broker-ready, parent-regression, trade-quality and one-shot tests passed.

Two stale workflow literals were corrected during this gate: the workflow had asserted old broker-panel/error wording after the runtime health semantics were intentionally upgraded. This was a CI contract drift, not a strategy defect.

After this state-sync commit, re-check `v69-forward-quality` on the new exact HEAD before operator execution.

## Classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_FORWARD_DIRECTION=LONG_ONLY`

`V69_FORWARD_DEMO_ONLY=1`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`V69_FORWARD_SHORT_ENABLED=0`

`V69_RUNTIME_HEARTBEAT=OBSERVED`

`V69_LOT_0_01_BROKER_SPEC=VALID`

`V69_BROKER_HEALTH_FIX=IMPLEMENTED_CI_PASS_PENDING_WINDOWS_RERUN`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Verify relevant CI is green on the exact post-sync remote HEAD.
2. Operator closes MT5 and MetaEditor once.
3. Fetch/checkout that exact clean HEAD and run only the canonical one-shot.
4. Require MetaEditor `0 errors, 0 warnings`.
5. Require two independent broker checks and chart `SYSTEM HEALTH: READY`.
6. If blocked, use the newly captured account flags + local error + server retcode/comment; do not guess and do not retune strategy.
7. If READY, leave the DEMO smoke running until 2 natural closed strategy trades or the 48-hour cap.
8. Review the final evidence before any later REAL-money decision.
