# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 07:20 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-17 — do not explain a baseline mismatch by accounting without checking the frozen accepted analyzer

The corrected V70 fast reanalysis returned 24/10/14 but `+$6.44`, while accepted frozen V69 is `+$7.14`. The earlier explanation that 6.44 was full round-trip accounting and 7.14 was exit-row accounting was incorrect.

Exact frozen V69 code at HEAD `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1` proves the accepted analyzer itself uses exit deals and computes `profit + commission + swap + fee`. Current V70 `legacy_accepted_summary()` uses the same formula and still returns 6.44.

Therefore the remaining -$0.70 is genuine replay/deal-value drift until localized. Do not change the expected 7.14 guard, widen tolerance, or promote V70 policies to hide the mismatch.

Correct next method is a hash-pinned raw-deal comparison against accepted V69 ZIP SHA256 `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`, comparing exit timestamp, price, profit, costs and reason trade-by-trade.

### KD-2026-09-03-16 — zero-trade months must not be forced to contain position-lifetime lifecycle markers

Feb-May 2026 contain zero V69/V70 trades. A zero-trade month correctly has zero position-lifetime START/END blocks. Integrity is per-month trade/shadow parity: 0/0 is valid; trades require exactly matching completed shadows; stray/missing/overlapping/unterminated shadows fail closed.

### KD-2026-09-03-15 — do not rerun an expensive tester campaign when raw evidence is valid and only post-processing was wrong

The V70 campaign already produced all nine raw evidence directories. Post-processing-only defects should be fixed and reanalyzed from existing evidence. A full tester replay is fallback only when source/semantic integrity genuinely requires new evidence.

### KD-2026-09-03-14 — accounting conventions must be explicit, but they do not explain the current V70 -$0.70 drift

Exit-row headline accounting and full round-trip accounting can differ in general. For this V70 evidence, current entry explicit costs are effectively zero, so both current calculations are 6.44. The accepted frozen V69 headline remains 7.14 under the same exit-row formula. The current mismatch is not an accounting-definition mismatch.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` MFE/MAE is NOT actual trade-lifetime excursion

The old noise shadow can continue after the real position closes. Do not reuse it as actual-trade MFE/MAE. V70 position-lifetime telemetry is the replacement.

### KD-2026-09-03-12 — MFE peak alone cannot simulate an honest trailing-stop counterfactual

Require ordered intra-trade path/ticks or an every-tick shadow policy.

### KD-2026-09-03-11 — next-cycle rearm PnL is not same-setup counterfactual edge

Chronological next-cycle association does not prove rejected same-setup edge.

### KD-2026-09-03-10 — high PF from two trades is not an archetype promotion signal

PULLBACK_SWEEP_BOS has only 2 sent trades. BREAKOUT_RETEST_BOS produced 22/24 and is the current engine.

### KD-2026-09-03-09 — selector bars are not independent setups

3,576 LONG-selected M15 bars cannot be divided directly into 24 trades. Use the staged setup/cycle funnel.

### KD-2026-09-03-08 — historical diagnostics must fail closed on evidence identity

Accepted V69 identity is `24 trades / 10W / 14L / +$7.14`. Accepted ZIP SHA256 is `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

### KD-2026-09-03-07 — candidate ENTRY_EVAL rows cannot measure all-bar opportunity coverage

All-bar coverage: 23,526 M15 rows; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not permission to enable SHORT

Do not enable SHORT or loosen LONG to manufacture turnover.

### KD-2026-09-03-05 — `V64_EVENTS=0` does NOT mean `no market signal`

Zero pending rows only prove no instrumented pending state.

### KD-2026-09-03-04 — actual DEMO execution PASS localizes no-trade diagnosis upstream

Actual 0.01 XAUUSDm BUY+close both returned server `10009 / done`. Do not rerun forced transport without contradictory evidence.

### KD-2026-09-03-03 — frozen dashboard `2 trades / 48h` is obsolete

Not a current gate.

