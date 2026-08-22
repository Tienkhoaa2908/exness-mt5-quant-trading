# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety — authoritative

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- V48 is DEMO-feed + internal virtual USD40 paper execution only.
- Native/external broker orders remain forbidden.
- No Martingale, uncontrolled grid, or doubling after loss.
- Research/paper stop-risk ceiling remains <=1.00%/trade.
- V48 requires a DEMO account; real/non-demo accounts are refused in MQL `OnInit`.
- Terminal automated-trading permission must be OFF at READY: `TERMINAL_TRADE_ALLOWED=0`.
- Terminal DLL permission must be OFF: `TERMINAL_DLLS_ALLOWED=0`.
- Generated V48 source forbids `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, and `#import`.
- `LIVE_AUTHORIZED=0`.
- Never use `git clean`.

## Repository / active campaign

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active branch: `agent/v48-demo-paper-forward`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 adaptive-state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

Frozen primary: `v46_hl10_thr0p05_breadth4`.
Formal V46 analyzer status remains `HOLD`; do not rewrite historical evidence as PASS.
Do not reopen same-sample breadth/HL/threshold tuning. ADX/DI remain shadow diagnostics only.

## V48 purpose

V48 observes frozen breadth4 on the real-time Exness DEMO `XAUUSDm` M15 feed using the existing internal virtual-book engine.

It does not submit broker demo orders. It does not submit real-money orders.

Frozen V48 generated MQL SHA remains:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Current hardening changes deployment/recovery/observability only; strategy decisions and risk geometry are unchanged.

## 2026-08-22 decisive startup evidence

Pre-MT5 gates were verified on Windows:
- original V48 static tests PASS 10/10;
- hardened v1 static tests PASS 6/6;
- secret scan PASS;
- V34 causal tape PASS;
- exact V46/V47/V48 provenance PASS;
- MetaEditor `0 errors, 0 warnings`;
- accepted V46 state seed was initially available.

Later journal evidence superseded the earlier pre-OnInit hypothesis:
- startup config was consumed;
- `V48DemoPaperObserver (XAUUSDm,M15)` loaded successfully;
- `OnInit` executed;
- account mode was DEMO and server was `Exness-MT5Trial6`;
- `TERMINAL_TRADE_ALLOWED=1` and `MQL_TRADE_ALLOWED=1` were observed;
- V48 correctly refused initialization because terminal AutoTrading was ON;
- MT5 reported initialization failure and called deinitialization with reason 8 (`REASON_INITFAILED`).

Therefore the current root cause is terminal trading permission, not Expert path resolution, market closure, compile failure, or alpha logic.

## Failed-init state contamination

The inherited V48 `OnDeinit` executes `SaveAdaptiveState()`, `WritePaperStatus()`, `WriteManifest()` and `WriteLatest()` even after `OnInit` returns `INIT_FAILED`.

That failed-init deinit path rewrote the V48 paper state to:
`f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`
while leaving `run_id` blank.

No accepted V48 forward session was created. The `f415...` state is failed-init debris, not forward evidence.

ADR-046 defines the recovery contract.

## Hardened V2 launcher — authoritative workflow

Canonical Git Bash entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`.

It routes through:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py`.

V2 behavior:
- reuses existing static/secret/provenance/build/compile gates;
- keeps root startup alias verification from hardened v1;
- uses startup config with `AllowLiveTrading=0`, `AllowDllImport=0`, `Enabled=0`, `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`;
- MQL `OnInit` still independently requires `TERMINAL_TRADE_ALLOWED=0`, `TERMINAL_DLLS_ALLOWED=0`, and DEMO account;
- recognizes non-seed state as auto-recoverable only for exact `STOPPED / reason=8 / broker_orders=0 / live_authorized=0 / XAUUSDm M15 / blank run_id` evidence;
- archives failed-init metadata/state before recovery;
- re-seeds exact accepted V46 state SHA before a fresh session;
- any other non-seed orphan state remains fail-closed;
- if a new startup fails before a valid run id exists, archives the failed attempt and restores the accepted V46 seed automatically;
- preserves launch-scoped diagnostics and suppresses unrelated historical MQL5.community/VPS noise;
- requires READY status plus a subsequent timer-driven status mtime refresh within 50 seconds, so market-closed startup is still testable.

Expected success markers:
- `V48_FRESH_SESSION_SEED_PASS=1`;
- `V48_STARTUP_ALIAS_PASS=1`;
- `V48_V2_CONFIG_SELF_CHECK_PASS=1`;
- `V48_V2_TERMINAL_AUTOTRADING_REQUESTED_OFF=1`;
- `V48_DEMO_PAPER_RUNNING=1`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

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

A clean run may receive `PAPER_OPERATIONAL_PASS`. That still does not authorize real-money broker orders.

## Runtime

Workspace: `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.

Start:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Status:
`runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`

Failure evidence:
`runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`

Common Files paper paths:
- `mt5_quant\paper\V48_DEMO_PAPER_INIT.txt`;
- `mt5_quant\paper\V48_DEMO_PAPER_STATUS.txt`;
- `mt5_quant\paper\V48_DEMO_PAPER_LATEST.txt`;
- `mt5_quant\paper\v48_demo_paper_state.csv`.
