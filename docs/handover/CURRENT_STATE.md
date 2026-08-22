# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Project objective — authoritative

- Mục tiêu dài hạn của dự án là hướng tới production/live trading bằng vốn thật trên Exness sau khi vượt đủ validation, execution, risk và operational gates.
- Paper/DEMO không phải đích cuối; chúng là các tầng xác nhận bắt buộc trước khi một build được đánh giá `LIVE_CANDIDATE_READY`.
- Không promote từ vài ngày PnL dương trực tiếp sang real. Native broker-DEMO parity, measured slippage/spread/delay stress, restart/reconciliation, fault handling và independent risk controls phải được đánh giá trước.
- `LIVE_CANDIDATE_READY` là trạng thái readiness của hệ thống; không phải cơ chế tự động chuyển account hoặc tự động bật live execution.

## Safety / current-phase scope

- V48 hiện tại vẫn là DEMO-feed + internal virtual USD40 paper execution only.
- Native/external broker orders vẫn bị cấm trong V48 hiện tại.
- Không Martingale, uncontrolled grid, hoặc doubling after loss.
- Research/paper stop-risk ceiling hiện tại <=1.00%/trade.
- V48 yêu cầu DEMO account; real/non-demo accounts bị refuse trong MQL `OnInit`.
- Terminal automated-trading permission phải OFF tại READY: `TERMINAL_TRADE_ALLOWED=0`.
- Terminal DLL permission phải OFF: `TERMINAL_DLLS_ALLOWED=0`.
- Generated V48 source cấm `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, và `#import`.
- `LIVE_AUTHORIZED=0` trong V48.
- Never use `git clean`.

Các guard trên là **scope của V48 active campaign**, không còn được diễn giải thành tuyên bố rằng toàn bộ project sẽ vĩnh viễn không hướng tới real-money production.

## Repository / active campaign

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active branch: `agent/v48-demo-paper-forward`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 adaptive-state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

Frozen primary: `v46_hl10_thr0p05_breadth4`.
Formal V46 analyzer status remains `HOLD`; do not rewrite historical evidence as PASS.
Do not reopen same-sample breadth/HL/threshold tuning. ADX/DI remain shadow diagnostics only.

Frozen V48 generated MQL SHA remains:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## ACTIVE V48 SESSION — ACCEPTED STARTUP

The first accepted V48 DEMO-paper session was established on 2026-08-22.

Runtime code identity used to start the session:
- branch: `agent/v48-demo-paper-forward`;
- Windows runtime HEAD: `3e5f126772c9c2d378f9b3e09720cc9789d76330`;
- frozen candidate: `v46_hl10_thr0p05_breadth4`;
- paper book: `usd40_r1p0_cent_continuous`.

Accepted run id:
`v48_demo_paper_forward_v2__XAUUSDm__PERIOD_M15__2026-08-22_10-52-37__471937`

MT5 session start:
`2026.08.22 10:52:37`

Observed READY/status evidence:
- account mode `DEMO`;
- `TERMINAL_TRADE_ALLOWED=0`;
- `MQL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- `MQL_DLLS_ALLOWED=0`;
- balance `$40.000000`;
- equity `$40.000000`;
- healthy HL10 count `3/5`;
- position `FLAT`;
- paper closed trades `0`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

The user-supplied screenshot showed the dashboard on XAUUSDm M15 with `State: RUNNING`, `Breadth: 3/5`, balance/equity $40, FLAT position, heartbeat, `REAL MONEY AUTHORIZED: NO`, and terminal Algo Trading OFF.

This startup occurred while XAU was closed, which is useful operational evidence: `OnInit`, dashboard and the 30-second timer/status loop are functioning without new market ticks.

Do not restart this session merely because the market is closed. Do not start a second V48 session while this run id is active.

See `docs/research/v48_startup_acceptance_2026-08-22.md`.

## Previous startup incident and V2 recovery

Earlier 2026-08-22 journal evidence showed:
- startup config consumed;
- `V48DemoPaperObserver (XAUUSDm,M15)` loaded successfully;
- `OnInit` executed;
- `TERMINAL_TRADE_ALLOWED=1` caused the V48 safety refusal;
- MT5 deinitialized with reason 8 (`REASON_INITFAILED`).

The inherited `OnDeinit` then rewrote state/status/latest despite failed initialization, producing paper-state SHA:
`f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`
with blank run id.

Hardened V2 correctly classified that exact reason-8 pattern, quarantined the failed-init debris, re-seeded the exact accepted V46 state, requested terminal AutoTrading OFF, and then established the accepted session above.

ADR-046 defines the failed-init recovery contract.

## Hardened V2 launcher — authoritative startup workflow

Canonical Git Bash entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`.

