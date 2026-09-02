# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 02:55 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

The aggregate V69 diagnostic found `83/83` unique preserved directional evaluations were `short_edge`, selected `-1`, rejected as `direction_isolated_out`, and occurred in selector-defined `SHORT_HTF_REGIME` with H1/H4 both `-1`.

That settles the blocker for those recorded evaluations, but it does **not** mean 100% of all closed M15 bars in the calendar window were SHORT-eligible.

Inherited V62/V69 `EvaluateBar` returns before writing `V64_ENTRY_EVAL.csv` when:

- `V64BuildFeatures()` fails; or
- `V64SelectDirection()` returns `d==0`.

Therefore candidate/evaluation telemetry is selection-biased for opportunity-coverage measurement.

Do not estimate LONG scarcity from `83/83 SHORT` alone. Measure coverage with an all-bar screen that logs feature-not-ready, neutral and directional outcomes.

Historical screen reuse is allowed only after exact identity validation of the feature builder, score function, selector and score thresholds against frozen V69. The selector-coverage recovery tool and CI now fail closed on any mismatch.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is regime abstention, not permission to enable SHORT

Final aggregate read-only operator evidence at checkpoint `9ca2ac66b4c82f5b2f5c51184259d7147486c5a9` found:

- raw ENTRY_EVAL rows `83`;
- unique rows `83`;
- duplicate rows removed `0`;
- `short_edge` `83/83`;
- `selected_direction=-1` `83/83`;
- `direction_isolated_out` `83/83`;
- `SHORT_HTF_REGIME` `83/83`;
- H1 trend `-1` `83/83`;
- H4 trend `-1` `83/83`;
- short score higher `83/83`;
- long-minus-short score margin was never better than `-9`.

This is internally consistent LONG-only abstention. Broker transport, reclaim, separation and retest were not the blockers for these rows.

Do not react by:

- enabling the historically rejected SHORT path;
- loosening LONG direction/regime gates merely to force turnover;
- resuming repeated upstream diagnostics after this observed-window blocker is settled.

The next question is all-bar regime/opportunity coverage, followed by separate economic research if bearish-regime opportunity is material.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending-event rows prove no instrumented pending-state event occurred. They do not prove `BuildFeatures`/`SelectDirection` found no candidate.

Pre-pending paths can return without `V64_EVENTS.csv`:

- `SelectDirection` returns `d==0`;
- opposite direction logs only `direction_isolated_out` to `V64_ENTRY_EVAL.csv`;
- archetype rejection logs only `no_complete_archetype`;
- raw structural-stop rejection logs only `invalid_arm_structural_stop`;
- only a successful arm emits `PENDING_ARM`.

Inspect pre-pending telemetry before changing strategy thresholds.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Execution probe checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` successfully opened and closed one DEMO `XAUUSDm 0.01` BUY with server retcode `10009 / done` on both actions.

Generic MT5/broker transport is settled PASS. Do not rerun the forced probe without contradictory transport evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

The dashboard can still show `Closed 0/2` and `wait until 48h cap`. Those lines are not current project gates. Do not restart a healthy runtime solely for cosmetic text.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

A transport probe does not prove V69 expectancy, slippage robustness, REAL safety or profitability. Never convert probe PASS directly into REAL authorization.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use staged telemetry and isolated transport evidence, not visual-chart guessing or longer passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Substantive tests passed but a static test expected a superseded literal marker implementation. The assertion was corrected to test the structured marker contract rather than mutating runtime semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero event rows are valid upstream evidence. The runner now accepts header-only/zero-event sources and can use the pre-probe snapshot after FILE_COMMON rotation.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Inherited runtime expected a different exact-HEAD variable. The bridge was fixed and regression-tested before the successful execution probe.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Local lot validation was not the issue. Server retcode/comment exposed insufficient funds. Always interpret `_LastError` with broker retcode/comment.

### KF-02 — broken Python launcher candidate

Probe executable candidates by actually running Python and require 3.10+.

### KF-03 — unsupported MQL helper `LongToString`

Use supported MQL5 conversion APIs and generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

Freeze true parent strategy identity; do not duplicate ephemeral generated-source pins in multiple places.

### KF-05 — background helpers flashed console windows

Background Windows helpers must use no-window execution and redirected handles.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful `OnInit()` creates telemetry. Zero telemetry after attempted startup means attachment/initialization failed; do not wait for a trade.

### KF-07 — manual EA attachment is avoidable operator risk

Prefer deterministic compile/install/startup/heartbeat automation.

### KF-08 — CI semantic contract drifted behind runtime wording

Fix stale CI wording rather than changing runtime semantics to satisfy literal greps.

### KF-09 — broker health runner concluded before a second refresh

Broker readiness requires independent stable observations; do not conclude before the configured refresh can occur.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all ten V68 winners while removing four losers, but `10/14` surviving V69 losers closed within 60 seconds. Entry/regime quality remains a verified economic research priority.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly replay: Sep `-$1.84`; Oct `+$9.15`; Nov `+$1.24`; Dec `-$2.28`; Jan `+$0.87`; Feb-May flat. Excluding October: `-$2.01`.

### KL-03 — V69 historical replay is development-only

V69 was designed after V68 was inspected. Sep 2025-May 2026 is not an untouched holdout. Do not tune on it again and call the result independent.

### KL-04 — profit ratchet has a theoretical sub-$2 harvest gap

Current lineage arms around +$2 and attempts to lock about +$1. Do not lower it blindly. Inspect MFE/capture/giveback first; near-zero-MFE fast losers cannot be rescued by earlier profit protection.

### KL-05 — session volatility is conditioning, not a trading rule

Session labels may explain volatility/efficiency, but `NEW_YORK = TRADE` is not an edge. Use DST-aware past-only statistics and expectancy/MFE/MAE by session.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` with broker server retcode/comment.
- Dry-run READY proves request readiness; execution probe PASS proves transport; neither proves strategy edge.
- After prolonged no-trade runtime, inspect stage telemetry instead of waiting blindly.
- Empty pending-event telemetry must be followed by pre-pending analysis before claiming no signals.
- Deduplicate rotated FILE_COMMON telemetry before treating row totals as market-sample counts.
- Candidate ENTRY_EVAL rows are not all-bar coverage when neutral/feature-fail paths return before logging.
- Reuse historical screen coverage only after exact directional-core and threshold identity validation.
- `short_edge` in a LONG-only runtime is abstention evidence, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes unless transport evidence changes.
- Ignore legacy dashboard `2 trades / 48h` as a project gate.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects or observability gaps.
- Exact-HEAD contracts reused across nested runtimes must be bridged and regression-tested end-to-end.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
