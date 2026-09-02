# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-04 — actual DEMO execution PASS + zero reclaim-confirm localizes the no-trade issue upstream

Successful corrected real-readiness run at code checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` proved actual MT5/broker transport:

- one DEMO BUY `XAUUSDm 0.01` opened successfully;
- open retcode `10009`, comment `done`;
- the probe-owned position closed immediately;
- close retcode `10009`, comment `done`;
- probe terminal exited gracefully;
- frozen V69 automatically relaunched and returned to stable broker/runtime READY.

The pre-probe live signal funnel from the preceding no-trade period showed:

- `POST_ZONE_REVERSAL_CONFIRM=0`;
- `POST_CONFIRM_SEPARATION=0`;
- `POST_CONFIRM_RETEST_READY=0`;
- `POST_CONFIRM_ENTRY_READY=0`;
- natural V69 deals `0`.

Therefore the observed no-trade period did **not** exercise V69 separation/retest/entry-ready/order-send logic. Do not continue blaming generic real-time deployment, lot size, or broker transport for that period.

Current preferred diagnostic is to read the archived event stream and locate the earliest failing upstream transition:

`PENDING_ARM -> MICRO_ENTRY_ARM -> ZONE_TOUCH -> PENETRATION -> POST_ZONE_CONFIRM_WAIT -> POST_ZONE_REVERSAL_CONFIRM`

Use the read-only upstream diagnostic. Do not wait for another natural trade and do not send another forced transport probe unless new transport evidence contradicts the PASS.

### KD-2026-09-03-03 — frozen dashboard still displays obsolete `2 trades / 48h` wait gate

The smoke dashboard can still show `Closed 0/2`, `2 more closed trades`, and `wait until 48h cap`. Those lines are obsolete as project gates.

Current gate is diagnostic localization, not passive waiting. Future dashboard work should label natural-trade counts informational or replace the legacy progress block with current real-readiness/upstream-diagnostic state.

Do not restart a healthy runtime solely to fix this cosmetic text.

### KD-2026-09-03-02 — a forced DEMO fill proves transport, not strategy edge

The isolated probe proves account/symbol/lot/filling/market-order transport can open and close. It does not prove V69 edge, live expectancy, acceptable slippage across regimes, or REAL safety/profitability.

Never convert probe PASS directly into automatic REAL authorization.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades does not locate the fault

Dry-run readiness plus zero trades is ambiguous. Resolve it with a signal funnel plus isolated execution probe, not visual chart interpretation or longer waiting.

That diagnostic has now been completed for the latest window: transport PASS; reclaim-confirm count zero; blocker moved upstream.

## Resolved harness/broker incidents

### KH-2026-09-03-01 — expected-HEAD variable mismatch in nested real-readiness runtime — RESOLVED

First Windows attempt at checkpoint `40115f1aa741720afa360b4cad4216dd0e2ab27e` failed before MT5 with `V69_ONE_SHOT_EXPECTED_HEAD is required` because the new launcher used `V69_REAL_READINESS_EXPECTED_HEAD` while inherited code required the old name.

Fix:

- launcher bridges the inherited variable;
- Python runner normalizes both names before inherited `ensure_repo()` and keeps the bridge through `forward.main()`;
- regression test asserts the cross-module bridge.

Corrected checkpoint `614d68e...` subsequently completed the entire real-readiness probe successfully, so this item is resolved.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Lot `0.01` was valid against broker min `0.01`, step `0.01`, max `200`. Server retcode/comment exposed `10019 / No money`. Restoring DEMO funds produced stable dry-run READY and later an actual open/close PASS.

Never interpret local `4756` alone when server retcode/comment is available.

### KF-02 — broken Python launcher candidate

Finding an executable path is insufficient. Probe candidates by executing Python and require 3.10+. Print rejected candidates.

### KF-03 — unsupported MQL helper `LongToString`

MetaEditor rejected generated dashboard source. Use supported MQL5 conversion APIs and retain generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

A deterministic UI builder changed while a runner retained a stale duplicated generated-source hash. Freeze the true parent strategy identity; validate generated UI through deterministic builds and installed bytes rather than redundant ephemeral pins.

### KF-05 — background helpers flashed console windows

Periodic console executables created visible windows. Background Windows helpers must use hidden/no-window execution and redirected handles.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful inherited `OnInit()` creates status/header telemetry. Zero telemetry after attempted startup means intended EA initialization/attachment failed; do not wait for a trade.

### KF-07 — manual EA attachment is avoidable operator risk

Normal workflow is deterministic compile -> byte verification -> startup config -> `XAUUSDm M15` launch -> heartbeat. Do not require manual attachment when automation can pin it.

### KF-08 — CI semantic contract drifted behind runtime wording

If actual tests pass but a workflow grep expects superseded literal strings, fix the CI contract rather than mutating strategy/runtime semantics to satisfy stale text.

### KF-09 — broker health runner concluded before a second broker refresh

A previous runner could classify BLOCKED at 12 seconds while broker refresh cadence was 30 seconds. Broker readiness now requires independent stable checks and must not conclude before a new broker observation exists.

## Maintenance follow-up

### KM-2026-09-01-01 — confirmed `10019 No money` should fail fast and expose account funds

Future non-disruptive dashboard revision should show balance/equity/used/free margin and classify repeated server `10019` as deterministic insufficient-funds BLOCKED after independent confirmation instead of spending a full transient retry window.

Do not change V69 alpha semantics to mask account funding defects.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all ten V68 winners while removing four losers, but `10/14` V69 losers closed within 60 seconds. Entry/regime quality remains the first verified economic research priority.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly replay: Sep `-$1.84`; Oct `+$9.15`; Nov `+$1.24`; Dec `-$2.28`; Jan `+$0.87`; Feb-May flat. Excluding October: `-$2.01`.

### KL-03 — V69 historical replay is development-only

V69 was designed after V68 was inspected. Sep 2025-May 2026 is not an untouched V69 holdout. Do not tune on it again and call the result independent.

### KL-04 — existing profit ratchet has a theoretical sub-$2 harvest gap

Current lineage arms around +$2 and attempts to lock about +$1. Do not lower it blindly. Inspect MFE/capture/giveback first; near-zero-MFE fast losers cannot be rescued by earlier profit protection.

### KL-05 — session volatility is a conditioning feature, not a trading rule

London/New York overlap and New York morning can have higher activity, but that does not imply positive expectancy. Build DST-aware, past-only session statistics from our own MT5 history and test volatility, spread efficiency, continuation/reversal behavior and MFE/MAE by symbol/session. Do not hard-code `NEW_YORK = TRADE`.

See `docs/research/SESSION_VOLATILITY_RESEARCH.md`.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor process rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` together with broker server retcode/comment.
- Dry-run READY proves request readiness; actual probe PASS proves transport; neither proves strategy edge.
- After prolonged no-trade runtime, inspect stage telemetry instead of waiting blindly.
- Once actual execution transport is proven, do not rerun forced probes unless transport evidence changes.
- Ignore legacy dashboard `2 trades / 48h` as a current project gate.
- Keep strategy, broker transport and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects.
- Exact-HEAD contracts reused across nested runtimes must be bridged and regression-tested end-to-end.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
