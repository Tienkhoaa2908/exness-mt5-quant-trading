# V48 Hardened Attach Launcher

Date: 2026-08-22

## Scope

This milestone changes only V48 deployment, startup diagnostics, failed-init recovery, terminal-permission handling, and operational readiness checks. It does not change the frozen `v46_hl10_thr0p05_breadth4` decision logic, risk geometry, V48 generated MQL source, or broker-order prohibition.

V48 remains DEMO-feed + internal virtual USD40 paper execution only. REAL-MONEY LIVE TRADING remains forbidden.

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

Official MetaTrader documentation states that disabling platform Auto Trading prevents Expert Advisors/scripts from trading while they can continue to run for analytical purposes. V48 relies on exactly that mode: the Expert must execute, but broker trading must remain prohibited.

Empirical Exness/MT5 evidence on this machine showed that the prior startup file with:

- `AllowLiveTrading=0`;
- `Enabled=1`;

still resulted in `TERMINAL_TRADE_ALLOWED=1` at V48 `OnInit`.

Hardened V2 therefore requests both controls OFF:

- `AllowLiveTrading=0`;
- `Enabled=0`;
- `AllowDllImport=0`.

The MQL `OnInit` safety gate remains authoritative: V48 can become READY only if `TERMINAL_TRADE_ALLOWED=0`, `TERMINAL_DLLS_ALLOWED=0`, and account mode is DEMO.

No trade API is added. The frozen V48 generated source SHA remains `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Hardened startup path

Canonical compiled source remains under `MQL5/Experts/mt5_quant/V48DemoPaperObserver.*`. Before startup, the launcher verifies the canonical source SHA and non-empty EX5, then copies an exact root-level startup alias:

- `MQL5/Experts/V48DemoPaperObserver.mq5`
- `MQL5/Experts/V48DemoPaperObserver.ex5`

The alias source must retain the frozen V48 source SHA, and alias EX5 must hash exactly equal to the canonical compiled EX5. This removes nested Expert-path resolution from the startup-critical path without changing strategy source.

The V2 startup INI uses `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`, `Enabled=0`, `AllowLiveTrading=0`, and `AllowDllImport=0`. The launcher reads the UTF-16 INI back and verifies every safety/startup key before launching terminal64.

## Failed-init debris recovery

A non-empty V48 `run_id` in LATEST or STATUS remains a hard stop: a second session must never be started silently.

A non-seed state without a valid run id is auto-recoverable only when all of the following evidence is present:

- INIT stage is `STOPPED`;
- INIT reason is `8` (`REASON_INITFAILED`);
- `broker_orders=0`;
- `live_authorized=0`;
- symbol is `XAUUSDm` and period is M15;
- LATEST and STATUS have no non-empty run id.

In that exact case, V2 archives LATEST/STATUS/INIT/state/seed metadata into a timestamped forensic directory, then re-seeds the exact accepted V46 state SHA `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

Any other non-seed orphan state still fails closed.

If a new startup attempt fails before a valid run id exists, V2 archives the failed-start artifacts and restores the exact V46 seed automatically. This prevents another failed `OnInit` / `OnDeinit(reason=8)` cycle from poisoning the next retry.

## Launch-scoped diagnostics

Immediately before terminal launch, the launcher records decoded line counts for terminal Journal and MQL5 Experts logs. On attach failure it reads only lines appended after that snapshot. Historical log lines are therefore not re-reported as current evidence.

Unrelated `MQL5.community` authorization and `Virtual Hosting` messages are counted and suppressed from the primary diagnostic body.

## Market-closed readiness gate

V48 startup must be testable while XAU is closed. `OnInit`, `OnTimer`, status writes, and the chart dashboard do not require a new market tick.

After a valid READY status appears, the launcher records the status file modification time and requires it to advance within 50 seconds. This proves the 30-second timer/status loop is alive even if market prices are static.

Success requires:

- DEMO account;
- `TERMINAL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- frozen candidate/book markers;
- non-empty run id;
- `STATUS_TIMER_REFRESH_PASS=1`.

Only then may the starter print `V48_DEMO_PAPER_RUNNING=1` and `CHART_DASHBOARD=ENABLED`.

## Entrypoints and tests

Canonical Git Bash entrypoint:

`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

It now executes:

`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py`

Static coverage includes:

- original V48 strategy/safety tests;
- V48 hardened launcher v1 tests;
- `tests/test_v48_demo_paper_hardened_v2_static.py` for AutoTrading-off config, reason-8-only recovery, exact V46 reseeding, and failed-start rollback.

No real-money or broker-order capability is introduced by this milestone.
