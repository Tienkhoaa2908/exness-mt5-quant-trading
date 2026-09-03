# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 07:45 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-18 — accepted historical PnL and contemporaneous replay PnL may differ because broker/tester cost tables drift

Hash-pinned raw comparison of accepted V69 against V70 localized the entire -$0.70 mismatch to one exit-row `swap` field. The affected Sep trade kept the same exit timestamp `2025.09.21 22:05:00`, price `3687.969`, gross profit `$3.64`, reason `5`, commission `0` and fee `0`; swap changed from `$0.00` to `-$0.70`.

Do not rewrite accepted V69 history. Accepted V69 remains +$7.14. Current V70 same-run economics are +$6.44.

A newer replay may use its contemporaneous cost baseline only when a hash-pinned raw audit proves execution identity is unchanged and the difference is cost-only. Do not generalize this into a wide PnL tolerance.

### KD-2026-09-03-17 — do not explain a baseline mismatch by accounting without checking the frozen accepted analyzer

Frozen V69 and V70 both use exit `profit + commission + swap + fee` for the legacy headline. The earlier accounting explanation for 7.14 versus 6.44 was wrong. Raw-deal comparison, not narrative inference, resolved the mismatch.

### KD-2026-09-03-16 — zero-trade months must not be forced to contain position-lifetime lifecycle markers

Feb-May 2026 have zero trades. Integrity is trade/shadow parity: 0/0 is valid; traded months require exact completed lifecycle parity.

### KD-2026-09-03-15 — do not rerun expensive tester evidence for post-processing-only defects

Reuse source-pinned raw evidence when parser/harness defects can be corrected offline. Full tester replay is fallback only when strategy/source/runtime evidence itself is invalid.

### KD-2026-09-03-14 — accounting conventions must remain explicit

