# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 07:47 (+07)

## Authority / safety

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active research branch: `agent/v70-exit-harvest-research`.

Always resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI before acting.

SHORT disabled. SHORT remains rejected for activation. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Contract: XAUUSDm M15, LONG only, lot 0.01, planned risk about $0.85-$1.10, emergency guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready, fixed stop, inherited +$2 -> about +$1 profit ratchet.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Gross profit `$22.58`, gross loss `$15.44`. Sep 2025-May 2026 is development-only. Month PnL: Sep -$1.84, Oct +$9.15, Nov +$1.24, Dec -$2.28, Jan +$0.87, Feb-May flat.

## Settled upstream questions

- DEMO execution transport PASS: actual 0.01 XAUUSDm BUY+close returned server `10009 / done` both ways.
- Live no-trade window: 83/83 preserved directional evals were `short_edge` / bearish and rejected by LONG-only isolation. Not broker/order-send failure.
- All-bar selector coverage: 23,526 M15 bars; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.
- Downstream LONG funnel: `460 pending -> 404 micro-arm -> 167 touch -> 95 penetration -> 51 reversal-confirm -> 49 separation -> 24 retest/entry -> 24 deals`. Separation is not the dominant contraction.
- Cycle economics: HARD_STRUCTURAL 235, TTL 120, CONTEXT_QUALITY 80, SENT 24, UNTERMINATED 1. BREAKOUT_RETEST_BOS produced 22/24 trades; PULLBACK_SWEEP_BOS only 2.
- Old `V64_NOISE_SHADOW` MFE/MAE is rejected as actual-trade excursion because it can continue after the real position exits.

## V70 objective and evidence

V70 preserves V69 entry/actual-exit semantics and adds observation-only true position-lifetime telemetry plus four exit shadows:

1. `BASELINE_200_100`: +$2 arm / +$1 floor.
2. `EARLY_100_025`: +$1 / +$0.25.
3. `MID_150_050`: +$1.50 / +$0.50.
4. `TIERED_100_025_200_100`: +$1/+0.25 then upgrade to +$1 after +$2.

The nine-month Sep 2025-May 2026 real-tick campaign completed once. Generated source SHA256: `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`; EX5 SHA256: `af321cdfe2f91b672443ad57aa7f33606d8e41d5660607cc3f74f6bf3f6a3f5f`; compile `0 errors, 0 warnings`. Raw evidence is retained and source-pinned.

Corrected fast reanalysis proved:

- month trade counts Sep 6, Oct 8, Nov 3, Dec 4, Jan 3, Feb-May 0;
- 24 matched trade/shadow lifecycles;
- true median MFE all `$0.625`, winners `$2.525`, losers `$0.00`;
- loser median true MAE `-$1.08`;
- 10 trades reached MFE >=$1, 9 reached >=$2, no realized loser reached >=$2.

Current contemporaneous V70 actual baseline: `24 / 10W / 14L / +$6.44 / PF 1.417098 / DD $3.65`.

## Baseline drift resolved by hash-pinned raw-deal audit

Operator ran `scripts/audit_v70_baseline_drift_against_accepted_v69.py` against the exact accepted V69 ZIP SHA256 `e35306d...`.

Result:

- accepted trades 24, current V70 trades 24;
- accepted net +$7.14, current V70 net +$6.44, delta -$0.70;
- classification `SAME_EXIT_TIMES_VALUE_DRIFT`;
- difference classes exactly `{"EXIT_COST_DRIFT": 1}`;
- all months except Sep are numerically identical;
- only differing exit is Sep trade index 4 at `2025.09.21 22:05:00`;
- accepted/current exit price both `3687.969`;
- accepted/current gross profit both `$3.64`;
- accepted/current exit reason both `5`;
- commission and fee unchanged at zero;
- only swap changed: accepted `$0.00`, current `-$0.70`.

