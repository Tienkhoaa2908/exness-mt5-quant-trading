# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 02:25 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is a selector/regime result, not permission to enable SHORT

Latest operator run at checkpoint `931caf8949564ecaad65a524a9f55f16f044593d` found, in the richest preserved `V64_ENTRY_EVAL.csv` source:

- 46 evaluation rows;
- `decision_reason=short_edge` on 46/46;
- `selected_direction=-1` on 46/46;
- `reject_reason=direction_isolated_out` on 46/46;
- no `PENDING_ARM` or later pending/reclaim event.

Inherited selector code only returns `short_edge` when the selector-defined short HTF regime, at least one short trigger, the minimum short score and the minimum short-vs-long score edge all pass. Therefore these 46 rows were not arbitrarily labeled SHORT; frozen LONG-only direction isolation rejected selector-qualified opposite-direction candidates by design.

Do not react by:

- enabling the historically rejected SHORT path;
- loosening LONG direction/regime gates merely to force turnover;
- blaming broker transport, reclaim, separation or retest for these rows.

The correct next question is whether this evidence represents the whole preserved period or only the richest archive root.

Raw row totals across FILE_COMMON roots may duplicate the same evaluations because archive rotation copies telemetry. The observed raw total `83` across four roots must be exact-row deduplicated before selector frequencies are interpreted as a market sample.

Regression/guard:

- diagnostic v4 aggregates all ENTRY_EVAL roots;
- exact duplicate rows are removed;
- it reconstructs selector HTF regime and trigger predicates from logged columns;
- it reports score relation, H1/H4 distributions, direction by regime/trigger, component directions and per-root summaries;
- a result where all unique rows are short-edge in short HTF regime is classified as internally consistent LONG-only abstention, while SHORT stays disabled.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

A read-only upstream run examined 8 preserved V69 sources and found zero `V64_EVENTS.csv` data rows, including `PENDING_ARM=0` and every later pending/reclaim stage at zero.

This proves that no **instrumented pending-state event** occurred. It does not prove that `BuildFeatures`/`SelectDirection` found no candidate.

Code lineage shows several paths before `PENDING_ARM` that do not create a pending event:

- `SelectDirection` can return `d==0` and `EvaluateBar` returns immediately;
- opposite selected direction can be recorded only in `V64_ENTRY_EVAL.csv` as `direction_isolated_out`;
- `V64ClassifyArchetype` can reject as `no_complete_archetype` and write only `V64_ENTRY_EVAL.csv`;
- raw M15 stop geometry can reject as `invalid_arm_structural_stop` and write only `V64_ENTRY_EVAL.csv`;
- only a successful arm emits `PENDING_ARM`.

Do not equate empty event telemetry with absence of visual/selector opportunities. Inspect `V64_ENTRY_EVAL.csv` before changing strategy thresholds.

If ENTRY_EVAL is also empty, observability is insufficient before the `d==0` return. The next step is an observability-only M15 `EvaluateBar` tracer, not threshold tuning.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes the no-trade issue upstream

Successful corrected real-readiness run at checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` proved actual MT5/broker transport:

- one DEMO BUY `XAUUSDm 0.01` opened successfully;
- open retcode `10009`, comment `done`;
- probe-owned close retcode `10009`, comment `done`;
- probe terminal exited gracefully;
- frozen V69 automatically returned to normal DEMO runtime.

Therefore generic real-time deployment, lot size and broker transport are not the primary explanation for the observed no-trade window. Do not rerun the forced transport probe unless new evidence contradicts this PASS.

### KD-2026-09-03-03 — frozen dashboard still displays obsolete `2 trades / 48h` wait gate

The smoke dashboard can still show `Closed 0/2`, `2 more closed trades`, and `wait until 48h cap`. Those lines are obsolete as project gates. Current gate is diagnostic localization, not passive waiting.

Do not restart a healthy runtime solely to fix this cosmetic text.

### KD-2026-09-03-02 — a forced DEMO fill proves transport, not strategy edge

The isolated probe proves account/symbol/lot/filling/market-order transport can open and close. It does not prove V69 edge, live expectancy, acceptable slippage across regimes, or REAL safety/profitability.

Never convert probe PASS directly into automatic REAL authorization.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades does not locate the fault

Dry-run readiness plus zero trades is ambiguous. Resolve it with signal-stage telemetry plus isolated execution evidence, not visual chart interpretation or longer waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-03 — diagnostic v4 CI failed on a stale source-string assertion — RESOLVED

At code checkpoint `85572066021b0f90f30e242d20f5e21c0d239116`, all substantive dedup/regime aggregation tests passed, but `v69-upstream-diag-quality` failed because a static test expected the literal source text `V69_PRE_PENDING_REJECT_REASONS=` while the runner emits that runtime marker through `print_json_marker(...)`.

Fix: test the structured marker name rather than the implementation-specific source literal. Corrected checkpoint `56787feaf6370da4cd766d917ad602bdb40f01fa` passed all five workflows.

Do not mutate runtime semantics merely to satisfy a stale textual assertion.

### KH-2026-09-03-02 — upstream diagnostic treated zero event rows as fatal — RESOLVED

The first upstream runner raised a fatal error even though the analyzer intentionally classified zero events as `INITIAL_SETUP_OR_PENDING_ARM_BLOCK`.

Fix:

- zero event rows are valid diagnostic evidence;
- pre-probe JSON snapshot is also considered after FILE_COMMON rotation;
- regression tests cover header-only/zero-event telemetry.

The corrected operator run subsequently completed with diagnostic PASS across 8 sources.

### KH-2026-09-03-01 — expected-HEAD variable mismatch in nested real-readiness runtime — RESOLVED

First Windows attempt at checkpoint `40115f1aa741720afa360b4cad4216dd0e2ab27e` failed before MT5 with `V69_ONE_SHOT_EXPECTED_HEAD is required` because the new launcher used `V69_REAL_READINESS_EXPECTED_HEAD` while inherited code required the old name.

Fix bridged the inherited variable end-to-end and added regression coverage. Corrected checkpoint `614d68e...` completed the real-readiness probe successfully.

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
- Empty pending-event telemetry must be followed by pre-pending ENTRY_EVAL analysis before claiming there were no signals.
- Deduplicate copied telemetry rows across rotated FILE_COMMON roots before treating row totals as market-sample counts.
- `short_edge` in a LONG-only runtime is abstention evidence, not authorization to activate SHORT.
- Once actual execution transport is proven, do not rerun forced probes unless transport evidence changes.
- Ignore legacy dashboard `2 trades / 48h` as a current project gate.
- Keep strategy, broker transport and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects or observability gaps.
- Exact-HEAD contracts reused across nested runtimes must be bridged and regression-tested end-to-end.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
