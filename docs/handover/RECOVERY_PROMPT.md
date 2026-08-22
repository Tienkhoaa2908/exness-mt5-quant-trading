# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Long-term project objective

Mục tiêu cuối của dự án là hướng tới production/live trading bằng vốn thật trên Exness sau khi hệ thống vượt đủ research, forward, native broker-DEMO execution, friction/stress, reconciliation và risk-control gates.

Paper/DEMO là validation stages, không phải đích cuối.

Không được hiểu mục tiêu này thành quyền chuyển một campaign đang chạy trực tiếp từ paper/demo sang real mà bỏ qua promotion evidence. Trạng thái cuối của quá trình nghiên cứu phải là `LIVE_CANDIDATE_READY` hoặc `NOT_READY`.

## Current safety / phase scope

V48 hiện tại là DEMO-feed + internal virtual USD40 paper execution only:
- DEMO account mandatory; real/non-demo account refused;
- READY requires `TERMINAL_TRADE_ALLOWED=0`;
- READY requires `TERMINAL_DLLS_ALLOWED=0`;
- generated source forbids `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, and `#import`;
- no native/external broker-order path is allowed in V48;
- `LIVE_AUTHORIZED=0` in V48;
- never `git clean`.

Những guard này thuộc **active V48 campaign**, không phải tuyên bố rằng project sẽ mãi mãi chỉ dùng vốn giấy.

## Active campaign

Branch: `agent/v48-demo-paper-forward`.
Frozen primary: `v46_hl10_thr0p05_breadth4`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
V48 generated MQL SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not retune breadth/HL/threshold on accepted historical samples. ADX/DI remain shadow diagnostics only.
Formal V46 result remains `HOLD`; do not relabel historical evidence.

## ACTIVE V48 SESSION — DO NOT START A SECOND ONE

The first accepted V48 session is active.

Runtime code used to start it:
- Windows runtime HEAD: `3e5f126772c9c2d378f9b3e09720cc9789d76330`;
- branch: `agent/v48-demo-paper-forward`.

Accepted run id:
`v48_demo_paper_forward_v2__XAUUSDm__PERIOD_M15__2026-08-22_10-52-37__471937`

Session start:
`2026.08.22 10:52:37`

Accepted startup evidence:
- original V48 static tests PASS 10/10;
- hardened v1 static tests PASS 6/6;
- hardened v2 static tests PASS 5/5;
- secret scan PASS;
- V34 causal tape PASS;
- exact V46/V47/V48 provenance PASS;
- compile `0 errors, 0 warnings`;
- exact failed-init debris classification/quarantine PASS;
- exact accepted V46 state reseed PASS;
- root startup alias PASS;
- V2 startup config self-check PASS;
- account mode DEMO;
- `TERMINAL_TRADE_ALLOWED=0`;
- `MQL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- `MQL_DLLS_ALLOWED=0`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

At the accepted snapshot:
- breadth health was `3/5`;
- balance/equity `$40.00`;
- position `FLAT`;
- closed trades `0`;
- decision `CONTINUE_FINITE_PAPER_CAMPAIGN`.

The user screenshot visibly showed `State: RUNNING`, `Breadth: 3/5`, heartbeat, FLAT position, `REAL MONEY AUTHORIZED: NO`, and terminal Algo Trading OFF.

Do NOT run the START script again while this run id is active. Do NOT fetch/reset/reseed the Windows runtime solely because documentation commits exist upstream. Use STATUS only.

## Read first

1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`
3. `docs/research/v48_startup_acceptance_2026-08-22.md`
4. `docs/adr/ADR-046-v48-failed-init-state-and-terminal-permission.md`
5. `docs/research/v48_hardened_attach_launcher.md`
6. `docs/research/v48_demo_paper_forward_plan.md`
7. `docs/research/v46_expert_breadth_results.md`
8. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

## Previous startup failure — resolved

