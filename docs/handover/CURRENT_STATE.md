# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-01 22:30 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

Always resolve the current remote HEAD before giving an operator command. Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` before project work.

## Current objective

Run a short live-market **DEMO smoke validation** of frozen V69 LONG on Exness MT5. Historical replay already supplies the bulk of development research; this live step is primarily execution/runtime verification plus a small natural forward sample.

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

V69 retained all 10 V68 winners while removing four losers. `10/14` V69 losers closed within 60 seconds. Monthly V69 LONG replay is regime-concentrated: Sep `-$1.84`, Oct `+$9.15`, Nov `+$1.24`, Dec `-$2.28`, Jan `+$0.87`, Feb-May flat; excluding October the total is `-$2.01`.

V69 was designed after V68 was inspected. The Sep 2025-May 2026 V69 replay is **development evidence, not an independent holdout**.

Current economic research priority remains entry/regime quality first, same-setup re-entry suppression second if cluster evidence confirms it, and harvest/exit changes only if MFE/capture diagnostics show material positive-MFE giveback.

## Current one-shot implementation

Canonical launcher:

`bash runtime/v69_one_shot_prospective_demo/START_V69_ONE_SHOT_PROSPECTIVE_DEMO_GIT_BASH.sh`

Chart EA: `V69FrozenForwardSmokeDashboardLong`

The one-shot performs exact Git-state validation, working-Python probing, static gates, deterministic source generation, MetaEditor compile, exact MQ5/EX5 verification, MT5 startup on `XAUUSDm M15`, live heartbeat verification, broker dry-run preflight, silent supervisor startup and forward evidence collection.

Smoke review target: **2 naturally closed strategy trades or a 48-hour hard cap**. Two trades are operational/forward sanity evidence, not statistical proof of profitability.

## Latest Windows runtime — HEALTHY

Operator reran exact branch checkpoint `9143c0ece7bd73af01f31e2c37a571941c53edae` at 2026-09-01 22:29 (+07) after restoring sufficient DEMO funds/free margin.

Observed results:

- Python 3.12.10 selected after broken `py.exe -3` was rejected;
- all local frozen-forward/dashboard/broker-ready/one-shot static gates passed;
- MetaEditor compile: `0 errors, 0 warnings`;
- broker-ready dashboard source SHA256: `1597f966175b15e0509a12ed7d0469c34615d08b8140bf43bc29dbe8627588f7`;
- EX5 SHA256: `ba682c26c04edd15c9489d1301d9bef3f08d9460e98c7ae8461766fca9480378`;
- startup expert copy passed;
- broker health check seq 1: `ready=1`, `detail=READY`, local error `0`, server retcode `0`, comment `Done`;
- broker health check seq 2: same READY result;
- `V69_FORWARD_DEMO_READY=1`;
- `V69_SYSTEM_HEALTH=READY`;
- `V69_BROKER_PREFLIGHT_READY=1`;
- `V69_BROKER_PREFLIGHT_STABLE_CHECKS=2`;
- broker volume contract: lot `0.01`, min `0.0100`, step `0.0100`, max `200.0000`;
- `V69_RUNTIME_SMOKE_VERIFIED=1`;
- silent supervisor started PID `3412`;
- `V69_BACKGROUND_CONSOLE_WINDOWS=DISABLED`;
- `V69_CHART_DASHBOARD_PINNED=1`;
- current chart status: `SYSTEM HEALTH: READY`, `BROKER PREFLIGHT: READY`, `Closed 0`, awaiting first natural strategy fill.

This proves runtime + broker dry-run order-path readiness. It does **not** yet prove an actual natural strategy fill; `EXECUTION VERIFIED` remains pending until a real DEMO V69 order/fill occurs.

## No-money incident — resolved operationally

The preceding run captured the specific broker result that the earlier generic `4756` was hiding:

- local `_LastError=4756`;
- server `retcode=10019`;
- server comment `No money`;
- lot `0.01` itself was valid against min/step/max.

After sufficient DEMO funds/free margin were restored, the exact same 0.01 preflight returned two consecutive `READY / retcode 0 / Done` checks. Therefore the incident was insufficient DEMO funds/free margin, not a lot-step defect and not a V69 strategy defect.

Future harness maintenance should classify repeated server retcode `10019` as a deterministic insufficient-funds blocker and display balance/equity/free-margin diagnostics rather than spending the full transient retry window. Do not interrupt the currently healthy smoke run solely for this observability improvement.

## CI state

Before the successful Windows run, exact checkpoint `9143c0ece7bd73af01f31e2c37a571941c53edae` had `v69-forward-quality`, `v69-quality`, `v68-quality`, and full `quality` all green.

This current state-sync is documentation only; strategy/runtime source is unchanged. The active MT5 process remains pinned to the successfully compiled source from checkpoint `9143c0e...`.

## Classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_FORWARD_DIRECTION=LONG_ONLY`

`V69_FORWARD_DEMO_ONLY=1`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`V69_FORWARD_SHORT_ENABLED=0`

`V69_RUNTIME_HEARTBEAT=OBSERVED`

`V69_LOT_0_01_BROKER_SPEC=VALID`

`V69_BROKER_PREFLIGHT=READY_STABLE_2_CHECKS`

`V69_RUNTIME_SMOKE_VERIFIED=1`

`V69_ACTUAL_EXECUTION_VERIFIED=0_AWAITING_NATURAL_FILL`

`V69_CLOSED_FORWARD_TRADES=0`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. **Do not rerun or restart the healthy smoke merely because closed trades are still zero.**
2. Leave MT5 running while `SYSTEM HEALTH: READY` and `BROKER PREFLIGHT: READY` remain green.
3. Wait for the first natural V69 fill; that changes execution state from `awaiting first natural fill` to `EXECUTION VERIFIED`.
4. End the short smoke review after 2 natural closed strategy trades or the 48-hour hard cap.
5. Supervisor should export the final smoke evidence automatically.
6. Review execution + trade evidence before any strategy change or later REAL-money decision.
7. REAL remains fail-closed until a separate explicit deployment/risk decision.
