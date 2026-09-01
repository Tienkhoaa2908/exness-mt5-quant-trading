# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-01 22:30 (+07)

## User input

User supplied the post-fix MT5 screenshot and complete one-shot log after restoring the DEMO account so broker preflight could be retested.

## Mandatory pre-work state read

Resolved active remote branch and read:

- current branch/remote HEAD;
- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- previous `docs/handover/TURN_SYNC.md`;
- prior exact-HEAD CI state.

## New runtime evidence

Operator ran exact checkpoint `9143c0ece7bd73af01f31e2c37a571941c53edae`.

The run passed all local static gates and compiled `V69FrozenForwardSmokeDashboardLong` with `0 errors, 0 warnings`.

Generated broker-ready dashboard source SHA256:

`1597f966175b15e0509a12ed7d0469c34615d08b8140bf43bc29dbe8627588f7`

EX5 SHA256:

`ba682c26c04edd15c9489d1301d9bef3f08d9460e98c7ae8461766fca9480378`

Two independent broker checks both returned:

- `ready=1`;
- `fatal=0`;
- `detail=READY`;
- local error `0`;
- server retcode `0`;
- server comment `Done`.

Final markers:

- `V69_FORWARD_DEMO_READY=1`;
- `V69_SYSTEM_HEALTH=READY`;
- `V69_BROKER_PREFLIGHT_READY=1`;
- `V69_BROKER_PREFLIGHT_STABLE_CHECKS=2`;
- lot `0.01`, min `0.0100`, step `0.0100`, max `200.0000`;
- `V69_RUNTIME_SMOKE_VERIFIED=1`;
- `V69_FORWARD_SUPERVISOR_PID=3412`;
- `V69_BACKGROUND_CONSOLE_WINDOWS=DISABLED`;
- `V69_ONE_SHOT_STARTED=1`;
- `V69_CHART_DASHBOARD_PINNED=1`;
- LONG only, DEMO only, SHORT disabled, REAL authorization false.

Screenshot also shows chart `SYSTEM HEALTH: READY`, `BROKER PREFLIGHT: READY`, progress 75%, closed trades 0/2, and `awaiting first natural fill`.

## Resolution of previous broker blocker

The immediately preceding run had repeatedly captured local error `4756` plus server `10019 / No money`.

The new successful run demonstrates that after sufficient DEMO funds/free margin were restored, the same 0.01 broker preflight is accepted. Therefore:

- `0.01` is a valid broker lot;
- the previous blocker was insufficient funds/free margin;
- it was not a V69 strategy defect;
- it was not a minimum-lot defect.

## Changes this turn

No strategy/runtime source is changed while the healthy smoke is active.

Canonical docs are updated to:

- mark broker preflight/runtime smoke as healthy;
- move the 4756/10019 incident to resolved status;
- retain a maintenance note to fast-fail repeated `10019` and display account balance/equity/free-margin in a later non-disruptive harness revision;
- make clear that actual execution is still unverified until the first natural V69 DEMO fill.

## Safety status

Unchanged:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only;
- SHORT disabled/rejected;
- REAL authorization false.

## Current blocker

No runtime/broker blocker is active.

The only remaining smoke evidence gate is natural execution/economic evidence: first natural fill, then 2 naturally closed strategy trades or the 48-hour hard cap.

## Next operator action

Do nothing disruptive. Leave MT5 running while the dashboard remains green. Do not rerun the launcher solely because closed trades are zero. Wait for natural strategy execution. Supervisor should package the smoke result automatically after 2 closed trades or the 48-hour cap.
