# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-01 22:30 (+07)

Read this before modifying Windows/MT5 runtime code.

## Current unresolved / maintenance follow-up

### KM-2026-09-01-01 — repeated server `10019 No money` should fail fast and expose account funds

The broker-health layer currently permits transient stabilization for up to 90 seconds. During the 2026-09-01 DEMO run it captured repeated:

- local `_LastError=4756`;
- server `retcode=10019`;
- server comment `No money`.

This was deterministic insufficient DEMO funds/free margin, not a transient transport event. After DEMO funds/free margin were restored, the same 0.01 preflight produced two consecutive `READY / retcode 0 / Done` checks and runtime became healthy.

Maintenance improvement for a future non-disruptive harness revision:

- classify repeated server retcode `10019` as deterministic insufficient-funds BLOCKED after independent confirmation;
- display/account-log `ACCOUNT_BALANCE`, `ACCOUNT_EQUITY`, `ACCOUNT_MARGIN`, and `ACCOUNT_MARGIN_FREE` so the reason is visible immediately;
- do not spend the full 90-second transient window on a confirmed `10019`;
- do not change V69 strategy/order semantics to solve this observability issue.

Do **not** interrupt the currently healthy smoke run just to add this enhancement.

## Resolved broker/harness incidents

### KF-2026-09-01-01 — generic 4756 was hiding broker `10019 No money`

Initial observation on Exness DEMO `XAUUSDm M15`:

- fixed lot `0.01`;
- broker min `0.0100`, step `0.0100`, max `200.0000`;
- symbol trade mode `4`;
- filling flags `3`;
- `OrderCheck()` false;
- `_LastError=4756`.

First harness revision fixed two instrumentation defects: it stopped concluding permanent failure from one startup sample and began recording `MqlTradeCheckResult.retcode/comment`. The next Windows run then exposed the actual deterministic broker result on repeated independent checks: `retcode=10019`, comment `No money`.

After sufficient DEMO funds/free margin were restored, the exact same health layer returned two consecutive READY checks with local error `0`, server retcode `0`, comment `Done`, and `V69_RUNTIME_SMOKE_VERIFIED=1`.

Conclusion: lot `0.01` is broker-valid; the incident was insufficient funds/free margin. Never interpret local 4756 alone when server retcode/comment is available.

### KF-02 — broken Python launcher candidate

Finding an executable path is insufficient. Probe it by actually executing Python and require 3.10+. Print rejected candidates. This prevents a broken `py.exe -3` from being selected merely because it exists.

### KF-03 — unsupported MQL helper `LongToString`

MetaEditor rejected a generated dashboard even though Python static tests passed. Use MQL5-supported conversions such as `IntegerToString(long)` and maintain generated-source compile/API regressions.

### KF-04 — generated dashboard hash-pin drift

A valid deterministic builder output changed after a dashboard fix while a runner retained an older duplicated generated-source hash. Freeze true parent strategy identity, but verify generated UI via deterministic A/B generation and exact installed bytes instead of redundant ephemeral pins.

### KF-05 — background helpers flashed console windows

Periodic `tasklist.exe` / PowerShell children could create visible windows. Background Windows helpers must use `pythonw.exe` and/or `CREATE_NO_WINDOW`, hidden PowerShell and redirected handles. Static tests guard this.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful inherited `OnInit()` creates status/header telemetry. Zero telemetry after attempted startup means the intended EA did not initialize/attach correctly; do not simply wait for a trade.

### KF-07 — manual EA attachment is avoidable operator risk

Normal workflow is deterministic compile -> exact byte verification -> startup config -> `XAUUSDm M15` launch -> heartbeat. Do not require manual attach when automation can pin the exact expert/chart.

### KF-08 — CI semantic contract drifted behind runtime health wording

After broker-health semantics changed from one-shot `BROKER: READY/BLOCKED` to stable multi-check `SYSTEM HEALTH` + `BROKER PREFLIGHT`, the broker-ready tests passed but `v69-forward-quality` initially failed because workflow grep assertions still expected obsolete literal strings. Inspect failing CI steps before changing runtime or alpha logic.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 losers are fast-loss dominated

V68 LONG: 28 trades, 10W/18L, +$2.87, PF ~1.146, max DD $6.04.

V69 LONG: 24 trades, 10W/14L, +$7.14, PF 1.462, max DD $3.34.

V69 retained all 10 V68 winners while removing four losers, but 10/14 V69 losers closed within 60 seconds. Entry/regime quality remains the first verified research priority.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly LONG: Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat. Excluding October: -$2.01.

### KL-03 — V69 historical replay is development-only

V69 was designed after V68 was inspected. Sep 2025-May 2026 is not an untouched V69 holdout. Do not tune on it again and call the result independent.

### KL-04 — existing profit ratchet has a theoretical sub-$2 harvest gap

Current lineage arms protection around +$2 and attempts to lock about +$1. Do not lower it blindly. Inspect MFE/capture/giveback first; near-zero-MFE fast losers cannot be fixed by earlier profit protection.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor process rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` together with broker `MqlTradeCheckResult.retcode/comment`.
- Server retcode `10019 / No money` means insufficient funds/free margin; do not relabel it as lot-size failure.
- A dry-run READY proves order-request readiness, not an actual future fill. Actual execution requires a natural DEMO fill or separately authorized DEMO probe.
- Resume only the failed layer; do not rerun historical MT5 merely for packaging/harness failures.
- Keep strategy, broker transport and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects.
- REAL money remains fail-closed until a later explicit decision.
