# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 03:21 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-09 — selector bars are not independent setups and must not be divided directly by trade count

All-bar coverage proved `3,576` LONG-selected M15 bars over the Sep 2025-Aug 2026 screen, while accepted V69 Sep-May development evidence contains only `24` LONG trades.

Do **not** interpret `24 / 3,576` as a strategy setup-conversion rate. Adjacent M15 bars can remain LONG-selected while one pending setup is already active, and selector context precedes archetype, stop-geometry and pending-state construction.

Correct denominator hierarchy:

`all-bar selector context -> initial LONG eval -> successful PENDING_ARM cycles -> downstream cycle stage reach -> actual entries/trades`.

Use cycle-based `PENDING_ARM` telemetry to localize contraction. Only after a gate is localized should rejected-cycle counterfactual outcomes be measured.

### KD-2026-09-03-08 — historical funnel diagnostics must fail closed on evidence identity

A downstream diagnostic that silently reads stale or different V69 run folders can produce a plausible but scientifically wrong funnel.

The V69 downstream funnel runner therefore requires accepted development economics to match:

- `24 trades`;
- `10 wins`;
- `14 losses`;
- about `+$7.14` net.

If it must recover from the V69 research ZIP, the ZIP SHA256 must be exactly:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Do not override identity failure and do not rerun MT5 tester merely to make the diagnostic pass.

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

The aggregate live diagnostic found `83/83` preserved directional evaluations were `short_edge`, selected `-1`, rejected as `direction_isolated_out`, and occurred in selector-defined `SHORT_HTF_REGIME`.

That does not mean every closed M15 bar was SHORT-eligible because inherited `EvaluateBar` returns before ENTRY_EVAL when feature building fails or selector direction is neutral.

The all-bar recovery subsequently proved:

- `23,526` M15 rows;
- `3,576` LONG selected (`15.2002%`);
- `1,744` SHORT selected (`7.4131%`);
- `18,206` neutral (`77.3867%`);
- LONG share of directional selections `67.218%`.

Thus the hypothesis that the V69 LONG selector is globally starved is rejected. Opportunity availability is regime-dependent, not uniformly absent.

Reuse historical all-bar screen evidence only after exact directional-core and score-threshold identity validation against frozen V69.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is regime abstention, not permission to enable SHORT

Final aggregate live evidence:

- unique rows `83`;
- `short_edge` `83/83`;
- `selected_direction=-1` `83/83`;
- `direction_isolated_out` `83/83`;
- `SHORT_HTF_REGIME` `83/83`;
- H1/H4 `-1` `83/83`;
- short score higher `83/83`.

This is internally consistent LONG-only abstention for those evaluations. Do not enable rejected historical SHORT, loosen LONG to force turnover, or blame broker/reclaim/separation/retest for these rows.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending-event rows only prove no instrumented pending state was created. Pre-pending paths can return through neutral direction, direction isolation, archetype rejection or structural-stop rejection without a `PENDING_ARM` event.

Inspect ENTRY_EVAL before threshold changes.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` opened and closed one DEMO `XAUUSDm 0.01` BUY with server retcode `10009 / done` on both actions.

Generic MT5/broker transport is settled PASS. Do not rerun the forced probe without contradictory transport evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

The dashboard can still show `Closed 0/2` and `wait until 48h cap`. Those lines are not current project gates. Do not restart healthy MT5 for cosmetic text.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

A transport probe does not prove expectancy, slippage robustness, REAL safety or profitability. Never convert transport PASS into REAL authorization.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use staged telemetry and isolated transport evidence, not visual-chart guessing or passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Substantive tests passed but a static test expected superseded literal wording. Fix the CI contract rather than mutating runtime semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero event rows are valid upstream evidence. Header-only/zero-event telemetry is now handled as diagnostic evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Inherited runtime expected a different exact-HEAD variable. The bridge was fixed and regression-tested before successful execution probing.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Interpret `_LastError` with broker server retcode/comment. Local request error alone was misleading.

### KF-02 — broken Python launcher candidate

Probe executable candidates by running Python and require 3.10+.

### KF-03 — unsupported MQL helper `LongToString`

Use supported MQL5 APIs and generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

Freeze the true parent strategy identity and avoid duplicated ephemeral generated-source pins.

### KF-05 — background helpers flashed console windows

Background Windows helpers must use no-window execution and redirected handles.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful `OnInit()` creates telemetry. Zero telemetry after startup means initialization/attachment failed; do not wait for a trade.

### KF-07 — manual EA attachment is avoidable operator risk

Prefer deterministic compile/install/startup/heartbeat automation.

### KF-08 — CI semantic contract drifted behind runtime wording

Fix stale CI wording rather than strategy/runtime semantics.

### KF-09 — broker health runner concluded before a second refresh

Broker readiness requires independent stable observations before conclusion.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 kept all ten V68 winners while removing four losers, but `10/14` surviving V69 losers closed within 60 seconds. Entry/regime quality remains a verified economic priority.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly replay: Sep `-$1.84`; Oct `+$9.15`; Nov `+$1.24`; Dec `-$2.28`; Jan `+$0.87`; Feb-May flat. Excluding October: `-$2.01`.

All-bar direction coverage independently reinforces regime variation: LONG selections were high in Sep-Feb, collapsed in Mar-Jun, then recovered sharply in Aug.

### KL-03 — V69 historical replay is development-only

V69 was designed after V68 inspection. Sep 2025-May 2026 is not an untouched holdout. Funnel analysis on these months can localize mechanics but cannot create independent edge evidence.

### KL-04 — profit ratchet has a theoretical sub-$2 harvest gap

Current lineage arms around +$2 and attempts to lock about +$1. Do not lower it blindly. Inspect MFE/capture/giveback first; near-zero-MFE fast losers cannot be rescued by earlier protection.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware past-only statistics and expectancy/MFE/MAE by session. Session labels alone are not an edge.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` with broker server retcode/comment.
- Dry-run READY proves request readiness; execution probe PASS proves transport; neither proves strategy edge.
- After prolonged no-trade runtime, inspect stage telemetry instead of waiting blindly.
- Empty pending-event telemetry requires pre-pending analysis before claiming no signals.
- Deduplicate rotated FILE_COMMON telemetry before treating row totals as market-sample counts.
- Candidate ENTRY_EVAL rows are not all-bar coverage when neutral/feature-fail paths return before logging.
- All-bar selector rows are context, not one-to-one setups or a trade denominator.
- Reuse historical evidence only after exact code/evidence identity checks appropriate to that analysis.
- `short_edge` in a LONG-only runtime is abstention evidence, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes unless transport evidence changes.
- Ignore legacy dashboard `2 trades / 48h` as a project gate.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not change strategy thresholds to mask tooling/broker defects or observability gaps.
- Do not loosen a gate from funnel volume alone; measure rejected-cycle counterfactual outcomes first.
- Exact-HEAD contracts reused across nested runtimes must be bridged and regression-tested end-to-end.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
