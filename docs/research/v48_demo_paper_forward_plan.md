# V48 Demo-Paper Forward Campaign

Date: 2026-08-22

## Purpose

Stop the historical-research loop and move the accepted V46 breadth4 mechanism into a finite forward paper campaign on the user's MT5 demo terminal.

V48 is operational validation, not another alpha search.

The frozen primary remains `v46_hl10_thr0p05_breadth4`:
- HL10 realized-R EWMA router;
- selected expert threshold 0.05;
- breadth health threshold 0.05;
- require >=4 of 5 shadow experts healthy before opening paper risk;
- existing entry/exit/stop/risk geometry unchanged;
- virtual USD40 r1.00% continuous paper book;
- no ADX/DI gate is active.

ADX/DI may continue to be logged/analyzed as shadow diagnostics only. They cannot change a V48 decision.

## What "paper" means

The observer runs on the real-time XAUUSDm M15 feed of an MT5 DEMO account and uses the existing internal virtual-book engine. It never submits a broker order.

Hard safety conditions:
- `ACCOUNT_TRADE_MODE_DEMO` is mandatory;
- REAL accounts are rejected in `OnInit`;
- Strategy Tester mode is rejected by the V48 observer (historical tests remain on frozen V46);
- terminal-level automated trading permission must be OFF (`AllowLiveTrading=0`, `TERMINAL_TRADE_ALLOWED=0`);
- terminal-level DLL permission must be OFF (`AllowDllImport=0`, `TERMINAL_DLLS_ALLOWED=0`);
- generated source forbids `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, and `#import`;
- `Enabled=1` is allowed and required so the EA itself can run; enabling EA execution is distinct from allowing broker trading;
- per-program `MQL_TRADE_ALLOWED` / `MQL_DLLS_ALLOWED` are recorded diagnostically but cannot create execution capability because terminal-level permissions are OFF and the source contains no broker/DLL path;
- no native/external broker-order path may be added.

This campaign does not authorize real-money trading.

## V48 v1 startup incident

The first V48 live-paper launch passed:
- static tests;
- secret scan;
- V34 tape verification;
- exact V46 parent/source provenance;
- deterministic V47/V48 build;
- MetaEditor `0 errors, 0 warnings`;
- exact V46 state seed copy.

It then timed out waiting for status. No accepted V48 paper session was created.

The v1 observer required both terminal and per-program trade/DLL flags to be false. MetaTrader exposes these as separate permission layers, so this was unnecessarily strict for a source that contains no trade or DLL execution path.

V48 v2 fixes startup observability and the permission contract without changing strategy decisions:
- only terminal-level trade/DLL permissions are hard startup blockers;
- per-program flags are logged;
- `V48_DEMO_PAPER_INIT.txt` records `ENTER`, `REFUSED`, `READY`, or `STOPPED` and a refusal reason;
- the starter extracts recent terminal/Expert logs if attach fails;
- blind 120-second timeout is replaced by immediate refusal diagnostics when possible.

V48 v2 source SHA:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Realtime chart dashboard

V48 v2 displays directly on the XAUUSDm M15 chart:
- RUNNING state;
- healthy breadth count;
- paper balance;
- paper equity;
- max MTM drawdown;
- current paper position LONG/SHORT/FLAT;
- entry/current/SL/TP;
- open R and unrealized USD PnL;
- heartbeat timestamp;
- explicit `BROKER ORDERS 0` / `REAL MONEY AUTHORIZED: NO` markers.

Dashboard refreshes on ticks and every 30 seconds.

## State continuity

Accepted V46 end-state SHA256:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

If a V48 paper state does not yet exist, setup seeds it from the accepted V46 end-state. The seed is copied to a V48-specific Common Files path and accepted V46 evidence is never modified.

V48 deliberately does **not** run an automatic mid-month historical catch-up using the existing V46 tester source. V46 `OnDeinit` performs an end-of-month-style forced close; using that source for a partial-August catch-up could contaminate adaptive state with artificial closes.

The EWMA router is trade-observation based rather than wall-clock decayed. The missing August observations are recorded as a state-seed gap and are not hidden.

V48 paper state path:
`mt5_quant\\paper\\v48_demo_paper_state.csv`.

Paper latest/status/init paths are isolated from historical-research files.

## Finite campaign stop rule

The campaign is not open-ended.

Evaluate at the first time both of these are true:
- at least 10 XAUUSD trading days have elapsed since the V48 live-paper session start;
- at least 20 primary breadth4 paper trades have closed.

Hard maximum observation horizon: 30 calendar days. If 20 trades have not closed by then, stop and evaluate with the evidence available. Do not automatically extend the campaign.

## Operational pass criteria

`PAPER_OPERATIONAL_PASS` requires all of the following:
- demo-account hard gate passed for the entire session;
- terminal AutoTrading/AllowLiveTrading remained OFF;
- terminal DLL permission remained OFF;
- zero broker-order/DLL API path in source;
- heartbeat/status files remained coherent while the market was open;
- no unexplained duplicate paper trades;
- no state/evidence overwrite of accepted V46 artifacts;
- no continuity break that silently resets an open virtual position;
- trade ledger and paper balance reconcile to the observer status;
- no paper max drawdown above 10% during the finite campaign;
- after >=20 closed trades, SumR is not below -5R and PF is not below 0.80.

The performance thresholds above are kill/hold checks, not alpha-optimization targets.

## Restart rule

The current V48 observer persists adaptive EWMA state every 30 seconds but does not claim full open-position restart recovery. Therefore an unexpected MT5/EA restart while a virtual position is open is a `CONTINUITY_BREAK` and invalidates that session for operational acceptance.

A clean restart while no primary virtual position is open may begin a new paper session; record the new session id. Do not merge broken sessions as if continuous.

## Decision at the end

- `PAPER_OPERATIONAL_PASS`: breadth4 has passed finite forward operational reconciliation. Freeze the evidence and stop tuning on that sample.
- `HOLD`: repair the specific operational/risk failure; do not restart broad historical parameter searching.

Real-money order execution remains outside the authorized scope of this project. V48 deliberately contains no route that can send a broker order.
