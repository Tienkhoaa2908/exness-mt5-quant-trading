# V48 Hardened Attach Launcher

Date: 2026-08-22

## Scope

This milestone changes only V48 deployment, startup diagnostics, stale-startup recovery, and operational readiness checks. It does not change the frozen `v46_hl10_thr0p05_breadth4` decision logic, risk geometry, V48 generated MQL source, or broker-order prohibition.

V48 remains DEMO-feed + internal virtual USD40 paper execution only. REAL-MONEY LIVE TRADING remains forbidden.

## Incident that triggered this hardening

On the 2026-08-22 Windows launch, all pre-MT5 gates passed: static tests, secret scan, accepted V34/V46 provenance, deterministic V47/V48 build, MetaEditor `0 errors, 0 warnings`, and exact V46 state seeding. MT5 opened XAUUSDm/M15 charts but no V48 dashboard or `V48_DEMO_PAPER_INIT.txt` appeared. The starter timed out.

The old diagnostic collector then printed mostly historical MQL5.community authorization and Virtual Hosting 403 lines from previous days. Those lines were unrelated to the V48 attach attempt and obscured the actual failure layer.

Because `V48_DEMO_PAPER_INIT.txt` is written at the first line of MQL `OnInit`, absence of that file is treated as pre-OnInit attach/load evidence, not a market-closed condition and not a strategy failure.

## Hardened startup path

Canonical compiled source remains under `MQL5/Experts/mt5_quant/V48DemoPaperObserver.*`. Before startup, the hardened launcher verifies the canonical source SHA and non-empty EX5, then copies an exact root-level startup alias:

- `MQL5/Experts/V48DemoPaperObserver.mq5`
- `MQL5/Experts/V48DemoPaperObserver.ex5`

The alias source must retain V48 source SHA `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`, and alias EX5 must hash exactly equal to the canonical compiled EX5. This removes nested Expert-path resolution from the startup-critical path without changing strategy source.

The startup INI uses `Expert=V48DemoPaperObserver`, `Symbol=XAUUSDm`, `Period=M15`, `Enabled=1`, `AllowLiveTrading=0`, and `AllowDllImport=0`. The launcher reads the UTF-16 INI back and verifies every safety/startup key before launching terminal64.

## Launch-scoped diagnostics

Immediately before terminal launch, the launcher records decoded line counts for terminal Journal and MQL5 Experts logs. On attach failure it reads only lines appended after that snapshot. Historical log lines are therefore not re-reported as current evidence.

Unrelated `MQL5.community` authorization and `Virtual Hosting` messages are counted and suppressed from the primary diagnostic body. Diagnostics report:

- exact startup config and SHA;
- root alias EX5 path and SHA;
- whether the exact config name appears in new log lines;
- whether the V48 Expert name appears in new log lines;
- whether `V48_DEMO_PAPER_INIT.txt` exists;
- only launch-scoped terminal/Expert log deltas.

## Stale metadata semantics

A non-empty V48 `run_id` in LATEST or STATUS remains a hard stop: a second session must never be started silently.

If LATEST/STATUS/INIT files exist but both run IDs are blank, they are treated as incomplete startup debris only when the active paper state is still the exact accepted V46 seed SHA. Those metadata files are moved into a timestamped quarantine directory; the active state is preserved.

If an orphan paper state differs from the accepted seed while there is no valid run ID, recovery fails closed because continuity is ambiguous. The launcher never resets such state automatically.

## Market-closed readiness gate

V48 startup must be testable while XAU is closed. `OnInit`, `OnTimer`, status writes, and the chart dashboard do not require a new market tick.

After a valid READY status appears, the hardened launcher records the status file modification time and requires it to advance within 50 seconds. This proves the 30-second timer/status loop is alive even if `TimeCurrent()` itself is unchanged while the market is closed.

Success therefore requires both:

- valid DEMO/safety/candidate/book status with a non-empty run ID; and
- `STATUS_TIMER_REFRESH_PASS=1`.

Only then may the starter print `V48_DEMO_PAPER_RUNNING=1` and `CHART_DASHBOARD=ENABLED`.

## Entrypoints and tests

Canonical Git Bash entrypoint remains:

`runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

It now executes:

`runtime/v48_demo_paper/RUN_V48_DEMO_PAPER_START_HARDENED.py`

Static coverage is split between the original V48 safety/strategy tests and `tests/test_v48_demo_paper_hardened_launcher_static.py`, which covers root-alias deployment, INI self-verification, stale metadata semantics, launch-scoped diagnostics, and the market-close-safe timer gate.

No real-money or broker-order capability is introduced by this milestone.