Earlier 2026-08-22 Windows evidence proved:
- config consumed;
- Expert loaded successfully;
- MQL `OnInit` ran;
- DEMO server `Exness-MT5Trial6`;
- `TERMINAL_TRADE_ALLOWED=1` caused safety refusal;
- MT5 then deinitialized with reason 8 (`REASON_INITFAILED`).

Inherited `OnDeinit` saved state/status/latest after failed initialization, producing blank-run-id paper-state SHA:
`f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`.

Hardened V2 recognized only that exact fully evidenced failed-init pattern, archived it, re-seeded the accepted V46 state and successfully started the current session with terminal AutoTrading OFF.

## Authoritative startup workflow — for a future new V48 session only

Canonical entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

It runs:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py`

V2 performs:
1. Python/static/secret/provenance/build/compile gates;
2. exact canonical + root-alias source/EX5 checks;
3. failed-init debris classification before fresh seeding;
4. auto-recovery only for exact INIT `STOPPED`, reason `8`, `broker_orders=0`, `live_authorized=0`, XAUUSDm M15, blank run ids;
5. timestamped forensic archive before recovery;
6. exact accepted V46 state reseed;
7. startup INI with `AllowLiveTrading=0`, `AllowDllImport=0`, `Enabled=0`, `Expert=V48DemoPaperObserver`, XAUUSDm M15;
8. MQL proof terminal trading/DLL permissions are actually OFF;
9. launch-scoped diagnostics only;
10. valid non-empty run id + candidate/book/safety READY markers;
11. status-file mtime advance within 50 seconds, proving `OnTimer` is alive even while XAU is closed;
12. if startup fails before a valid run id, archive failure and restore exact V46 seed automatically.

Any non-seed orphan state not matching the exact reason-8 pattern remains fail-closed.
Any non-empty run id blocks a second session.

## Current observability caveats

`CURRENT_PRICE=0.000` while FLAT is expected under current frozen V48 observability code because the `px` status field is only populated when a virtual position is open. Do not restart/change MQL merely for this cosmetic field.

`STATUS_V48_DEMO_PAPER.py` still computes `ELAPSED_WEEKDAYS_APPROX` and currently uses it for `FINITE_GATE_READY`. This is not the preregistered >=10 actual XAUUSD trading-day rule. Treat `FINITE_GATE_READY` as non-authoritative for the day-count criterion until actual trading days are counted from run evidence or an observability-only fix is made without disturbing the active session.

## State continuity

V48 paper state path:
`mt5_quant\paper\v48_demo_paper_state.csv`.

Accepted V46 evidence is immutable and never modified.
Unexpected restart while a primary virtual position is open remains a `CONTINUITY_BREAK`; V48 does not claim full open-position restart persistence.

## Finite campaign rule

Review at >=10 actual XAUUSD trading days AND >=20 closed breadth4 paper trades.
Hard maximum: 30 calendar days. Do not auto-extend.

Operational HOLD if:
- paper max DD >10%;
- after >=20 closed trades, SumR < -5R or PF <0.80;
- safety guards fail;
- continuity break, duplicate ledger, or state/evidence overwrite occurs.

A clean run may receive `PAPER_OPERATIONAL_PASS`. Đây là gate để xét promotion sang broker-DEMO native execution, không phải auto-live switch.

## Promotion roadmap toward production/live

Sau V48, sequence mục tiêu là:
1. Native Exness DEMO broker-order parity với frozen decision logic.
2. Virtual-vs-broker parity cho direction, entry/exit, size, SL/TP và order lifecycle.
3. Measure spread/slippage/fill-delay/rejects và stress dưới friction cao hơn.
4. Restart/reconnect/stale-feed/state reconciliation/fault tests.
5. Independent risk limits, kill-switch và operational monitoring review.
6. Final status `LIVE_CANDIDATE_READY` hoặc `NOT_READY`.

Không dùng riêng một tuần có lợi nhuận làm promotion rule.

## Runtime while current session is active

Workspace: `D:\v31_mt5_40usd`.

Read-only status:
`bash runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`

Do not invoke the START script until the current session has been deliberately stopped/reviewed under the finite-campaign protocol.
Do not transform the current V48 session into a real-account/live-execution session.