It routes through:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py`.

V2 behavior:
- reuses existing static/secret/provenance/build/compile gates;
- keeps root startup alias verification from hardened v1;
- uses startup config with `AllowLiveTrading=0`, `AllowDllImport=0`, `Enabled=0`, `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`;
- MQL `OnInit` independently requires `TERMINAL_TRADE_ALLOWED=0`, `TERMINAL_DLLS_ALLOWED=0`, and DEMO account;
- recognizes non-seed state as auto-recoverable only for exact `STOPPED / reason=8 / broker_orders=0 / live_authorized=0 / XAUUSDm M15 / blank run_id` evidence;
- archives failed-init metadata/state before recovery;
- re-seeds exact accepted V46 state SHA before a fresh session;
- any other non-seed orphan state remains fail-closed;
- if a new startup fails before a valid run id exists, archives the failed attempt and restores the accepted V46 seed automatically;
- preserves launch-scoped diagnostics and suppresses unrelated historical MQL5.community/VPS noise;
- requires READY status plus a subsequent timer-driven status mtime refresh within 50 seconds.

## Current observability notes

`CURRENT_PRICE=0.000` while the primary virtual position is FLAT is not currently treated as a connection failure. In the frozen V48 source, `V48PaperEquity()` only populates the `px` field when the virtual position is open. Do not restart or change MQL during the active session only to make this cosmetic field nonzero.

`STATUS_V48_DEMO_PAPER.py` currently computes `ELAPSED_WEEKDAYS_APPROX` and uses that approximation for `FINITE_GATE_READY`. That is NOT equivalent to the preregistered requirement of >=10 actual XAUUSD trading days. Therefore `FINITE_GATE_READY` is not authoritative for the trading-day criterion until this observability-only issue is corrected or actual trading days are counted from run evidence.

## Finite V48 stop rule

Review when both are true:
- >=10 actual XAUUSD trading days have elapsed since accepted session start; and
- >=20 primary breadth4 paper trades have closed.

Hard maximum: 30 calendar days. Do not auto-extend.

Operational HOLD if:
- paper max DD >10%;
- after >=20 closed trades, SumR < -5R or PF <0.80;
- real-account/trade/DLL guard fails;
- continuity break, duplicate ledger, or evidence/state overwrite occurs.

A clean run may receive `PAPER_OPERATIONAL_PASS`. That status promotes the system only to the next validation layer, not directly to live execution.

## Promotion path toward real-money production

Target sequence:

1. `V48 PAPER_OPERATIONAL_PASS` or equivalent evidence review.
2. Native Exness DEMO broker-order parity using the same frozen strategy decisions.
3. Measure virtual-vs-broker entry/exit parity, spread, slippage, fill delay, rejects and order lifecycle integrity.
4. Stress measured friction, including elevated spread/slippage and execution delay.
5. Restart/reconnect/state-reconciliation/fault tests.
6. Independent risk and kill-switch review.
7. Final readiness decision: `LIVE_CANDIDATE_READY` or `NOT_READY`.

Do not use a positive week alone as a promotion rule.

ADR-047 records this long-term production target and promotion discipline.

## ACTIVE-SESSION OPERATING RULE

While the accepted run id above is active:
- keep MT5 open on the DEMO account;
- keep Algo Trading OFF;
- do not run the START script again;
- do not fetch/reset/reseed solely for documentation changes;
- do not manually edit/delete V48 paper state or metadata;
- use `STATUS_V48_DEMO_PAPER_GIT_BASH.sh` for read-only monitoring;
- package/analyze evidence at appropriate checkpoints or at finite-gate review;
- do not alter the current session into a real-account/live-execution session.

## Runtime

Workspace: `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.

Status only while active:
`runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`

Failure evidence for future startup incidents:
`runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`

Common Files paper paths:
- `mt5_quant\paper\V48_DEMO_PAPER_INIT.txt`;
- `mt5_quant\paper\V48_DEMO_PAPER_STATUS.txt`;
- `mt5_quant\paper\V48_DEMO_PAPER_LATEST.txt`;
- `mt5_quant\paper\v48_demo_paper_state.csv`.
