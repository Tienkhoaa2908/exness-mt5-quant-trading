# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current campaign

Accepted V46 evidence commit:
`655bf2f77503d91d0749d2f5c99cc0ad8678c388`.

Accepted V46 ZIP SHA256:
`ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.

Formal V46 result remains `HOLD` because one preregistered annual-sign gate failed. The breadth4 mechanism is nevertheless frozen for forward paper because it passed 13/14 checks and materially repaired drawdown/regime behavior.

Active branch:
`agent/v48-demo-paper-forward`.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v46_expert_breadth_results.md`
3. `docs/research/v48_demo_paper_forward_plan.md`
4. `docs/research/v47_forward_regime_shadow_plan.md`
5. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

Never `git clean`.

## Safety

REAL-MONEY LIVE TRADING is forbidden in this project.

V48 is DEMO paper only:
- DEMO account required; real accounts hard-refused;
- terminal-level `AllowLiveTrading=0` / `TERMINAL_TRADE_ALLOWED=0` required;
- terminal-level `AllowDllImport=0` / `TERMINAL_DLLS_ALLOWED=0` required;
- generated source forbids `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, and `#import`;
- per-program `MQL_TRADE_ALLOWED` / `MQL_DLLS_ALLOWED` are diagnostic only, because terminal-level permissions are OFF and source has no execution path;
- internal virtual USD40 book only;
- `LIVE_AUTHORIZED=0`.

`Enabled=1` in the MT5 startup config is intentional: it allows the EA to execute while `AllowLiveTrading=0` separately disables automated broker trading.

## Frozen primary

`v46_hl10_thr0p05_breadth4`

- HL10 realized-R EWMA;
- selected expert threshold 0.05;
- breadth health threshold 0.05;
- >=4/5 healthy shadow experts required;
- entries/exits/stop/risk unchanged;
- paper book `usd40_r1p0_cent_continuous`;
- ADX/DI diagnostics are shadow-only.

V46 source SHA:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

Accepted V46 adaptive-state SHA:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

V47 observability-only source SHA:
`7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44`.

V48 v2 demo-paper source SHA:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## V48 v1 attach incident

First V48 launch on 2026-08-22 passed:
- static gates;
- secret scan;
- V34 tape;
- exact V46/V47/V48 deterministic build;
- MetaEditor `0 errors, 0 warnings`;
- exact V46 state seed.

Then it timed out waiting for V48 status. No accepted paper session was established.

V48 v2 changes only operational/observability behavior, not strategy decisions:
- removes the unnecessary requirement that per-program MQL trade/DLL flags themselves be zero;
- keeps terminal global trade/DLL permissions hard-OFF;
- adds `V48_DEMO_PAPER_INIT.txt` from the first line of `OnInit` with explicit refusal reason;
- starter extracts recent terminal/Expert logs on attach failure into `runtime/v48_demo_paper/OUTPUT_V48/v48_mt5_attach_diagnostics.txt`;
- chart dashboard displays breadth, balance, equity, DD, position, entry/current/SL/TP, open R/PnL and heartbeat;
- status adds equity, unrealized PnL and current price.

## V48 state protocol

V48 paper state is isolated at:
`mt5_quant\\paper\\v48_demo_paper_state.csv`.

On first setup, copy the exact accepted V46 end-state into that paper path. Never modify accepted V46 evidence.

Do NOT use the existing V46 source for an automatic partial-August tester catch-up. V46 `OnDeinit` performs an EOM-style forced close and can contaminate state when a test ends mid-month. The missing August observations are recorded as a known seed gap.

Adaptive EWMA state is saved every 30 seconds.

Open virtual position state is not yet fully restart-persistent. Unexpected restart while a primary paper position is open is a `CONTINUITY_BREAK`.

## Finite stop rule

V48 is not open-ended.

Review at >=10 XAUUSD trading days AND >=20 closed breadth4 paper trades.

Hard maximum: 30 calendar days. Stop and review even if trade count is below 20. Do not auto-extend.

Operational HOLD if:
- max paper DD >10%;
- after >=20 trades, SumR < -5R or PF <0.80;
- real-account/terminal-trade/terminal-DLL guard fails;
- continuity break, duplicate ledger, or state/evidence overwrite occurs.

A clean run may receive `PAPER_OPERATIONAL_PASS`. That still does not authorize real-money broker orders in this project.

## Runtime

Workspace: `D:\v31_mt5_40usd`.

Start:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Status:
`runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh`

The starter requires MT5 and MetaEditor closed once. After it reports `V48_DEMO_PAPER_RUNNING=1`, keep MT5 open on the DEMO account and keep terminal AutoTrading OFF.

Paper files under MT5 Common Files:
- `mt5_quant\\paper\\V48_DEMO_PAPER_INIT.txt`;
- `mt5_quant\\paper\\V48_DEMO_PAPER_STATUS.txt`;
- `mt5_quant\\paper\\V48_DEMO_PAPER_LATEST.txt`;
- `mt5_quant\\paper\\v48_demo_paper_state.csv`.
