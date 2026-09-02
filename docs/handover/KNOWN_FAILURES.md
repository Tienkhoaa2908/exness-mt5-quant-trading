# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 (+07)

Read this before modifying Windows/MT5 runtime code.

## Active diagnostic lesson

### KD-2026-09-03-01 — broker READY + live ticks + zero trades does not locate the fault

Observed state:

- frozen V69 attached correctly on `XAUUSDm M15`;
- live ticks and telemetry active;
- broker preflight stable READY twice;
- dry-run OrderCheck accepted lot `0.01`;
- approximately one day passed with no natural V69 fill.

A long wait with zero trades is ambiguous. It can mean either:

1. frozen V69 never reached its final entry state because its setup/reclaim/separation/retest gates were not all satisfied; or
2. V69 reached `POST_CONFIRM_ENTRY_READY` but its integrated preflight/send path failed.

Do **not** keep waiting indefinitely and do not infer either explanation from the chart visually.

Current regression/diagnostic contract:

- snapshot `V64_EVENTS.csv` / `V64_DEALS.csv` and count each V69 stage;
- classify the last reached state using `scripts/analyze_v69_live_signal_path.py`;
- independently prove actual MT5<->broker market execution using the isolated DEMO-only `V69DemoExecutionProbe`;
- execution probe uses unique magic `699901`, lot `0.01`, XAUUSDm only, opens one DEMO BUY then immediately closes only its own position;
- actual probe trades must never be counted as V69 strategy evidence;
- after probe completion, relaunch frozen V69 automatically;
- if `POST_CONFIRM_ENTRY_READY > 0` with no natural V69 deal while the actual execution probe passes, inspect V69 preflight/send events immediately.

This is the preferred fast diagnostic before any REAL-readiness decision.

### KD-2026-09-03-02 — a forced DEMO fill proves transport, not strategy edge

An isolated DEMO execution probe can prove that the account, symbol, lot, filling mode and MT5/broker market-order path can actually open and close. It does **not** prove:

- V69 signal logic is correct;
- historical edge will persist;
- live slippage is acceptable across market regimes;
- a REAL deployment is safe/profitable.

Never convert probe PASS directly into automatic REAL authorization.

## Maintenance follow-up

### KM-2026-09-01-01 — server `10019 No money` should fail fast and expose account funds

Prior DEMO run captured repeated:

- local `_LastError=4756`;
- server `retcode=10019`;
- server comment `No money`.

After DEMO funds/free margin were restored, the exact same 0.01 preflight produced two consecutive `READY / retcode 0 / Done` checks. Therefore `10019` was deterministic insufficient funds/free margin, not a transient transport event and not a lot-step failure.

Future non-disruptive harness revision should:

- classify repeated server `10019` as deterministic insufficient-funds BLOCKED after independent confirmation;
- display/account-log balance, equity, used margin and free margin;
- avoid spending the entire transient retry window on confirmed `10019`;
- never change V69 alpha/strategy semantics to mask account-funding defects.

## Resolved broker/harness incidents

### KF-2026-09-01-01 — generic 4756 was hiding broker `10019 No money`

Lot `0.01` was valid against broker min `0.01`, step `0.01`, max `200`. Instrumentation was improved to retain `MqlTradeCheckResult.retcode/comment`; this exposed server `10019 / No money`. Restoring DEMO funds resolved the blocker and produced stable broker READY.

Never interpret local `4756` alone when server retcode/comment is available.

### KF-02 — broken Python launcher candidate

Finding an executable path is insufficient. Probe it by actually executing Python and require 3.10+. Print rejected candidates. This prevents a broken `py.exe -3` from being selected merely because it exists.

### KF-03 — unsupported MQL helper `LongToString`

MetaEditor rejected a generated dashboard even though Python static tests passed. Use supported MQL5 conversion APIs and retain generated-source compile/API regressions.

### KF-04 — generated dashboard hash-pin drift

A valid deterministic builder changed while a runner retained a stale duplicated generated-source hash. Freeze the true parent strategy identity, but validate generated UI through deterministic A/B builds and exact installed bytes rather than redundant ephemeral pins.

### KF-05 — background helpers flashed console windows

Periodic console executables could create visible windows. Background Windows helpers must use `pythonw.exe` and/or `CREATE_NO_WINDOW`, hidden PowerShell and redirected handles. Static tests guard this.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful inherited `OnInit()` creates status/header telemetry. Zero telemetry after attempted startup means the intended EA did not initialize/attach correctly; do not simply wait for a trade.

### KF-07 — manual EA attachment is avoidable operator risk

Normal workflow is deterministic compile -> exact byte verification -> startup config -> `XAUUSDm M15` launch -> heartbeat. Do not require manual attach when automation can pin the exact expert/chart.

### KF-08 — CI semantic contract drifted behind runtime wording

If actual tests pass but a workflow grep expects superseded literal strings, fix the CI contract rather than changing strategy/runtime semantics to satisfy stale text.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 losers are fast-loss dominated

V68 LONG: 28 trades, 10W/18L, +$2.87, PF ~1.146, max DD $6.04.

V69 LONG: 24 trades, 10W/14L, +$7.14, PF 1.462, max DD $3.34.

V69 retained all ten V68 winners while removing four losers, but 10/14 V69 losers closed within 60 seconds. Entry/regime quality remains the first verified economic research priority.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly LONG: Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat. Excluding October: -$2.01.

### KL-03 — V69 historical replay is development-only

V69 was designed after V68 was inspected. Sep 2025-May 2026 is not an untouched V69 holdout. Do not tune on it again and call the result independent.

### KL-04 — existing profit ratchet has a theoretical sub-$2 harvest gap

Current lineage arms protection around +$2 and attempts to lock about +$1. Do not lower it blindly. Inspect MFE/capture/giveback first; near-zero-MFE fast losers cannot be fixed by earlier profit protection.

### KL-05 — session volatility is a conditioning feature, not a trading rule

London/New York overlap and New York morning can have greater liquidity/activity, but this does not imply positive expectancy for every symbol or setup. Build DST-aware, past-only session statistics from our own MT5 history and test continuation/reversal expectancy, spread efficiency and MFE/MAE by symbol/session. Do not hard-code `NEW_YORK = TRADE`.

See `docs/research/SESSION_VOLATILITY_RESEARCH.md`.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor process rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` together with broker `MqlTradeCheckResult.retcode/comment`.
- Server retcode `10019 / No money` means insufficient funds/free margin; do not relabel it as lot-size failure.
- Dry-run READY proves request readiness, not an actual fill.
- After prolonged no-trade runtime, use signal-funnel + isolated actual DEMO probe instead of waiting blindly.
- Keep strategy, broker transport and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects.
- REAL money remains fail-closed until a separate explicit decision and deployment/risk gate.
