# KNOWN FAILURES / DO-NOT-REPEAT REGISTRY

Updated: 2026-09-03 14:15 (+07)

Read this before modifying Windows/MT5 runtime or strategy code.

## Active diagnostic lessons

### KD-2026-09-03-22 — do not generalize XAU fast-loss timing to FX

V71 direct no-retune portability produced XAU fast-loss share 10/14 = 71.43%, but all tested FX pairs had zero losing trades closed within 60 seconds: EURUSD 0/4, AUDUSD 0/4, USDJPY 0/4, GBPUSD 0/16.

This supports an instrument-speed explanation for the <=60s statistic. It does **not** mean the FX strategy is profitable: GBPUSD still lost -$14.43 with PF 0.171 despite zero fast losses.

Therefore fast-loss duration and economic edge must be treated as separate dimensions.

### KD-2026-09-03-21 — direct portability can fail catastrophically even when risk dollars are normalized

Using exact V69 LONG semantics, same 0.01 lot and same $0.85-$1.10 risk band did not produce uniform FX behavior:

- EURUSD +$4.55 / PF 2.060606 / 8 trades;
- AUDUSD +$1.29 / PF 1.305687 / 7 trades;
- USDJPY +$0.21 / PF 1.049065 / 6 trades;
- GBPUSD -$14.43 / PF 0.171166 / 19 trades.

Do not create a generic "Forex version" by pooling these instruments. If one pair is pursued, it needs its own successor research/validation lineage.

### KD-2026-09-03-20 — package accepted raw evidence instead of requesting giant pasted logs

For completed tester campaigns, preserve source-pinned raw evidence in deterministic ZIPs containing analysis, summary, generated source, compile/config text and per-symbol raw CSV telemetry. Include SHA256 manifest metadata and keep packaging read-only with no tester rerun.

V71 packer exports combined full/core packages and per-symbol packages. It excludes EX5 binaries and verifies raw deal-pair counts against analyzed trades.

### KD-2026-09-03-19 — cross-symbol portability must be tested before symbol-specific retuning

V71 started with XAUUSDm control plus EURUSDm, GBPUSDm, USDJPYm and AUDUSDm using exact V69 LONG strategy semantics after metadata normalization.

Do not optimize cash-risk, target, separation, ATR, score or timing thresholds per FX pair in the first comparison. Symbol-specific tuning is a later research question and must not contaminate portability screening.

Use one full-period real-tick run per symbol and reconstruct monthly metrics from deals.

### KD-2026-09-03-18 — accepted historical PnL and contemporaneous replay PnL may differ because tester costs drift

Hash-pinned V69/V70 raw comparison localized the entire -$0.70 mismatch to one exit-row swap field while exit timestamp, price, gross profit and reason stayed identical. Preserve accepted V69 +$7.14 separately from current replay economics. Never widen a general PnL tolerance to hide cost drift.

### KD-2026-09-03-17 — do not explain baseline mismatch by accounting without checking accepted code

Frozen V69 and V70 both use exit profit + commission + swap + fee for the historical headline. Raw-deal comparison resolved the mismatch.

### KD-2026-09-03-16 — zero-trade periods are valid evidence

A symbol/month can legitimately produce zero trades. Do not fabricate lifecycle evidence or classify zero turnover as a harness failure unless required source/event files are actually missing.

### KD-2026-09-03-15 — do not rerun expensive tester evidence for post-processing-only defects

Reuse source-pinned raw evidence when parser/harness/packaging work can be corrected offline.

### KD-2026-09-03-13 — `V64_NOISE_SHADOW` is not actual position-lifetime MFE/MAE

It can continue after the real position exits. V70 bounded lifetime telemetry supersedes it for actual-trade excursion claims.

### KD-2026-09-03-12 — MFE peak alone cannot simulate trailing exits

Use ordered intra-trade path/ticks for exit counterfactuals.

### KD-2026-09-03-11 — next-cycle association is not same-setup counterfactual edge

Do not infer missed edge from chronological proximity alone.

### KD-2026-09-03-10 — do not promote an archetype from two trades

PULLBACK_SWEEP_BOS has only 2 sent XAU trades; BREAKOUT_RETEST_BOS produced 22/24.

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

### KL-01 — V69 XAU losers are fast-loss dominated, but V71 FX losers are not

XAU: 24 trades / 10W / 14L; 10/14 losers <=60 seconds. V71 FX: zero <=60-second losers across EURUSD/AUDUSD/USDJPY/GBPUSD. Do not use one timing threshold across instruments without evidence.

### KL-02 — XAU October concentration indicates regime sensitivity

Accepted XAU month PnL: Sep -$1.84; Oct +$9.15; Nov +$1.24; Dec -$2.28; Jan +$0.87; Feb-May flat; ex-Oct = -$2.01.

### KL-03 — reused Sep 2025-May 2026 history is development-only

V69, V70 and V71 comparisons on this period are not untouched holdout evidence.

### KL-04 — V70 exit-harvest did not justify changing real exit semantics

TIERED remained a candidate only; no promotion.

### KL-06 — downstream XAU attrition is mostly structural

Accepted XAU funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`.

### KL-07 — breakout-retest is the current XAU economic engine

BREAKOUT_RETEST_BOS accounts for 22/24 XAU trades.

### KL-08 — EURUSD is the leading V71 FX screen, not a validated strategy

EURUSD: 8 trades / 4W / 4L / +$4.55 / PF 2.060606 / DD $3.30. Only two positive months and two negative months; five months flat. Treat as candidate-selection evidence only.

### KL-09 — GBPUSD direct portability is rejected

GBPUSD: 19 trades / 3W / 16L / -$14.43 / PF 0.171166 / DD $16.32 / zero positive months. Do not tune around this failure inside the same portability screen.

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
- Prefer source-pinned reanalysis/packaging over unnecessary tester reruns.
- For cross-symbol research, establish a no-retune portability baseline before any per-symbol optimization.
- Keep one same-run control symbol when comparing instruments so tester cost/feed regime is contemporaneous.
- Do not equate slower losses with positive edge.
- Do not pool FX pairs into one strategy just because all are Forex.
- SHORT remains disabled unless separately researched and explicitly approved.
- REAL money remains fail-closed until a separate explicit deployment/risk decision.
