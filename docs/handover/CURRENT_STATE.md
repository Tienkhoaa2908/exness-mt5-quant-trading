# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety — authoritative

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- V48 is DEMO-feed + internal virtual USD40 paper execution only.
- Native/external broker orders remain forbidden.
- No Martingale, uncontrolled grid, or doubling after loss.
- Research/paper stop-risk ceiling remains <=1.00%/trade.
- V48 requires a DEMO account; real/non-demo accounts are refused in MQL `OnInit`.
- Terminal automated-trading permission must remain OFF: `AllowLiveTrading=0` / `TERMINAL_TRADE_ALLOWED=0`.
- Terminal DLL permission must remain OFF: `AllowDllImport=0` / `TERMINAL_DLLS_ALLOWED=0`.
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

Do not reopen same-sample breadth/HL/threshold tuning. ADX/DI remain shadow diagnostics only.

## Accepted V46 mechanism

Formal V46 analyzer status remains `HOLD`; do not rewrite historical evidence as PASS.

Key accepted evidence for breadth4:
- full cold-start `$40 -> $106.947120`;
- total +167.3678%;
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

The mechanism is frozen for finite forward operational validation, not declared profitable or production-ready.

## V48 purpose

V48 stops the historical optimization loop and observes frozen breadth4 on the real-time Exness DEMO `XAUUSDm` M15 feed using the existing internal virtual-book engine.

It does not submit broker demo orders. It does not submit real-money orders.

V48 generated source SHA remains:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

The hardened-launch milestone changes deployment/observability only; strategy decisions, risk geometry and generated MQL are unchanged.

## 2026-08-22 startup incidents

Pre-MT5 gates were verified on Windows:
- original V48 static tests PASS 10/10;
- secret scan PASS;
- V34 causal tape PASS;
- exact V46 source provenance PASS;
- deterministic V47/V48 source build PASS;
- MetaEditor `0 errors, 0 warnings`;
- accepted V46 state seed PASS.

A stale blank `run_id` metadata guard first blocked startup. That debris was quarantined and the exact accepted V46 state was re-seeded.

The next launch opened MT5/XAUUSDm charts but produced no V48 dashboard and no `V48_DEMO_PAPER_INIT.txt`; the old runner timed out. Its diagnostic collector incorrectly surfaced historical MQL5.community/VPS noise from previous days. Because the init diagnostic is written at the first line of MQL `OnInit`, this is classified as a pre-OnInit Expert attach/load problem, not a market-closed problem and not an alpha failure.

No accepted V48 forward session has yet been established from those failed attempts.

## Hardened V48 launcher

Canonical Git Bash entrypoint remains:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`.

It now routes through:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED.py`.

Hardening contract:
- verify canonical V48 source SHA and non-empty compiled EX5;
- copy exact root startup aliases `MQL5/Experts/V48DemoPaperObserver.mq5/.ex5` so startup does not depend on nested Expert-path resolution;
- require root alias source SHA == frozen V48 source SHA and alias EX5 hash == canonical EX5 hash;
- write `v48_demo_paper_forward_hardened.ini` with `Expert=V48DemoPaperObserver`, XAUUSDm M15, `Enabled=1`, `AllowLiveTrading=0`, `AllowDllImport=0`;
- read the UTF-16 INI back and verify all startup/safety keys before terminal launch;
- snapshot terminal/Experts log line counts before launch and diagnose only post-launch deltas;
- suppress unrelated MQL5.community authorization / Virtual Hosting noise from the primary diagnostic body;
- non-empty LATEST/STATUS `run_id` remains a hard duplicate-session stop;
- blank-run-id startup debris may be timestamp-quarantined only when active paper state is still the exact accepted V46 seed;
- orphan non-seed state without a valid run id fails closed and is never auto-reset;
- valid READY status requires DEMO/safety/candidate/book markers plus non-empty run id;
- after READY, status file mtime must advance within 50 seconds, proving the 30-second timer loop works even while XAU is closed.

Success markers include:
- `V48_STARTUP_ALIAS_PASS=1`;
- `V48_CONFIG_SELF_CHECK_PASS=1`;
- `V48_DEMO_PAPER_RUNNING=1`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

See `docs/research/v48_hardened_attach_launcher.md`.

## Finite V48 stop rule

V48 is not open-ended.

Review when both are true:
- >=10 actual XAUUSD trading days have elapsed since accepted session start; and
- >=20 primary breadth4 paper trades have closed.

Hard maximum: 30 calendar days. Do not auto-extend.

Operational HOLD if:
- paper max DD >10%; or
- after >=20 closed trades, SumR < -5R or PF <0.80; or
- real-account/trade/DLL guard fails; or
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
