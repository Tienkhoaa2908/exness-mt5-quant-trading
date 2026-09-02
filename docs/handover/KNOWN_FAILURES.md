# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 05:10 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` MFE/MAE is NOT actual trade-lifetime excursion

This supersedes the MFE interpretation in KD-12.

`V64NoiseStart()` begins at actual fill, but `V64UpdateNoiseShadows()` continues independently after the real position closes. The noise shadow resolves only after its synthetic stop/target matrix completes or after `InpV64NoiseShadowMaxMinutes=480`.

Therefore `V64_NOISE_SHADOW.max_pnl/min_pnl` can contain price excursion many minutes or hours after the actual trade exit. Matching a shadow to an entry timestamp does not clip it to the deal's lifetime.

The V69 MFE/giveback recovery at checkpoint `12c97d81d6846b2b0c81cad234d698c25c9a3341` was operationally correct but its MFE attribution was scientifically wrong. Do not reuse its median MFE, median giveback, capture ratio, `MFE >= $2` counts, or large per-trade MFE values as evidence for exit tuning.

Valid parts of that run are the accepted deal economics and events explicitly filtered inside actual entry->exit windows. In particular, `9` trades logged `PROFIT_LOCK` modify attempts, all `9` were modified, and `0` logged modify failures.

Correct method: instrument or replay excursion only while the actual owned position exists. V70 exit-harvest research does exactly this and explicitly does not read `V64_NOISE_SHADOW`.

### KD-2026-09-03-12 — MFE peak alone cannot simulate an honest trailing-stop counterfactual

Even a correctly bounded actual-trade MFE/MAE peak is not enough to reconstruct chronological path ordering after the peak.

Do not infer a trailing-stop exit from MFE peak alone. A genuine trailing/cash-floor counterfactual requires ordered intra-trade ticks or an in-replay shadow policy that evaluates every tick. V70 uses the latter.

### KD-2026-09-03-11 — next-cycle rearm PnL is not same-setup counterfactual edge

Cycle-economics recovery found positive next-cycle net after context-quality (`+$6.90`) and TTL (`+$2.46`) rejections, while hard-structural next cycles were `-$2.22`.

Do not conclude that relaxing the rejected gate would have captured those profits. The recovery proves only chronological next-cycle association. `same archetype != same setup identity`, and cross-month rearms were not linked.

To change a gate, measure the rejected cycle's own subsequent path or run a correctly paired shadow/replay.

### KD-2026-09-03-10 — high PF from two trades is not an archetype promotion signal

`PULLBACK_SWEEP_BOS` produced `1W / 1L`, net `+$2.38`, PF `3.125`, but only `2` sent trades out of `219` cycles. Do not promote it from the headline PF.

`BREAKOUT_RETEST_BOS` produced `22/24` V69 trades and is the economically relevant engine for current work.

### KD-2026-09-03-09 — selector bars are not independent setups and must not be divided directly by trade count

All-bar coverage proved `3,576` LONG-selected M15 bars while accepted V69 development evidence contains `24` LONG trades.

Do not interpret `24 / 3,576` as a setup-conversion rate. Adjacent M15 bars can remain LONG-selected while one pending setup is active and selector context precedes archetype, stop geometry and pending-state construction.

Correct hierarchy:

`all-bar selector context -> initial LONG eval -> PENDING_ARM cycle -> downstream cycle stages -> actual entry/trade`.

### KD-2026-09-03-08 — historical diagnostics must fail closed on evidence identity

Accepted V69 development identity is:

- `24 trades`;
- `10 wins`;
- `14 losses`;
- about `+$7.14` net.

If accepted ZIP recovery is used, required SHA256 is:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Do not override identity failure and do not regenerate strategy evidence merely to make a diagnostic pass.

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

The live sample had `83/83` directional evaluations selected SHORT and rejected by LONG-only isolation. That does not mean all closed M15 bars were SHORT-eligible.

All-bar recovery proved:

- `23,526` M15 rows;
- `3,576` LONG selected;
- `1,744` SHORT selected;
- `18,206` neutral;
- LONG share of directional selections `67.218%`.

Global LONG-selector starvation is rejected.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not permission to enable SHORT

