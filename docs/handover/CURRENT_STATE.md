# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Project objective

Mục tiêu dài hạn là production/live trading bằng vốn thật trên Exness sau khi hệ thống được đánh giá đủ readiness. Paper/DEMO là tầng xác nhận, không phải đích cuối.

## Frozen alpha / inherited evidence

Frozen primary: `v46_hl10_thr0p05_breadth4`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 adaptive-state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
Frozen V48 source SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not reopen same-sample breadth/HL/threshold tuning. No Martingale, uncontrolled grid or doubling after loss. Research/strategy risk ceiling remains <=1% per trade.

Historical/alpha validation is inherited for V49 and is not rerun as a separate campaign.

## Active V48 runtime until V49 transition

The accepted V48 DEMO-paper session was started from Windows runtime HEAD `3e5f126772c9c2d378f9b3e09720cc9789d76330`.

Run id:
`v48_demo_paper_forward_v2__XAUUSDm__PERIOD_M15__2026-08-22_10-52-37__471937`

Accepted startup evidence included DEMO account, trade/DLL permissions OFF, timer/dashboard PASS, broker orders 0 and real-money authorization 0.

V49 transition is allowed only while the V48 primary virtual position is FLAT. If it is OPEN, the V49 one-shot fails closed and leaves V48 running.

## V49 — authoritative next milestone

Branch:
`agent/v49-one-shot-demo-rehearsal`

The branch is maintained as one clean commit ahead of the V48 documentation base.

ADR:
`docs/adr/ADR-048-v49-one-shot-production-rehearsal.md`

Plan:
`docs/research/v49_one_shot_demo_rehearsal_plan.md`

V49 collapses the previous post-paper gate ladder into one integrated finite production rehearsal.

Inherited instead of rerun:
- V45/V46 historical robustness work;
- frozen breadth4 identity;
- deterministic V48 parent identity;
- V48 startup/config/compile lessons;
- no-Martingale/no-grid/no-doubling invariant.

V49 one-shot performs in the same campaign:

`frozen virtual intent -> native Exness DEMO order -> automatic close -> OnTradeTransaction reconciliation -> push notification -> fill/request logging -> finite verdict -> one ZIP`

## V49 execution scope

V49 may use MT5 native trade APIs only on `ACCOUNT_TRADE_MODE_DEMO`.

Hard V49 invariants:
- REAL/non-DEMO account -> initialization refusal before a broker request;
- XAUUSDm M15 only;
- dedicated magic `490049`;
- own only its own broker positions;
- foreign/manual positions are never managed;
- DLL imports remain OFF;
- frozen primary virtual book remains signal owner;
- execution adapter does not create a second alpha path;
- real-money authorization remains 0 in V49.

V49 uses `CTrade` for DEMO broker requests and `OnTradeTransaction` as the asynchronous broker-event reconciliation stream. API boolean success is not treated as fill proof; server retcodes and deal events are logged.

Pending-open/pending-close flags, request cooldown and confirmation timeouts prevent repeated order requests while broker state is still converging. A broker-side SL/TP exit while virtual intent still appears OPEN enters a short reconciliation wait rather than immediately reopening another position.

## Simplified one-shot acceptance

This is an execution/operations rehearsal, not another historical-alpha gate.

Minimum useful sample:
- >=3 distinct market-active XAUUSD dates; and
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

`LIVE_CANDIDATE_READY` classification requires minimum sample plus:
- zero real-account guard violation;
- zero duplicate owned entries/positions;
- zero unresolved virtual-vs-broker direction mismatch;
- zero unresolved owned-position reconciliation mismatch;
- no catastrophic execution-loop failure;
- broker request reject ratio <=20%;
- frozen parent identity intact.

At hard stop without the minimum sample, use `INSUFFICIENT_EXECUTION_SAMPLE`.

Spread/slippage/latency are measured and reported rather than creating another tuning loop.

## Phone notifications

V49 uses MetaTrader push notifications via `SendNotification()` when configured. MetaQuotes ID stays in terminal settings and is never stored in Git.

Notify:
- START;
- broker DEMO OPEN confirmation;
- broker DEMO CLOSE confirmation;
- HALT;
- FINAL verdict.

Notification failure is observability evidence only; it does not trigger a duplicate trade request.

## One user task — authoritative workflow

Canonical entrypoint:
`runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

The one task performs, in order:
1. static/secret checks;
2. rebuild frozen V48 parent and generate V49;
3. MetaEditor compile and require `0 errors, 0 warnings` **while the accepted V48 observer is still untouched**;
4. only after compile PASS, inspect the active V48 status;
5. if V48 is OPEN, abort transition and leave V48 running;
6. if V48 is FLAT, close MT5 gracefully with Windows `CloseMainWindow`;
7. copy the final V48 adaptive state into V49 state;
8. write V49 startup config with DEMO AutoTrading enabled and DLL disabled;
9. launch MT5/V49 and require DEMO READY status;
10. start detached supervisor.

This ordering means a V49 build/compile failure does not stop the working V48 observer.

After `V49_ONE_SHOT_STARTED=1`, Git Bash may be closed. Keep the PC, Internet and MT5 running. The detached supervisor waits for FINAL/hard stop and creates one ZIP under `runtime/v49_demo_rehearsal/OUTPUT_V49/` with an internal SHA256 manifest.

## Current acceptance status

Prepared in Git:
- `scripts/build_v49_one_shot_demo_rehearsal_source.py`;
- `runtime/v49_demo_rehearsal/RUN_V49_ONE_SHOT.py`;
- `runtime/v49_demo_rehearsal/SUPERVISE_V49_ONE_SHOT.py`;
- `runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`;
- `tests/test_v49_one_shot_demo_rehearsal_static.py`;
- ADR-048 and V49 plan.

Python syntax for the revised builder/runner was checked during implementation, but there is no current-head GitHub CI status and no Windows MetaEditor evidence yet. V49 is therefore NOT yet claimed as Windows-accepted. First local one-shot must prove static tests + secret scan + MetaEditor `0 errors, 0 warnings` + clean DEMO READY. Native broker automation is not claimed successful until an actual DEMO round trip is observed.
