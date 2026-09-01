# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-01

Read this before modifying Windows/MT5 runtime code.

## Current unresolved / active investigation

### KF-2026-09-01-01 — first broker dry-run returned generic 4756

Observed on Exness DEMO `XAUUSDm M15` during V69 broker-ready smoke:

- fixed lot: `0.01`;
- broker volume min: `0.0100`;
- broker volume step: `0.0100`;
- broker volume max: `200.0000`;
- symbol trade mode: `4` (full trading);
- filling flags: `3` (FOK + IOC available);
- `OrderCheck()` call returned false;
- `_LastError=4756` (`ERR_TRADE_SEND_FAILED`).

Important conclusion: **this was not a minimum-lot/lot-step failure**. The broker's own
volume specification accepts `0.01`.

The failed implementation discarded `MqlTradeCheckResult.retcode/comment`, so the
server-side reason was not captured. It also refreshed broker preflight every 30 seconds
but the Python runner permanently failed after 12 seconds with the same result. This
meant one startup check could be misclassified as a permanent broker block before a
second independent `OrderCheck` ever occurred.

Fix contract now implemented on the active branch:

- refresh broker check every 5 seconds;
- expose a monotonic `broker_check_seq`;
- check terminal connection, account trade permission, account EA permission, EA/local
  permissions and symbol synchronization;
- capture both local `_LastError` and server `retcode/comment`;
- construct dry-run request according to `SYMBOL_TRADE_EXEMODE`;
- treat bare 4756 with no server retcode as transient initially;
- require two independent consecutive READY checks before `SYSTEM HEALTH=READY`;
- require repeated independent confirmation before deterministic fatal classification;
- allow transient transport checks up to 90 seconds to stabilize;
- show `SYSTEM HEALTH` directly on the MT5 panel.

Do not claim this incident resolved until Windows MetaEditor compiles the new source and
the new live DEMO run produces stable `SYSTEM HEALTH: READY` or a more specific captured
server retcode/comment.

## Resolved harness incidents

### KF-01 — Python launcher selected a broken `py.exe -3`

Symptom: launcher found `py.exe` but execution failed later.

Rule: every launcher must execute a real probe and require Python 3.10+. Current
preferred fallback on this machine has been Python 3.12.10 at the user's local Python
installation. Print `PYTHON_REJECTED=` for failed candidates and `PYTHON_SELECTED=` only
for a candidate that actually executes.

### KF-02 — dashboard used unsupported `LongToString`

Symptom: MetaEditor compile failure after static Python tests passed.

Fix: use MQL5-supported `IntegerToString(long)` and regression-test generated source.
Also check `OrderCalcProfit` return values to avoid compiler warnings.

### KF-03 — generated dashboard hash pin drift

Symptom: deterministic builder generated a new valid source hash but runner still pinned
an older hardcoded generated hash and failed with `dashboard source drift`.

Rule: do not maintain redundant generated-source hash pins in multiple places. Freeze
true parent strategy identity; verify A/B deterministic generation and exact installed
bytes instead.

### KF-04 — background supervisor flashed Terminal/console windows

Cause: periodic `tasklist.exe` and notification PowerShell helpers spawned visible
console processes.

Fix: use `pythonw.exe`, `CREATE_NO_WINDOW`, hidden PowerShell and redirected standard
handles for background helpers. Regression tests must enforce this.

### KF-05 — `FORWARD_SNAPSHOT_FILES=0` was wrongly easy to interpret as "no trades"

The inherited EA creates headers/status during successful `OnInit()`. Therefore zero
forward telemetry files after an attempted attach means the exact EA did not initialize,
was not attached, or was attached to the wrong environment. It is stronger evidence than
"no trade yet".

Current one-shot avoids manual attach by compiling/copying the exact EA and launching MT5
with a startup config pinned to `XAUUSDm M15`.

### KF-06 — manual MT5 attachment is an avoidable source of operator error

Do not require the user to manually locate/attach the EA when deterministic startup config
can do it. The one-shot launcher owns compile -> byte verification -> startup config ->
MT5 launch -> heartbeat verification.

## Research / trading-system lessons that must not be lost

### KL-01 — V68/V69 surviving losers are heavily fast-loss dominated

Accepted comparison:

- V68 LONG: 28 trades, 10W/18L, +$2.87, PF ~1.146, max DD $6.04;
- V69 LONG: 24 trades, 10W/14L, +$7.14, PF 1.462, max DD $3.34;
- V69 retained the 10 V68 winners while removing four losers;
- 10/14 V69 losers closed within 60 seconds (71.4%).

Implication: current verified priority is entry/regime quality first; same-setup re-entry
suppression second; harvest remains architecturally plausible but requires MFE evidence
before being promoted to the primary failure mode.

### KL-02 — October concentration means V69 edge is regime-sensitive

V69 monthly LONG replay:

- Sep 2025 -$1.84;
- Oct +$9.15;
- Nov +$1.24;
- Dec -$2.28;
- Jan +$0.87;
- Feb-May flat;
- total +$7.14;
- excluding October: -$2.01.

Do not tune repeatedly on the same historical months and call the result independent.

### KL-03 — V69 historical replay is development evidence, not untouched holdout

V69 was designed after inspecting V68. The Sep 2025-May 2026 V69 replay is development
replay. The first independent evidence is prospective/live DEMO after the V69 freeze.

### KL-04 — existing profit ratchet leaves a sub-$2 theoretical harvest gap

Current lineage arms protection around +$2 and attempts to lock about +$1. Positive
trades that never reach +$2 can theoretically round-trip. Do not lower the threshold
blindly; first inspect MFE/capture/giveback diagnostics to determine whether this gap is
actually material.

## Permanent Windows/runtime rules

- Never `git clean`.
- Do not `stash pop` during active evidence/runtime work.
- Explicit UTF-8 text I/O on Windows.
- MetaEditor rc alone is not compile success; require exact source identity + final
  `0 errors, 0 warnings` + non-empty current EX5.
- Terminal process exit/launch alone is not runtime success; require telemetry/heartbeat.
- Resume the failed stage; do not rerun expensive historical MT5 work just to package.
- Strategy thresholds must not be changed to mask harness/broker defects.
- REAL money must remain fail-closed until explicitly authorized in a later deployment
  decision.
