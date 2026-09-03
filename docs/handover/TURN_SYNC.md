# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 07:45 (+07)

## User input

Operator ran the focused V70 accepted-baseline raw-deal audit at exact checkpoint:

`79e48be0469bf4324ee11b7e2708e980b62caa76`

The accepted V69 ZIP identity passed exactly:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Audit result:

- `V70_BASELINE_AUDIT_TRADES=accepted:24 v70:24`;
- accepted net `7.14`, V70 net `6.44`, delta `-0.70`;
- classification `SAME_EXIT_TIMES_VALUE_DRIFT`;
- difference classes `{"EXIT_COST_DRIFT": 1}`;
- only Sep differs; Oct-Jan are identical and Feb-May remain zero-trade;
- affected exit is Sep trade index 4 at `2025.09.21 22:05:00`;
- accepted/current price `3687.969` identical;
- accepted/current gross profit `$3.64` identical;
- accepted/current reason `5` identical;
- accepted swap `$0.00`, V70 swap `-$0.70`;
- commission and fee remain zero.

`V70_BASELINE_DRIFT_AUDIT=PASS`.

## Classification

The previous suspicion that the V70 observation hook might have changed exit timing is rejected by the raw evidence for this mismatch. The -$0.70 is entirely an exit-cost/swap value drift with unchanged tested exit timestamp, price, gross profit and reason.

The audit supports a conservative interpretation: historical financing/cost data or tester cost modeling changed between the accepted V69 run and the current V70 run. It does not identify the exact external source of that swap-table change.

Accepted V69 remains frozen at +$7.14. Current V70 policy economics should be compared to the same-run +$6.44 baseline; do not rewrite historical V69 results.

## Code action

The V70 runtime baseline gate was corrected without changing strategy semantics.

Old behavior:

- any current baseline outside `7.14 +/- 0.05` failed, even when raw execution identity was unchanged and only historical costs drifted.

New behavior:

- exact +7.14 still passes normally;
- a non-identical current net requires the hash-pinned accepted V69 raw audit;
- accepted ZIP must reproduce 24 trades and about +$7.14;
- current analyzer net must exactly match current raw-audit net;
- only `SAME_EXIT_TIMES_VALUE_DRIFT` is considered;
- difference classes must be exactly `EXIT_COST_DRIFT`;
- each differing row is independently checked for identical exit time, price, gross profit and reason;
- any cohort, timing, price, gross-profit or reason change fails closed.

The accepted-net tolerance was not widened. No V69/V70 entry, actual exit, LONG-only, SHORT or REAL semantic changed.

Regression tests now cover:

- exact accepted baseline;
- cost-only drift accepted only with raw audit;
- non-identical baseline without audit rejected;
- price drift rejected;
- timing drift rejected;
- hidden exit-reason change rejected;
- existing lifecycle and zero-trade protections retained.

Dedicated V70 CI passed on the code checkpoint before final handover synchronization.

## Economic decision

Same-run policy results from the corrected V70 evidence remain:

- BASELINE_200_100: `+$6.48`, delta `+$0.04`, PF `1.419689`, DD `$3.65`;
- EARLY_100_025: `+$7.08`, delta `+$0.64`, PF `1.494759`, DD `$3.27`, 2 changed trades;
- MID_150_050: `+$6.44`, delta `$0.00`;
- TIERED_100_025_200_100: `+$7.12`, delta `+$0.68`, PF `1.497554`, DD `$3.27`, 4 changed trades.

Decision: no exit-policy semantic promotion from V70. TIERED remains the strongest candidate, but +$0.68 on a reused 24-trade development sample, with only four changed trades and only +$0.04 incremental benefit over EARLY, is not enough to justify mutating the frozen/forward exit contract.

V70 exit-harvest is therefore closed as research-only / no promotion. The next successor research should target the larger verified weaknesses: fast-loss avoidance, regime/session breadth, breakout-retest follow-through and post-retest entry quality.

## Safety

SHORT remains disabled/rejected.
REAL money remains unauthorized.
No Strategy Tester rerun is required for this V70 resolution.

## Next action

1. Require all exact-head workflows to complete successfully after final handover synchronization.
2. Do not ask the operator to rerun V70 merely to reproduce already-established evidence.
3. Start the next successor research on a separate branch focused on LONG entry/re-entry quality.
4. Retain TIERED as shadow-only candidate for later independent/prospective validation.
5. Do not enable SHORT and do not authorize REAL money.