Therefore the V70 observation hook did **not** perturb the tested exit timestamp, exit price, gross profit or exit reason. The -$0.70 is a historical exit-cost/swap value drift, consistent with historical financing-data/model changes between tester runs. The audit does not prove why the swap table changed, so do not label a more specific cause without evidence.

The accepted V69 +$7.14 headline remains frozen historical evidence. The V70 same-run policy comparison uses the contemporaneous +$6.44 baseline; do not rewrite V69 history to 6.44.

## Harness correction after the audit

The V70 runtime no longer fails merely because the contemporaneous baseline net differs from 7.14. It accepts a non-identical net **only** when a hash-pinned raw-deal audit proves all of the following:

- accepted ZIP reproduces 24 trades and about +$7.14;
- current analyzer net equals current raw-deal audit net;
- classification is `SAME_EXIT_TIMES_VALUE_DRIFT`;
- the only difference class is `EXIT_COST_DRIFT`;
- every differing row keeps identical exit time, exit price, gross profit and exit reason.

Any cohort, timing, price, profit or reason drift still fails closed. The 7.14 tolerance was not widened and no strategy threshold changed.

## V70 exit-harvest decision

Same-run policy results on the 6.44 contemporaneous cohort:

- BASELINE_200_100: +$6.48, delta +$0.04, PF 1.419689, DD $3.65, 2 changed trades;
- EARLY_100_025: +$7.08, delta +$0.64, PF 1.494759, DD $3.27, 2 changed trades, one baseline loser improved and one baseline winner cut;
- MID_150_050: +$6.44, delta $0.00, no changed trades;
- TIERED_100_025_200_100: +$7.12, delta +$0.68, PF 1.497554, DD $3.27, 4 changed trades, one baseline loser improved and one baseline winner cut.

Decision: **do not promote an exit-policy semantic change from V70**. TIERED is the best tested candidate and is retained for future validation, but its advantage is only +$0.68 on a reused 24-trade development sample; it changes only four trades, and its incremental gain over EARLY is only $0.04. That is insufficient evidence to mutate the frozen/forward exit contract.

The larger verified economic weaknesses remain entry/regime quality: October concentration, ex-October negative development PnL, and fast-loss-heavy losers. Next research should attack entry/re-entry quality rather than keep tuning exit thresholds on the same 24 trades.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_RAW_NINE_MONTH_EVIDENCE=RETAINED`
`V70_TRADE_SHADOW_PARITY=PASS_24`
`V70_TRUE_LIFETIME_TELEMETRY=NONZERO`
`V70_ACCEPTED_V69_NET_USD=7.14_FROZEN_HISTORY`
`V70_CONTEMPORANEOUS_BASELINE_NET_USD=6.44`
`V70_BASELINE_DRIFT_CLASS=SAME_EXIT_TIMES_EXIT_COST_ONLY`
`V70_BASELINE_DRIFT_SWAP_USD=-0.70_ONE_EXIT`
`V70_EXIT_TIMING_PERTURBATION_HYPOTHESIS=REJECTED_BY_RAW_AUDIT`
`V70_EXIT_POLICY_DECISION=NO_PROMOTION`
`V70_TIERED_POLICY=RETAIN_AS_CANDIDATE_ONLY`
`V70_ENTRY_SEMANTICS_CHANGED=0`
`V70_REAL_EXIT_SEMANTICS_CHANGED=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. No Strategy Tester rerun is required for V70.
2. Require exact-head CI success after the cost-drift gate and handover synchronization.
3. Close V70 exit-harvest as research-only / no promotion.
4. Start the next successor research on a separate branch focused on LONG entry/re-entry quality and regime breadth, not on forcing more trades and not on enabling SHORT.
5. Prioritize features tied to the verified weaknesses: fast-loss avoidance, session/regime conditioning, breakout-retest follow-through and post-retest quality, using past-only data and month-aware validation.
6. Keep TIERED exit policy as a shadow candidate for later independent/prospective validation; do not activate it in frozen V69 or REAL.
7. Do not enable SHORT. Do not authorize REAL money.
