# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 06:45 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-14 — accepted headline accounting and economic round-trip accounting are different contracts

The first full V70 Windows replay reproduced the same 24-trade cohort but reported `+$6.44` from `analyze_v69_forward_trade_quality.parse_deals()` while the accepted V69 headline is `+$7.14`.

Source audit found different accounting conventions, not immediate strategy drift:

- legacy V68/V69 accepted headline: exit profit + exit-row commission/swap/fee;
- economic round-trip: exit profit + entry explicit costs + exit explicit costs.

Do not silently replace the accepted V69 `+$7.14` with `+$6.44`, and do not compare a counterfactual policy against one convention while gating identity with the other. V70 must report both. Use legacy accounting only to prove the accepted cohort identity; use full round-trip accounting consistently for policy economics.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` MFE/MAE is NOT actual trade-lifetime excursion

`V64NoiseStart()` begins at actual fill, but `V64UpdateNoiseShadows()` continues independently after the real position closes. The noise shadow resolves only after its synthetic stop/target matrix completes or after `InpV64NoiseShadowMaxMinutes=480`.

Therefore `V64_NOISE_SHADOW.max_pnl/min_pnl` can contain excursion after the actual trade exit. Do not reuse its median MFE, giveback, capture ratio, `MFE >= $2` counts, or extreme values as actual-trade evidence.

Valid old evidence is limited to actual deal economics and events explicitly filtered inside entry->exit windows. In particular, 9 trades logged PROFIT_LOCK modify attempts; all 9 were modified and 0 logged modify failures.

### KD-2026-09-03-12 — MFE peak alone cannot simulate an honest trailing-stop counterfactual

A peak has no path ordering. Genuine trailing/cash-floor counterfactuals require ordered intra-trade ticks or an in-replay shadow evaluated every tick.

### KD-2026-09-03-11 — next-cycle rearm PnL is not same-setup counterfactual edge

Positive next-cycle net after context-quality or TTL rejects proves chronological association only. `same archetype != same setup identity`. Do not relax a gate from next-cycle association.

### KD-2026-09-03-10 — high PF from two trades is not an archetype promotion signal

`PULLBACK_SWEEP_BOS` had only 2 sent trades. `BREAKOUT_RETEST_BOS` produced 22/24 V69 trades and is the economically relevant engine.

### KD-2026-09-03-09 — selector bars are not independent setups

All-bar coverage found 3,576 LONG-selected M15 bars while V69 has 24 trades. Do not use `24/3576` as setup conversion. Correct hierarchy is selector context -> initial eval -> pending cycle -> downstream stages -> actual trade.

### KD-2026-09-03-08 — historical diagnostics must fail closed on evidence identity

Accepted V69 identity is `24 trades / 10W / 14L / about +$7.14` under the legacy accepted accounting convention. Accepted ZIP SHA256 is `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Do not override identity failure and do not regenerate evidence merely to make a diagnostic pass.

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

All-bar recovery proved 23,526 M15 rows: LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG-selector starvation is rejected.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not permission to enable SHORT

