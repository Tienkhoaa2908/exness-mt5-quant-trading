# V48 Hardened Attach Launcher

Date: 2026-08-22

## Policy note

This document records a historical V48 paper-only milestone. Project-wide policy is now defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

All trade-permission restrictions below apply to V48 itself. They are not a permanent ban on researching or preparing production/live trading with real capital.

## Scope

This milestone changes only V48 deployment, startup diagnostics, failed-init recovery, terminal-permission handling, and operational readiness checks. It does not change the frozen `v46_hl10_thr0p05_breadth4` decision logic, risk geometry, V48 generated MQL source, or V48 broker-order prohibition.

V48 remains DEMO-feed + internal virtual USD40 paper execution only.

## Evidence from the 2026-08-22 launch sequence

All pre-MT5 gates passed: static tests, secret scan, accepted V34/V46 provenance, deterministic V47/V48 build, MetaEditor `0 errors, 0 warnings`, and exact V46 state seeding.

The decisive MT5 journal evidence later showed that the Expert was not failing at path resolution:
- startup config was consumed;
- `V48DemoPaperObserver (XAUUSDm,M15)` loaded successfully;
- MQL entered `OnInit`;
- `TERMINAL_TRADE_ALLOWED=1` and `MQL_TRADE_ALLOWED=1` were observed;
- V48 correctly refused with `terminal_auto_trading_on` / reason 8;
- MT5 then called `OnDeinit(REASON_INITFAILED=8)`.

The generated V48 source writes `V48_DEMO_PAPER_INIT.txt` at entry to `OnInit`, so the later evidence supersedes the earlier pre-OnInit hypothesis.

The legacy V48 `OnDeinit` path calls `SaveAdaptiveState()`, `WritePaperStatus()`, `WriteManifest()` and `WriteLatest()` even when `OnInit` failed. This produced blank-run-id metadata plus a rewritten V48 paper state SHA `f415050bac4095021a7e1bed579cfffee034bfb288348b30cf3a8beca3524e30`, despite no accepted session ever reaching READY.

This is failed-init debris, not forward paper evidence.

## Terminal AutoTrading semantics

Official MetaTrader documentation states that disabling platform Auto Trading prevents Expert Advisors/scripts from trading while they can continue to run for analytical purposes. V48 relies on exactly that mode: the Expert must execute, but broker trading must remain prohibited **for V48**.

Empirical evidence on this machine showed that the prior startup file with `AllowLiveTrading=0` and `Enabled=1` still resulted in `TERMINAL_TRADE_ALLOWED=1` at V48 `OnInit`.

Hardened V2 therefore requests:
- `AllowLiveTrading=0`;
- `Enabled=0`;
- `AllowDllImport=0`.

The V48 MQL `OnInit` safety gate remains authoritative: V48 can become READY only if `TERMINAL_TRADE_ALLOWED=0`, `TERMINAL_DLLS_ALLOWED=0`, and account mode is DEMO.

No trade API is added to V48. The frozen generated source SHA remains `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Hardened startup path

Canonical compiled source remains under `MQL5/Experts/mt5_quant/V48DemoPaperObserver.*`. Before startup, the launcher verifies the canonical source SHA and non-empty EX5, then copies an exact root-level startup alias.

The V2 startup INI uses `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`, `Enabled=0`, `AllowLiveTrading=0`, and `AllowDllImport=0`. The launcher reads the UTF-16 INI back and verifies every safety/startup key before launching terminal64.

## Failed-init debris recovery

A non-empty V48 `run_id` in LATEST or STATUS remains a hard stop for starting a second V48 session.

A non-seed state without a valid run id is auto-recoverable only when exact reason-8 failed-init evidence is present, including `broker_orders=0`, `live_authorized=0`, XAUUSDm M15 and no accepted run id.

In that exact case, V2 archives artifacts before re-seeding the exact accepted V46 state SHA `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

Any other non-seed orphan state still fails closed.

## Launch-scoped diagnostics

Immediately before terminal launch, the launcher records decoded line counts for terminal Journal and MQL5 Experts logs. On attach failure it reads only lines appended after that snapshot.

Unrelated historical authorization/hosting messages are suppressed from the primary diagnostic body.

## Market-closed readiness gate

V48 startup must be testable while XAU is closed. `OnInit`, `OnTimer`, status writes, and the chart dashboard do not require a new market tick.

Success requires DEMO account, terminal trade/DLL permissions OFF, frozen candidate/book markers, non-empty run id and timer/status refresh.

## Entrypoints and tests

Canonical Git Bash entrypoint:
`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

Static coverage includes original V48 strategy/safety tests, hardened launcher tests and reason-8 recovery tests.

No real-money or broker-order capability was introduced by this historical V48 milestone. Later milestones are governed by ADR-049 and may explicitly research production/live deployment.
