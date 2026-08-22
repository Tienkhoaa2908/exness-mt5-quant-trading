# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Objective

Long-term project objective: production/live trading after readiness evaluation. V49 is the integrated broker-DEMO production rehearsal used to obtain the final engineering-readiness evidence without rerunning historical alpha research.

## Frozen strategy / inherited evidence

Frozen primary: `v46_hl10_thr0p05_breadth4`.
Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
Frozen V48 source SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not reopen same-sample optimization. No Martingale, uncontrolled grid or doubling after loss.

## Current V48 runtime before transition

Accepted V48 DEMO-paper run may still be active:
`v48_demo_paper_forward_v2__XAUUSDm__PERIOD_M15__2026-08-22_10-52-37__471937`

Runtime HEAD used to start it:
`3e5f126772c9c2d378f9b3e09720cc9789d76330`.

V49 transition is allowed only while the V48 primary virtual position is FLAT. The canonical V49 runner checks this itself. If V48 is OPEN it aborts and leaves V48/MT5 running; rerun the same one-shot later after V48 returns FLAT.

## V49 authoritative branch

`agent/v49-one-shot-demo-rehearsal`

The branch is kept as one clean commit ahead of the V48 documentation base.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-048-v49-one-shot-production-rehearsal.md`
3. `docs/research/v49_one_shot_demo_rehearsal_plan.md`
4. `docs/windows_mt5_exness_setup.md`
5. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`

## V49 one-shot model

`frozen breadth4 virtual intent -> native Exness DEMO order -> automatic broker close -> OnTradeTransaction reconciliation -> phone push -> execution logging -> finite final verdict -> one ZIP`

Historical robustness is inherited rather than rerun.

## V49 hard guards

Native trade APIs are allowed only when:
- account mode is `ACCOUNT_TRADE_MODE_DEMO`;
- symbol is `XAUUSDm`;
- period is M15;
- terminal/MQL AutoTrading is enabled for DEMO broker execution;
- DLL permission is OFF.

REAL/non-DEMO account -> `INIT_FAILED` before any broker request.

Dedicated magic: `490049`.
V49 manages only its own positions/orders. Manual/foreign positions are never closed or modified by V49.
Real-money authorization remains 0 in V49.

Pending open/close requests are guarded so a broker state that has not yet converged cannot cause a duplicate request. `OnTradeTransaction` deal events confirm broker activity; `CTrade` boolean return alone is not treated as fill proof.

## Simplified acceptance

Minimum useful execution sample:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

`LIVE_CANDIDATE_READY` requires minimum sample plus:
- zero real-account guard violation;
- zero duplicate owned position/entry;
- zero unresolved direction/reconciliation mismatch;
- no catastrophic execution-loop failure;
- broker request reject ratio <=20%;
- frozen V48 parent identity preserved.

At hard stop without minimum sample: `INSUFFICIENT_EXECUTION_SAMPLE`.

Spread/slippage/latency are recorded as execution evidence instead of starting another parameter-tuning loop.

## Notifications

V49 uses `SendNotification()` when MetaTrader push notifications are configured. MetaQuotes ID stays in terminal settings and is not committed.

Expected phone events: START, DEMO OPEN, DEMO CLOSE, HALT, FINAL.

## Canonical one-shot command

`bash runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

Execution order is intentionally fail-safe and single-action:
1. static/secret checks;
2. generate and MetaEditor-compile V49 while V48 is still untouched;
3. require compile `0 errors, 0 warnings`;
4. inspect active V48 status;
5. if V48 OPEN -> stop the transition only, leave V48 running;
6. if V48 FLAT -> close MT5 gracefully via `CloseMainWindow`;
7. transition the final V48 adaptive state to V49;
8. launch V49 with DEMO AutoTrading enabled / DLL disabled;
9. require V49 DEMO READY;
10. detach the supervisor.

Thus a build/compile problem does not kill the accepted V48 observer.

After `V49_ONE_SHOT_STARTED=1`, Git Bash may be closed. Keep PC + Internet + MT5 running.

Supervisor:
`runtime/v49_demo_rehearsal/SUPERVISE_V49_ONE_SHOT.py`

Final evidence directory:
`runtime/v49_demo_rehearsal/OUTPUT_V49/`

The supervisor creates one final ZIP containing `bundle_manifest_sha256.txt` after EA FINAL or timeout.

## Acceptance status

V49 source/runner are prepared in Git but are not yet Windows-accepted. Do not claim broker-DEMO automation works until the one-shot proves:
- local static/secret checks PASS;
- MetaEditor `0 errors, 0 warnings`;
- clean DEMO READY startup;
- then at least one actual native DEMO round trip.
