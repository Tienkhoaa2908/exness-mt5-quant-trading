# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING is forbidden.

V48 is DEMO-feed + internal virtual USD40 paper execution only:
- DEMO account mandatory; real/non-demo account refused;
- READY requires `TERMINAL_TRADE_ALLOWED=0`;
- READY requires `TERMINAL_DLLS_ALLOWED=0`;
- generated source forbids `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, and `#import`;
- no native/external broker-order path may be added;
- `LIVE_AUTHORIZED=0`;
- never `git clean`.

## Active campaign

Branch: `agent/v48-demo-paper-forward`.
Frozen primary: `v46_hl10_thr0p05_breadth4`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
V48 generated MQL SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not retune breadth/HL/threshold on accepted historical samples. ADX/DI remain shadow diagnostics only.
Formal V46 result remains `HOLD`; do not relabel historical evidence.

## Read first

1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-046-v48-failed-init-state-and-terminal-permission.md`
3. `docs/research/v48_hardened_attach_launcher.md`
4. `docs/research/v48_demo_paper_forward_plan.md`
5. `docs/research/v46_expert_breadth_results.md`
6. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

## Current verified failure layer

2026-08-22 Windows evidence proves:
- source/build/compile prerequisites passed;
- startup config was consumed;
- `V48DemoPaperObserver (XAUUSDm,M15)` loaded successfully;
- MQL `OnInit` ran;
- DEMO server was `Exness-MT5Trial6`;
- `TERMINAL_TRADE_ALLOWED=1` / `MQL_TRADE_ALLOWED=1` caused the V48 safety refusal;
- MT5 then deinitialized with reason 8 (`REASON_INITFAILED`).

Therefore do not classify the current problem as pre-OnInit attachment failure or market closure.

The inherited V48 `OnDeinit` saves adaptive state/status/latest even after failed initialization. This produced blank-run-id failed-init debris and paper-state SHA:
`f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`.

No accepted V48 session was established from those attempts.

## Authoritative startup workflow — Hardened V2

Canonical entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

It now runs:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py`

V2 performs:
1. Python/static/secret/provenance/build/compile gates;
2. exact canonical + root-alias source/EX5 checks;
3. failed-init debris classification before fresh seeding;
4. auto-recovery only for exact INIT `STOPPED`, reason `8`, `broker_orders=0`, `live_authorized=0`, XAUUSDm M15, blank run ids;
5. timestamped forensic archive before any recovery;
6. exact accepted V46 state reseed;
7. startup INI with `AllowLiveTrading=0`, `AllowDllImport=0`, `Enabled=0`, `Expert=V48DemoPaperObserver`, XAUUSDm M15;
8. MQL proof that terminal trading and DLL permissions are actually OFF;
9. launch-scoped diagnostics only;
10. valid non-empty run id + candidate/book/safety READY markers;
11. status-file mtime advance within 50 seconds, proving `OnTimer` is alive even while XAU is closed;
12. if startup fails before a valid run id, archive the failure and restore exact V46 seed automatically.

Any non-seed orphan state not matching the exact reason-8 recovery pattern remains fail-closed.
Any non-empty run id blocks a second session.

Expected success markers:
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

If startup fails, use:
`runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`

Do not ask the user to hunt old screenshots or multi-day logs when launch-scoped evidence exists.

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

A clean run may receive `PAPER_OPERATIONAL_PASS`. It does not authorize real-money trading.

## Runtime

Workspace: `D:\v31_mt5_40usd`.

Before startup, manually opened MT5 and MetaEditor must be closed once.

Start:
`bash runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Status after a successful start:
`bash runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`
