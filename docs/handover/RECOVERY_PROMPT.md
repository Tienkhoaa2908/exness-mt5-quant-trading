# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING is forbidden.

V48 is DEMO-feed + internal virtual USD40 paper execution only:
- DEMO account mandatory; real/non-demo account refused;
- terminal `AllowLiveTrading=0` / `TERMINAL_TRADE_ALLOWED=0` mandatory;
- terminal `AllowDllImport=0` / `TERMINAL_DLLS_ALLOWED=0` mandatory;
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
2. `docs/research/v48_hardened_attach_launcher.md`
3. `docs/research/v48_demo_paper_forward_plan.md`
4. `docs/research/v46_expert_breadth_results.md`
5. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

## Current failure layer / evidence

On 2026-08-22 Windows launches, source/build/compile/state prerequisites passed, but no accepted V48 session was established.

Verified pre-MT5 evidence included:
- original V48 static tests PASS 10/10;
- secret scan PASS;
- V34 tape PASS;
- exact V46/V47/V48 provenance PASS;
- MetaEditor `0 errors, 0 warnings`;
- exact accepted V46 state seed PASS.

One attempt was blocked by stale blank-run-id metadata. It was safely quarantined and the accepted V46 state was re-seeded.

The subsequent attempt launched MT5 and XAUUSDm/M15 charts but produced no dashboard and no `V48_DEMO_PAPER_INIT.txt`. Because the init file is written at the first line of MQL `OnInit`, classify that attempt as pre-OnInit Expert attach/load failure. Market closure does not explain it: `OnInit`, `OnTimer`, dashboard and status writes must work without new XAU ticks.

The old diagnostic collector surfaced historical MQL5.community/VPS noise and is superseded.

## Hardened launcher — authoritative startup workflow

Canonical entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

The entrypoint now runs:
`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED.py`

The hardened launcher:
1. reuses existing static/secret/provenance/build/compile/state gates;
2. verifies canonical `MQL5/Experts/mt5_quant/V48DemoPaperObserver.mq5/.ex5`;
3. deploys exact root startup aliases `MQL5/Experts/V48DemoPaperObserver.mq5/.ex5`;
4. requires alias source SHA == frozen V48 SHA and alias EX5 hash == canonical EX5 hash;
5. writes UTF-16 `v48_demo_paper_forward_hardened.ini` with `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`, `Enabled=1`, `AllowLiveTrading=0`, `AllowDllImport=0`;
6. reads the INI back and verifies every required startup/safety key before launch;
7. snapshots terminal/Experts log line counts immediately before launch;
8. on failure, reports only launch-scoped log deltas and suppresses unrelated historical MQL5.community/Virtual Hosting noise;
9. refuses a second session if LATEST or STATUS has a non-empty run id;
10. may quarantine blank-run-id startup debris only if active V48 state is still the exact accepted V46 seed;
11. fails closed on orphan non-seed state with no valid run id;
12. requires valid DEMO/safety/candidate/book READY status with a non-empty run id;
13. after READY, requires the status file mtime to advance within 50 seconds, proving the timer loop is alive while the market is closed.

Expected success markers:
- `V48_STARTUP_ALIAS_PASS=1`;
- `V48_CONFIG_SELF_CHECK_PASS=1`;
- `V48_DEMO_PAPER_RUNNING=1`;
- `STATUS_TIMER_REFRESH_PASS=1`;
- `CHART_DASHBOARD=ENABLED`;
- `BROKER_ORDERS=0`;
- `REAL_MONEY_AUTHORIZED=0`.

If attach fails, use only:
`runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`

Do not ask the user for historical screenshots/log hunting when the launch-scoped diagnostic exists.

## State continuity

V48 paper state path:
`mt5_quant\paper\v48_demo_paper_state.csv`.

Accepted V46 evidence is immutable and never modified.

Unexpected restart while a primary virtual position is open remains a `CONTINUITY_BREAK`; V48 does not claim full open-position restart persistence.

Do not auto-reset a non-seed orphan state. Fail closed and inspect continuity evidence.

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

Start only after closing manually opened MT5 and MetaEditor once:
`bash runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Status after a successful start:
`bash runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`
