# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 07:02 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-16 — zero-trade months must not be forced to contain position-lifetime lifecycle markers

The first V70 existing-evidence reanalysis correctly source-pinned the previously generated V70 source, then incorrectly failed on `holdout_2026_02_long` because the fast-path harness required `V70_EXIT_SHADOW_START` and `V70_EXIT_SHADOW_END` in every monthly directory.

That requirement is invalid for a month with no actual positions. Accepted V69/V70 development evidence is flat from Feb-May 2026, so those months can legitimately contain zero completed trades and therefore zero position-lifetime shadow blocks.

Correct integrity rule is **trade/shadow parity per month**, not unconditional lifecycle presence:

- zero trades -> zero shadow blocks is valid;
- trades > 0 -> exactly matching completed shadow blocks are required;
- zero trades + stray shadow, trade without shadow, overlapping/unterminated shadow, or timestamp mismatch must fail closed;
- aggregate campaign still must contain matched trades and reproduce the accepted 24/10/14 identity.

Use the analyzer's actual `analyze_run()` trade/shadow matching contract instead of grep-style lifecycle presence checks.

### KD-2026-09-03-15 — do not rerun an expensive tester campaign when raw evidence is valid and only post-processing was wrong

The first full V70 campaign successfully compiled the exact source and produced all nine Sep 2025-May 2026 raw evidence directories. Its policy conclusions were invalid because the Python analyzer parsed the wrong CSV fields and mixed accounting conventions; the tester campaign itself did not need to be regenerated for those post-processing bugs.

Correct recovery is source-pinned reanalysis. Full tester replay is fallback only when source/evidence identity actually fails.

### KD-2026-09-03-14 — accepted headline accounting and economic round-trip accounting are different contracts

Legacy V68/V69 accepted headline = exit profit + exit-row commission/swap/fee. Full economic round-trip = exit profit + entry explicit costs + exit explicit costs.

The first V70 run produced `+$6.44` under round-trip accounting while the accepted V69 headline is `+$7.14`. Do not silently replace one with the other. Use legacy accounting only for accepted cohort identity and full round-trip accounting consistently for policy economics.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` MFE/MAE is NOT actual trade-lifetime excursion

The shadow can continue up to 480 minutes after the real position closes. Do not reuse its MFE, giveback, capture ratio or threshold counts as actual-trade evidence. Valid old in-trade evidence: 9 PROFIT_LOCK modify events, all 9 modified, 0 logged failures.

### KD-2026-09-03-12 — MFE peak alone cannot simulate an honest trailing-stop counterfactual

Require ordered intra-trade path/ticks or an every-tick shadow policy.

### KD-2026-09-03-11 — next-cycle rearm PnL is not same-setup counterfactual edge

Chronological next-cycle association does not prove a rejected setup itself contained missed edge.

### KD-2026-09-03-10 — high PF from two trades is not an archetype promotion signal

PULLBACK_SWEEP_BOS has only 2 sent trades. BREAKOUT_RETEST_BOS produced 22/24 V69 trades and is the relevant engine.

### KD-2026-09-03-09 — selector bars are not independent setups

3,576 LONG-selected M15 bars cannot be divided directly into 24 trades as setup conversion. Use selector context -> eval -> pending cycle -> downstream stages -> trade.

### KD-2026-09-03-08 — historical diagnostics must fail closed on evidence identity

Accepted V69 identity is `24 trades / 10W / 14L / about +$7.14` under legacy accepted accounting. Accepted ZIP SHA256 is `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

All-bar coverage: 23,526 M15 rows; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not permission to enable SHORT