The observed `83/83 short_edge` live evaluations were internally consistent LONG-only abstention in a bearish window. Do not enable rejected historical SHORT or loosen LONG to manufacture turnover.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending-event rows prove only that no instrumented pending state was created. Inspect pre-pending ENTRY_EVAL/selector paths before threshold changes.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` opened and closed one DEMO `XAUUSDm 0.01` BUY with server retcode `10009 / done` on both actions.

Do not rerun the forced probe without contradictory transport evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

The dashboard may still display the old gate. It is not a current project gate.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

A transport probe does not prove expectancy, REAL safety or profitability.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use staged telemetry and isolated transport evidence instead of visual-chart guessing or passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-04 — V69 MFE/giveback attribution used a post-exit shadow — RESOLVED BY V70 DESIGN

The V69 MFE recovery correctly matched noise shadows to actual entry timestamps but assumed the shadow ended with the actual deal. Source audit showed the shadow can continue for up to `480` minutes post-exit.

Resolution: do not patch the old numbers. V70 measures high-water/low-water only while the actual owned position exists and evaluates cash-floor policies in ordered tick replay.

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Substantive tests passed but a static test expected superseded literal wording. Fix the CI contract rather than runtime semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero event rows are valid upstream evidence. Header-only/zero-event telemetry is handled as evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Inherited runtime expected a different exact-HEAD variable. The bridge was fixed and regression-tested.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Interpret `_LastError` together with server retcode/comment.

### KF-02 — broken Python launcher candidate

Probe executable candidates by running Python and require 3.10+.

### KF-03 — unsupported MQL helper `LongToString`

Use supported MQL5 APIs and generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

Freeze the true parent strategy identity and avoid duplicated ephemeral generated-source pins.

### KF-05 — background helpers flashed console windows

Background Windows helpers must use no-window execution and redirected handles.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful `OnInit()` creates telemetry. Zero telemetry after startup means initialization/attachment failed; do not wait blindly.

### KF-07 — manual EA attachment is avoidable operator risk

Prefer deterministic compile/install/startup/heartbeat automation.

### KF-08 — CI semantic contract drifted behind runtime wording

Fix stale CI wording rather than strategy/runtime semantics.

### KF-09 — broker health runner concluded before a second refresh

Broker readiness requires independent stable observations before conclusion.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`; `10/14` surviving V69 losers closed within 60 seconds.

### KL-02 — October concentration indicates regime sensitivity

V69 monthly replay: Sep `-$1.84`; Oct `+$9.15`; Nov `+$1.24`; Dec `-$2.28`; Jan `+$0.87`; Feb-May flat. Excluding October: `-$2.01`.

### KL-03 — V69/V70 reused historical replay is development-only

V69 was designed after V68 inspection. Sep 2025-May 2026 is not an untouched holdout. V70 exit-harvest policy comparison on the same period is also development-only.

### KL-04 — inherited profit ratchet is `+$2 -> about +$1`, but its opportunity cost is not yet proven

The valid in-trade V69 event evidence shows `9` successful `PROFIT_LOCK` modify-event trades and no logged modify failures. The old noise-shadow MFE cannot establish how many other trades actually reached `+$2` before exit.

Use the V70 true-lifetime replay before lowering the arm threshold.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware past-only statistics and expectancy by session. Session labels alone are not edge.

### KL-06 — downstream attrition is mostly structural, not V69 separation

Accepted funnel: `460 PENDING_ARM -> 404 micro-arm -> 167 touch -> 95 penetration -> 51 reversal confirm -> 49 separation -> 24 retest/entry -> 24 deals`.

`235/460` terminal cycles were hard structural. Do not remove separation to manufacture turnover.

### KL-07 — breakout-retest is the current economic engine

`BREAKOUT_RETEST_BOS`: `241` cycles, `22` trades, `9W/13L`, `+$4.76`, PF `1.332402`.

`PULLBACK_SWEEP_BOS`: `219` cycles, only `2` trades. Do not promote its PF from that sample.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor rc alone is not compile acceptance; require exact source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` with server retcode/comment.
- Dry-run READY proves request readiness; execution probe PASS proves transport; neither proves strategy edge.
- Do not wait on natural trades after a diagnostic question can be settled by deterministic evidence.
- Deduplicate rotated FILE_COMMON telemetry before treating row totals as market-sample counts.
- Candidate ENTRY_EVAL rows are not all-bar coverage when neutral/feature-fail paths return before logging.
- All-bar selector rows are context, not one-to-one setups.
- Reuse historical evidence only after exact code/evidence identity checks.
- `short_edge` in a LONG-only runtime is abstention evidence, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes unless transport evidence changes.
- Ignore legacy dashboard `2 trades / 48h` as a project gate.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not change strategy thresholds to mask tooling defects or observability gaps.
- Do not loosen a gate from funnel volume alone.
- Next-cycle association is not same-setup counterfactual proof.
- Do not promote an archetype from a two-trade PF.
- Never interpret a shadow's MFE/MAE as actual-trade excursion unless the shadow lifetime is explicitly bounded to the actual position.
- Do not simulate a trailing exit from peak MFE alone; require path ordering or tick-replay shadowing.
- Exact-HEAD contracts reused across nested runtimes must be bridged and regression-tested end-to-end.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
