# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN in this project.
- Research/paper stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Native/external broker orders remain forbidden.
- Historical validation uses Strategy Tester with `AllowLiveTrading=0`, `AllowDllImport=0`.
- V48 may run on a DEMO live feed only.
- V48 startup config sets terminal-level `AllowLiveTrading=0`, `AllowDllImport=0`; generated MQL source contains no `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or `#import` path.
- Real accounts are hard-refused in MQL `OnInit`.
- `LIVE_AUTHORIZED=0`.
- Never use `git clean`.

## Repository / campaign

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
V47 forward-shadow design commit: `360e4c8bed642c1a1168ebe8982bee8bffa3a08c`.
Active campaign branch: `agent/v48-demo-paper-forward`.

## Accepted V46 mechanism

Formal analyzer status remains `HOLD` because one preregistered annual-sign gate failed. Do not rewrite that historical result.

Frozen primary: `v46_hl10_thr0p05_breadth4`.

Key accepted evidence:
- full cold-start $40 -> $106.947120;
- +167.3678% total;
- annualized +21.344869%;
- max MTM DD 16.5983%;
- PF 1.281739;
- 825 evaluation trades;
- worst full year -0.810156%;
- worst rolling-12m -1.946983%;
- 2022 -0.744202%;
- 2023 -0.810156%;
- 2024 +5.179345%;
- 2025 +42.785951%;
- 2026 Jan-Jul +80.829731%.

Decision: freeze breadth4. Do not reopen historical breadth/HL/threshold tuning on the accepted sample.

Canonical V46 source SHA:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

Accepted V46 adaptive state SHA:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

## V48 demo-paper campaign

V48 ends the historical-research loop and runs frozen breadth4 on the real-time XAUUSDm/M15 feed of the MT5 DEMO account using the existing internal virtual-book engine.

It is not broker demo order execution. There is no broker-order route in source.

Frozen strategy behavior:
- HL10 realized-R EWMA expert router;
- selected-expert threshold 0.05;
- breadth health threshold 0.05;
- require >=4/5 healthy experts before new paper risk;
- entries/exits/stop/risk unchanged;
- virtual book `usd40_r1p0_cent_continuous`;
- ADX/DI remain shadow diagnostics only.

## V48 attach incident and v2 fix

The first V48 paper launch on 2026-08-22 passed static gates, exact source build, MetaEditor `0 errors, 0 warnings`, V34 tape verification and V46 state seeding, then timed out waiting for paper status. No accepted paper session was established.

The v1 observer over-constrained startup by requiring both terminal-level permissions and per-program `MQL_TRADE_ALLOWED` / `MQL_DLLS_ALLOWED` to be false. MetaTrader has separate terminal and per-program permission layers. V48 v2 uses the effective safety boundary instead:
- DEMO account mandatory;
- terminal `TERMINAL_TRADE_ALLOWED` must be false;
- terminal `TERMINAL_DLLS_ALLOWED` must be false;
- source-level broker/DLL execution APIs are forbidden;
- per-program MQL permission flags are logged as diagnostics but do not decide whether the non-trading observer may run.

The startup config deliberately has `Enabled=1` so Expert Advisors can execute, while `AllowLiveTrading=0` prevents automated broker trading. These are separate MetaTrader settings.

V48 v2 adds:
- `V48_DEMO_PAPER_INIT.txt` written from the first line of `OnInit`, including refusal reason and all relevant permission flags;
- automatic terminal/Expert log extraction on attach failure;
- direct chart dashboard via `Comment()` showing breadth, balance, equity, DD, position, entry/current/SL/TP/open-R/PnL and heartbeat;
- realtime dashboard refresh on ticks and every 30 seconds;
- status fields for equity, unrealized PnL and current price.

V48 deterministic source chain:
- V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- V47 observability-only source SHA `7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44`;
- V48 v2 source SHA `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

V48 does not perform a partial-August tester catch-up because V46 `OnDeinit` force-closes positions like EOM and could contaminate state. It seeds the exact accepted V46 end-state into a V48-specific paper state and records the gap explicitly.

## Finite stop rule

V48 is not open-ended.

Review when both are true:
- >=10 XAUUSD trading days have elapsed; and
- >=20 primary breadth4 paper trades have closed.

Hard maximum: 30 calendar days. Stop and review even if trade count is below 20. Do not auto-extend.

Operational risk HOLD if:
- paper max DD >10%; or
- after >=20 closed trades, SumR < -5R or PF <0.80; or
- a continuity break, duplicate ledger, or state/evidence overwrite occurs.

A clean campaign may be labeled `PAPER_OPERATIONAL_PASS`. That still does not authorize real-money broker orders in this project.

## Runtime

Workspace: `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.

V48 entrypoints:
- `runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`;
- `runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`.

If V48 fails to attach, read:
- `runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`;
- Common Files `mt5_quant\paper\V48_DEMO_PAPER_INIT.txt`.
