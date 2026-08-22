# Windows MT5 / Exness — V48 DEMO paper workflow

Updated: 2026-08-22

Broker environment: Exness Technologies Ltd.; DEMO account only; server observed `Exness-MT5Trial6`; symbol `XAUUSDm`; timeframe M15.

REAL-MONEY LIVE TRADING is forbidden. V48 does not submit broker demo orders either; it uses a real-time DEMO feed plus an internal virtual USD40 paper book.

Canonical branch:
`agent/v48-demo-paper-forward`

Canonical Git Bash entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Canonical status entrypoint:
`runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`

## Frozen strategy

Primary:
`v46_hl10_thr0p05_breadth4`

Do not retune breadth/HL/threshold on accepted historical evidence. ADX/DI remain shadow diagnostics only.

Frozen V48 generated MQL SHA256:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`

Accepted V46 adaptive-state SHA256:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`

## Safety contract

V48 READY requires all of the following:
- DEMO account mode;
- `TERMINAL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- generated source contains no `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or `#import` path;
- candidate is frozen breadth4;
- virtual book is `usd40_r1p0_cent_continuous`;
- `broker_orders=0`;
- `live_authorized=0`.

Never enable Algo Trading for V48. Never enable DLL imports.

## 2026-08-22 root cause

The important Windows journal evidence is:
- startup config was consumed;
- `V48DemoPaperObserver (XAUUSDm,M15)` loaded successfully;
- MQL `OnInit` executed;
- `TERMINAL_TRADE_ALLOWED=1` was observed;
- V48 refused initialization as designed;
- MT5 then deinitialized with reason 8 (`REASON_INITFAILED`).

The previous startup config used `AllowLiveTrading=0` but also `Enabled=1`; on this installation that left terminal trading permission ON at `OnInit`.

Hardened V2 therefore requests:
- `AllowLiveTrading=0`;
- `Enabled=0`;
- `AllowDllImport=0`.

MetaTrader documentation states that when platform Auto Trading is disabled, Expert Advisors/scripts can continue to work but cannot execute trading operations. V48 uses that analytical-only mode.

## Failed-init state recovery

The inherited V48 `OnDeinit` writes adaptive state/status/latest after failed `OnInit`. A reason-8 failed startup produced blank-run-id state SHA:
`f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`.

This is not accepted forward evidence.

Hardened V2 automatically recovers only when the exact failure signature is present:
- INIT `stage=STOPPED`;
- `reason=8`;
- `broker_orders=0`;
- `live_authorized=0`;
- XAUUSDm M15;
- no non-empty run id in LATEST or STATUS.

Recovery is archive-first, never delete-first. Failed artifacts are moved to a timestamped forensic directory, then the exact accepted V46 state is reseeded.

Any other non-seed orphan state fails closed.

If a new startup fails before a valid run id exists, V2 archives that attempt and restores the accepted V46 seed automatically.

## Hardened V2 startup sequence

1. Close manually opened MT5 and MetaEditor.
2. Run the canonical Git Bash entrypoint.
3. Static/secret/provenance gates run first.
4. V48 source is deterministically regenerated and compile evidence is verified/reused.
5. Failed-init debris is classified and, only if eligible, archived/recovered.
6. Exact accepted V46 state is required before fresh launch.
7. Canonical V48 source/EX5 is copied to a root startup alias and hashes are verified.
8. UTF-16 startup INI is written and read back for exact safety keys.
9. MT5 launches on XAUUSDm M15.
10. MQL `OnInit` must prove DEMO + terminal trading OFF + DLL OFF.
11. READY status must contain a non-empty run id and frozen candidate/book markers.
12. Status file mtime must advance within 50 seconds, proving `OnTimer` is alive even while XAU is closed.

Expected success markers include:
- `V48_FRESH_SESSION_SEED_PASS=1`;
- `V48_STARTUP_ALIAS_PASS=1`;
- `V48_V2_CONFIG_SELF_CHECK_PASS=1`;
- `V48_V2_TERMINAL_AUTOTRADING_REQUESTED_OFF=1`;
- `V48_DEMO_PAPER_RUNNING=1`;
- `TERMINAL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

## Failure evidence

Use:
`runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`

The hardened diagnostic is launch-scoped. Historical MQL5.community authorization and Virtual Hosting 403 noise is not treated as current V48 failure evidence.

## Market closed

Market closure is not a blocker for startup validation. `OnInit`, `OnTimer`, dashboard rendering and status writes must work without a new XAU tick.

No paper trade is expected while the market is closed, but V48 must still reach READY and refresh its status timer.

## Finite campaign

Review only when both are true:
- >=10 actual XAUUSD trading days since accepted session start;
- >=20 closed primary breadth4 paper trades.

Hard stop: 30 calendar days. Do not auto-extend.

A clean result may be labeled `PAPER_OPERATIONAL_PASS`; this never authorizes real-money trading.