Do not enable SHORT or loosen LONG to manufacture turnover.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending rows only prove no instrumented pending state.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca`: actual 0.01 XAUUSDm BUY and close both server `10009 / done`. Do not rerun forced transport without contradictory evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

Not a current gate.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

Transport PASS does not prove expectancy or REAL safety.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use deterministic telemetry rather than passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-06 — existing-evidence fast path required lifecycle in a zero-trade month — RESOLVED

At exact checkpoint `a74e48c0bbf4d24801d798f10acbb27671e72dd7`, the operator reran V70 in `V70_REANALYZE_EXISTING=1` mode. Source identity passed with SHA256 `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`, but the harness stopped at `holdout_2026_02_long` because no V70 START/END lifecycle marker existed.

Root cause: the fast-path integrity gate assumed every replay month must contain at least one real position. That contradicts the accepted sample, where Feb-May 2026 are flat/zero-trade months.

Resolution:

- remove unconditional lifecycle-string presence check;
- run each monthly directory through the corrected analyzer's `analyze_run()` function;
- accept 0 trades / 0 shadows;
- require exact trade/shadow parity and timestamp matching when trades exist;
- keep aggregate nonzero-trade guard;
- add regression with mixed zero-trade + traded months and a separate traded-month-without-shadow rejection.

No tester replay is required for this incident.

### KH-2026-09-03-05 — first full V70 replay parsed wrong event numeric columns and mixed accounting — RESOLVED

At checkpoint `6d4095f1903f15077fdf805fda1f4485f4ffd314`, all nine tester months completed, but analyzer output had all-zero true excursion and baseline `6.44` versus accepted `7.14`.

Root causes:

1. real `V64_EVENTS.csv` numeric fields are `value1/value2/value3`; V70 read `v1/v2/v3`, and the synthetic test repeated the same invented schema;
2. full round-trip economic PnL was compared against legacy accepted headline accounting.

Every first-run `POLICY_*` number is INVALID, including the apparent EARLY improvement.

Resolution:

- parse canonical `value1/value2/value3`;
- tests use real schema;
- separate `legacy_accepted_identity` and `economic_roundtrip_actual`;
- gate accepted 24/10/14/~+7.14 on legacy accounting;
- compare policies to full round-trip baseline;
- fail closed if excursion/policy telemetry is all zero;
- add source-pinned existing-evidence reanalysis.

### KH-2026-09-03-04 — V69 MFE/giveback attribution used a post-exit shadow — RESOLVED BY V70 DESIGN

V70 measures excursion only while the actual owned position exists.

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Fix stale wording contracts, not strategy semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero rows can be valid evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Bridge and regression-test nested exact-head contracts.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Interpret `_LastError` with server retcode/comment.

### KF-02 — broken Python launcher candidate

Probe candidates and require Python 3.10+.

### KF-03 — unsupported MQL helper `LongToString`

Use supported MQL5 APIs and generated-source compile regressions.

### KF-04 — generated dashboard hash-pin drift

Freeze true parent strategy identity rather than ephemeral generated pins.

### KF-05 — background helpers flashed console windows

Use no-window background execution.

### KF-06 — zero forward telemetry is stronger than zero trades

Successful OnInit creates telemetry; zero telemetry implies initialization/attachment failure.

### KF-07 — manual EA attachment is avoidable operator risk

Prefer deterministic startup automation.

### KF-08 — CI semantic contract drifted behind runtime wording

Fix stale CI wording rather than strategy semantics.

### KF-09 — broker health runner concluded before a second refresh

Require independent stable health observations.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34; 10/14 losers closed within 60 seconds.

### KL-02 — October concentration indicates regime sensitivity

Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat; ex-Oct -$2.01.

### KL-03 — V69/V70 reused historical replay is development-only

Sep 2025-May 2026 is not an untouched holdout.

### KL-04 — inherited profit ratchet is +$2 -> about +$1, but opportunity cost is not yet proven

Valid old evidence shows 9 successful in-trade PROFIT_LOCK modifies. Use corrected V70 true-lifetime analysis before changing thresholds.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware past-only statistics and expectancy by session.

### KL-06 — downstream attrition is mostly structural, not V69 separation

Accepted funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`; hard-structural terminals 235/460.

### KL-07 — breakout-retest is the current economic engine

BREAKOUT_RETEST_BOS: 241 cycles, 22 trades, 9W/13L, +$4.76, PF 1.332402. Pullback-sweep has only 2 trades.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- Require exact source identity + `0 errors, 0 warnings` + current non-empty EX5 for compile acceptance.
- Terminal process state alone is not runtime health; require telemetry.
- Interpret `_LastError` with server retcode/comment.
- Do not wait on natural trades when deterministic evidence can answer the question.
- Deduplicate rotated telemetry.
- Candidate ENTRY_EVAL rows are not all-bar coverage.
- All-bar selector rows are context, not setups.
- Reuse historical evidence only after exact code/evidence identity checks.
- `short_edge` in LONG-only runtime is abstention, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes without contradictory evidence.
- Ignore legacy `2 trades / 48h` dashboard gate.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not tune thresholds to mask tooling defects.
- Do not loosen a gate from funnel volume alone.
- Next-cycle association is not same-setup counterfactual proof.
- Do not promote an archetype from two trades.
- Never use a shadow's excursion as actual-trade excursion unless lifetime is explicitly bounded.
- Do not simulate trailing exit from peak MFE alone; require ordered path.
- Do not mix accounting conventions when asserting identity or policy deltas.
- Synthetic telemetry tests must use the real CSV field schema.
- Prefer source-pinned reanalysis of valid raw evidence over unnecessary full tester reruns after post-processing-only fixes.
- Validate existing V70 evidence by per-month trade/shadow parity; do not require lifecycle markers in a legitimate zero-trade month.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