Observed live 83/83 short-edge evaluations were consistent LONG-only abstention in a bearish window. Do not enable SHORT or loosen LONG to manufacture turnover.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending-event rows only prove no instrumented pending state. Inspect pre-pending ENTRY_EVAL/selector paths first.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` opened and closed one DEMO XAUUSDm 0.01 BUY with server `10009 / done` both times. Do not rerun forced transport without contradictory evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

It is not a current gate.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

Transport PASS does not prove expectancy, REAL safety or profitability.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use staged telemetry and isolated transport evidence instead of passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-05 — first full V70 replay parsed the wrong event numeric columns and mixed accounting — RESOLVED IN PATCH

At checkpoint `6d4095f1903f15077fdf805fda1f4485f4ffd314`, all nine tester months completed, but analyzer output showed all-zero true excursion and then failed baseline identity with `6.44` versus accepted `7.14`.

Two independent analyzer issues were found:

1. actual V64 event telemetry columns are `value1/value2/value3`, while V70 read `v1/v2/v3`; the synthetic regression test used the same wrong fake keys and therefore masked the defect;
2. runtime identity compared full round-trip economic PnL against the legacy V69 headline accounting.

Consequences: every `POLICY_*` number from that first complete V70 replay is INVALID and must not be used, including the apparent small EARLY policy improvement.

Resolution at code checkpoint `6d8138490b7413aed5b38e273275bd60380460d4`:

- parse canonical `value1/value2/value3` fields;
- tests use the real event schema;
- separate `legacy_accepted_identity` from `economic_roundtrip_actual`;
- gate 24/10/14/~+7.14 on legacy accounting only;
- compare policy economics to the full round-trip baseline;
- fail closed if true excursion/policy telemetry remains all zero.

### KH-2026-09-03-04 — V69 MFE/giveback attribution used a post-exit shadow — RESOLVED BY V70 DESIGN

Do not patch the old V64 noise-shadow numbers. V70 measures high-water/low-water only while the actual owned position exists and evaluates cash-floor policies in ordered tick replay.

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Fix stale CI wording rather than runtime semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero event rows are valid upstream evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Exact-HEAD environment variables reused by nested runtimes must be bridged and regression-tested.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Interpret `_LastError` together with server retcode/comment.

### KF-02 — broken Python launcher candidate

Probe executable candidates and require Python 3.10+.

### KF-03 — unsupported MQL helper `LongToString`

Use supported MQL5 APIs and generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

Freeze the true parent strategy identity rather than ephemeral generated pins.

### KF-05 — background helpers flashed console windows

Use no-window background execution.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful OnInit creates telemetry; zero telemetry after startup means initialization/attachment failure.

### KF-07 — manual EA attachment is avoidable operator risk

Prefer deterministic compile/install/startup/heartbeat automation.

### KF-08 — CI semantic contract drifted behind runtime wording

Fix stale CI wording rather than strategy semantics.

### KF-09 — broker health runner concluded before a second refresh

Require independent stable broker-ready observations.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

V69: 24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34; 10/14 losers closed within 60 seconds.

### KL-02 — October concentration indicates regime sensitivity

Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat. Ex-Oct total -$2.01.

### KL-03 — V69/V70 reused historical replay is development-only

Sep 2025-May 2026 is not an untouched holdout. V70 policy comparison on it is also development-only.

### KL-04 — inherited profit ratchet is +$2 -> about +$1, but opportunity cost is not yet proven

Valid old evidence shows 9 successful in-trade PROFIT_LOCK modifies and 0 logged failures. Use corrected V70 true-lifetime replay before lowering thresholds.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware past-only statistics and expectancy by session.

### KL-06 — downstream attrition is mostly structural, not V69 separation

Accepted funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`. Hard structural terminals were 235/460.

### KL-07 — breakout-retest is the current economic engine

BREAKOUT_RETEST_BOS: 241 cycles, 22 trades, 9W/13L, +$4.76, PF 1.332402. Pullback-sweep has only 2 trades.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- MetaEditor rc alone is not compile acceptance; require source identity + `0 errors, 0 warnings` + current non-empty EX5.
- Terminal process state alone is not runtime health; require telemetry/heartbeat.
- Interpret `_LastError` with server retcode/comment.
- Dry-run READY proves request readiness; execution probe PASS proves transport; neither proves strategy edge.
- Do not wait on natural trades when deterministic evidence can answer the question.
- Deduplicate rotated FILE_COMMON telemetry before treating row totals as market-sample counts.
- Candidate ENTRY_EVAL rows are not all-bar coverage.
- All-bar selector rows are context, not one-to-one setups.
- Reuse historical evidence only after exact code/evidence identity checks.
- `short_edge` in LONG-only runtime is abstention evidence, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes without new contradictory transport evidence.
- Ignore the legacy `2 trades / 48h` dashboard gate.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not change strategy thresholds to mask tooling defects.
- Do not loosen a gate from funnel volume alone.
- Next-cycle association is not same-setup counterfactual proof.
- Do not promote an archetype from a two-trade PF.
- Never interpret a shadow MFE/MAE as actual-trade excursion unless its lifetime is explicitly bounded to the actual position.
- Do not simulate trailing exits from peak MFE alone; require ordered path/tick replay.
- Do not mix accounting conventions when asserting baseline identity or policy deltas.
- A synthetic telemetry test must use the real CSV field schema, not an invented alias-only fixture.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
