# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 08:00 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-19 — cross-symbol portability must be tested before symbol-specific retuning

V71 starts with XAUUSDm control plus EURUSDm, GBPUSDm, USDJPYm and AUDUSDm using the exact V69 LONG strategy semantics after metadata normalization.

Do not optimize cash-risk, target, separation, ATR, score or timing thresholds per FX pair in the first comparison. The first pass answers whether the existing edge/geometry transfers at the same 0.01 lot and same cash-risk budget. Symbol-specific tuning is a later research question and must not contaminate the portability screen.

Use one full-period real-tick run per symbol and reconstruct monthly metrics from deals. This reduces tester work from 45 monthly passes to five default passes while preserving month-level economic diagnostics.

### KD-2026-09-03-18 — accepted historical PnL and contemporaneous replay PnL may differ because tester costs drift

Hash-pinned V69/V70 raw comparison localized the entire -$0.70 mismatch to one exit-row swap field while exit timestamp, price, gross profit and reason stayed identical. Preserve accepted V69 +$7.14 separately from current replay economics. Never widen a general PnL tolerance to hide cost drift.

### KD-2026-09-03-17 — do not explain baseline mismatch by accounting without checking accepted code

Frozen V69 and V70 both use exit profit + commission + swap + fee for the historical headline. Raw-deal comparison resolved the mismatch.

### KD-2026-09-03-16 — zero-trade periods are valid evidence

A symbol/month can legitimately produce zero trades. Do not fabricate lifecycle evidence or classify zero turnover as a harness failure unless required source/event files are actually missing.

### KD-2026-09-03-15 — do not rerun expensive tester evidence for post-processing-only defects

Reuse source-pinned raw evidence when parser/harness defects can be corrected offline.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` is not actual position-lifetime MFE/MAE

It can continue after the real position exits. V70 bounded lifetime telemetry supersedes it.

### KD-2026-09-03-12 — MFE peak alone cannot simulate trailing exits

Use ordered intra-trade path/ticks for exit counterfactuals.

### KD-2026-09-03-11 — next-cycle association is not same-setup counterfactual edge

Do not infer missed edge from chronological proximity alone.

### KD-2026-09-03-10 — do not promote an archetype from two trades

PULLBACK_SWEEP_BOS has only 2 sent trades; BREAKOUT_RETEST_BOS produced 22/24.

### KD-2026-09-03-09 — selector bars are not independent setups

Use selector -> eval -> pending cycle -> downstream stages -> trade.

### KD-2026-09-03-08 — historical diagnostics must fail closed on evidence identity

Accepted V69 ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

### KD-2026-09-03-07 — ENTRY_EVAL rows are not all-bar opportunity coverage

All-bar coverage: 23,526 M15 rows; LONG 3,576; SHORT 1,744; neutral 18,206.

### KD-2026-09-03-06 — `direction_isolated_out + short_edge` is abstention, not SHORT authorization

SHORT remains disabled/rejected.

### KD-2026-09-03-04 — DEMO execution transport is already proven

0.01 XAUUSDm BUY+close both returned server `10009 / done`. Do not rerun forced transport without contradictory evidence.

## Resolved harness / diagnostic incidents

### KH-2026-09-03-08 — V70 7.14 baseline gate rejected valid cost-only replay drift — RESOLVED

A non-identical current net is accepted only when hash-pinned raw audit proves same execution identity and EXIT_COST_DRIFT only. No strategy mutation or wide tolerance.

### KH-2026-09-03-07 — V70 policy parser/lifecycle valid but baseline net differed — RESOLVED BY RAW AUDIT

The mismatch was one swap row, not instrumentation timing.

### KH-2026-09-03-06 — zero-trade month lifecycle requirement — RESOLVED

Use trade/shadow parity.

### KH-2026-09-03-05 — V70 event parser used wrong numeric fields — RESOLVED

Canonical fields are `value1/value2/value3`.

### KH-2026-09-03-04 — old MFE/giveback attribution used post-exit shadow — RESOLVED BY V70

### KH-2026-09-03-03 — stale static source-string assertion — RESOLVED

Fix stale wording contracts, not strategy semantics.

### KH-2026-09-03-01 — nested exact-HEAD variable mismatch — RESOLVED

Bridge and regression-test exact-head contracts.

## Trading-system lessons that must not be lost

### KL-01 — V69 losers are fast-loss dominated on XAUUSD

24 trades / 10W / 14L / accepted +$7.14; 10/14 losers closed within 60 seconds. V71 is explicitly testing whether this behavior is instrument-specific rather than assuming it is universal.

### KL-02 — October concentration indicates regime sensitivity

Accepted XAU month PnL: Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat; ex-Oct = -$2.01.

### KL-03 — reused Sep 2025-May 2026 history is development-only

V69, V70 and V71 comparisons on this period are not untouched holdout evidence.

### KL-04 — V70 exit-harvest did not justify changing real exit semantics

TIERED remained a candidate only; no promotion.

### KL-06 — downstream attrition is mostly structural

Accepted XAU funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`.

### KL-07 — breakout-retest is the current XAU economic engine

BREAKOUT_RETEST_BOS accounts for 22/24 trades.

## Permanent rules

- Never `git clean`.
- Do not `stash pop` during active runtime/evidence work.
- Use explicit UTF-8 on Windows.
- Keep strategy, broker transport, telemetry and harness failures separate.
- Require exact source/evidence identity for historical claims.
- Do not tune thresholds to mask tooling defects.
- Do not widen an accepted PnL tolerance to hide replay drift.
- Compare raw deals trade-by-trade when counts match but PnL differs.
- Preserve accepted historical headline separately from current replay economics.
- Do not wait on natural trades when deterministic tester evidence can answer the question.
- Candidate ENTRY_EVAL rows are not all-bar coverage.
- All-bar selector rows are context, not setups.
- `short_edge` in LONG-only runtime is abstention, not authorization to activate SHORT.
- Do not loosen a gate from funnel volume alone.
- Do not promote an archetype from two trades.
- Do not simulate trailing exits from peak MFE alone.
- Prefer source-pinned reanalysis over unnecessary tester reruns.
- For cross-symbol research, establish a no-retune portability baseline before any per-symbol optimization.
- Keep one same-run control symbol when comparing instruments so tester cost/feed regime is contemporaneous.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