Legacy accepted headline and full economic round-trip accounting can differ in general. Do not mix denominators when reporting policy deltas.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` is not actual position-lifetime MFE/MAE

It can continue after the real position exits. Use V70 bounded position-lifetime telemetry instead.

### KD-2026-09-03-12 — MFE peak alone cannot simulate trailing exits

Use ordered intra-trade path/tick telemetry.

### KD-2026-09-03-11 — next-cycle association is not same-setup counterfactual edge

Do not infer missed edge from chronological proximity alone.

### KD-2026-09-03-10 — do not promote an archetype from two trades

PULLBACK_SWEEP_BOS has only 2 sent trades; BREAKOUT_RETEST_BOS produced 22/24.

### KD-2026-09-03-09 — selector bars are not independent setups

Use selector -> eval -> pending cycle -> downstream stages -> trade.

### KD-2026-09-03-08 — historical diagnostics must fail closed on accepted evidence identity

Accepted V69 ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

### KD-2026-09-03-07 — ENTRY_EVAL rows are not all-bar opportunity coverage

All-bar coverage: 23,526 M15 rows; LONG 3,576; SHORT 1,744; neutral 18,206.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not SHORT authorization

SHORT remains disabled/rejected.

### KD-2026-09-03-05 — `V64_EVENTS=0` does not mean no market signal

It proves only absence of instrumented pending-state events.

### KD-2026-09-03-04 — DEMO execution transport is already proven

0.01 XAUUSDm BUY+close both returned server `10009 / done`. Do not rerun forced transport without contradictory evidence.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-08 — V70 7.14 baseline gate rejected a valid cost-only replay drift — RESOLVED

Operator raw audit against the exact accepted V69 ZIP produced:

- accepted/current trade count `24/24`;
- accepted/current net `7.14/6.44`;
- `SAME_EXIT_TIMES_VALUE_DRIFT`;
- difference classes `{"EXIT_COST_DRIFT": 1}`;
- only one swap row changed by `-$0.70`.

Resolution:

- preserve the frozen 7.14 historical reference;
- when current net differs, require the hash-pinned raw audit;
- accept only `SAME_EXIT_TIMES_VALUE_DRIFT` with exactly `EXIT_COST_DRIFT` differences;
- independently verify every differing row has identical time, price, gross profit and reason;
- current analyzer net must equal current raw-audit net;
- any cohort/time/price/profit/reason drift still fails closed;
- no tolerance widening and no strategy mutation.

### KH-2026-09-03-07 — policy parser/lifecycle valid but baseline net differed — RESOLVED BY RAW AUDIT

The mismatch was not an instrumentation timing defect. Exit timing/price/gross profit/reason were identical; only one swap value changed.

### KH-2026-09-03-06 — zero-trade month lifecycle requirement — RESOLVED

Use per-month trade/shadow parity.

### KH-2026-09-03-05 — V70 event parser used wrong numeric fields — RESOLVED

Canonical fields are `value1/value2/value3`.

### KH-2026-09-03-04 — old MFE/giveback attribution used post-exit shadow — RESOLVED BY V70

V70 bounds excursion to actual owned-position lifetime.

### KH-2026-09-03-03 — stale static source-string assertion — RESOLVED

Fix stale wording contracts, not strategy semantics.

### KH-2026-09-03-02 — zero event rows treated as fatal — RESOLVED

Zero rows can be valid evidence.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Bridge and regression-test exact-head contracts.

## Trading-system lessons that must not be lost

### KL-01 — V69 losers are fast-loss dominated

24 trades / 10W / 14L / accepted +$7.14; 10/14 losers closed within 60 seconds.

### KL-02 — October concentration indicates regime sensitivity

Accepted month PnL: Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat. Ex-Oct = -$2.01.

### KL-03 — V69/V70 Sep 2025-May 2026 is development-only

It is not untouched holdout evidence.

### KL-04 — V70 exit-harvest did not justify changing real exit semantics

Current same-run baseline is +$6.44. TIERED produced +$7.12, delta +$0.68, PF 1.497554 and DD $3.27, but only four trades changed. EARLY produced +$7.08, delta +$0.64 on two changed trades. The incremental TIERED advantage over EARLY is only $0.04. Retain TIERED as a candidate; do not promote it from this reused 24-trade sample.

### KL-05 — session volatility is conditioning, not a trading rule

Use DST-aware, past-only statistics.

### KL-06 — downstream attrition is mostly structural

Accepted funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`.

### KL-07 — breakout-retest is the current economic engine

BREAKOUT_RETEST_BOS accounts for 22/24 trades.

### KL-08 — next research priority is entry/re-entry quality, not more exit-threshold tuning

Verified weaknesses are fast losses, October concentration and negative ex-October development PnL. Focus successor research on regime/session conditioning, breakout-retest follow-through and post-retest quality without forcing turnover.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Require exact source/evidence identity for historical claims.
- Do not tune thresholds to mask tooling defects.
- Do not widen an accepted PnL tolerance to hide replay drift.
- When counts match but PnL differs, compare raw deals trade-by-trade.
- A cost-only drift exception must be hash-pinned and execution-identity preserving.
- Preserve accepted historical headline separately from current replay economics.
- Do not wait on natural trades when deterministic evidence can answer the question.
- Deduplicate rotated telemetry.
- Candidate ENTRY_EVAL rows are not all-bar coverage.
- All-bar selector rows are context, not setups.
- `short_edge` in LONG-only runtime is abstention, not authorization to activate SHORT.
- Once transport is proven, do not rerun forced probes without contradictory evidence.
- Ignore legacy `2 trades / 48h` dashboard gates.
- Do not loosen a gate from funnel volume alone.
- Do not promote an archetype from two trades.
- Do not simulate trailing exits from peak MFE alone.
- Synthetic telemetry tests must use the real CSV schema.
- Prefer source-pinned reanalysis over unnecessary tester reruns.
- Validate zero-trade months as 0 trades / 0 shadows.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