### KD-2026-09-03-02 — forced DEMO fill proves transport, not edge

Transport PASS does not prove expectancy or REAL safety.

### KD-2026-09-03-01 — broker READY + live ticks + zero trades is ambiguous

Use deterministic telemetry rather than passive waiting.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-07 — V70 policy parser/lifecycle are now valid, but baseline identity still fails — OPEN ECONOMIC/REPLAY CLASSIFICATION

At `f984f259f122f691b31e8aee3ed5bf639b516dfe`, source identity, all nine months, trade/shadow lifecycle parity and nonzero true position-lifetime telemetry passed. The run still stopped because baseline net was 6.44 vs accepted 7.14.

This is no longer a parser or zero-trade-month harness bug. Policy values from that V70 cohort are provisional only until the -$0.70 baseline drift is classified against accepted raw V69 deals.

### KH-2026-09-03-06 — existing-evidence fast path required lifecycle in a zero-trade month — RESOLVED

Fixed by per-month trade/shadow parity and regression coverage.

### KH-2026-09-03-05 — first full V70 replay parsed wrong event numeric columns — RESOLVED

Real fields are `value1/value2/value3`; tests now use the real schema. The previous accounting explanation attached to this incident is superseded by KD-17.

### KH-2026-09-03-04 — V69 MFE/giveback attribution used a post-exit shadow — RESOLVED BY V70 DESIGN

V70 measures excursion only while the owned actual position exists.

### KH-2026-09-03-03 — diagnostic CI failed on stale source-string assertion — RESOLVED

Fix stale wording contracts, not strategy semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero rows can be valid evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Bridge and regression-test nested exact-head contracts.

### KF-2026-09-01-01 — generic 4756 hid server `10019 No money` — RESOLVED

Interpret `_LastError` with server retcode/comment.

## Trading-system lessons that must not be lost

### KL-01 — surviving V69 historical losers are fast-loss dominated

24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34; 10/14 losers closed within 60 seconds.

### KL-02 — October concentration indicates regime sensitivity

Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat; ex-Oct -$2.01.

### KL-03 — V69/V70 reused historical replay is development-only

Sep 2025-May 2026 is not an untouched holdout.

### KL-04 — inherited profit ratchet is +$2 -> about +$1, but opportunity cost is not yet proven

Old evidence has 9 successful PROFIT_LOCK modifies. V70 policy promotion remains blocked until baseline drift is classified.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware past-only statistics and expectancy by session.

### KL-06 — downstream attrition is mostly structural, not V69 separation

Accepted funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`; hard-structural terminals 235/460.

### KL-07 — breakout-retest is the current economic engine

BREAKOUT_RETEST_BOS: 22/24 sent trades. Pullback-sweep has only 2.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- Require exact source/evidence identity for historical claims.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Do not tune thresholds to mask tooling defects.
- Do not change an accepted baseline guard merely because a newer replay misses it.
- Before explaining a numerical mismatch by accounting, inspect the exact accepted analyzer implementation.
- Compare raw deals trade-by-trade when counts match but net does not.
- Do not wait on natural trades when deterministic evidence can answer the question.
- Deduplicate rotated telemetry.
- Candidate ENTRY_EVAL rows are not all-bar coverage.
- All-bar selector rows are context, not setups.
- `short_edge` in LONG-only runtime is abstention, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes without contradictory evidence.
- Ignore legacy `2 trades / 48h` dashboard gate.
- Do not loosen a gate from funnel volume alone.
- Next-cycle association is not same-setup counterfactual proof.
- Do not promote an archetype from two trades.
- Never use a shadow's excursion as actual-trade excursion unless lifetime is explicitly bounded.
- Do not simulate trailing exit from peak MFE alone; require ordered path.
- Synthetic telemetry tests must use the real CSV schema.
- Prefer source-pinned reanalysis over unnecessary tester reruns after post-processing-only fixes.
- Validate zero-trade months as 0 trades / 0 shadows.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
