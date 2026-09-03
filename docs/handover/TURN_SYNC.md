# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 07:20 (+07)

## User input

Operator reran the V70 source-pinned existing-evidence analysis at exact checkpoint:

`f984f259f122f691b31e8aee3ed5bf639b516dfe`

with no Strategy Tester rerun.

The corrected integrity path passed:

- source SHA256 `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`;
- Sep 6 trades, Oct 8, Nov 3, Dec 4, Jan 3, Feb-May 0;
- `V70_EXISTING_EVIDENCE_LIFECYCLE=PASS matched_trades=24 traded_months=5 zero_trade_months=4`;
- all nine months accepted;
- true position-lifetime telemetry nonzero.

Analyzer output for the current V70 replay cohort:

- 24 trades / 10W / 14L;
- net `+$6.44`, PF `1.417098`;
- median true MFE all `$0.625`;
- median winner true MFE `$2.525`;
- median loser true MFE `$0.00`;
- median loser true MAE `-$1.08`;
- 10 trades reached MFE >=$1;
- 9 reached MFE >=$2;
- 0 realized losers reached MFE >=$2.

Provisional counterfactual policy results on the same 6.44 cohort:

- BASELINE_200_100: net 6.48, delta +0.04;
- EARLY_100_025: net 7.08, delta +0.64, 11W/13L, DD 3.27;
- MID_150_050: net 6.44, delta 0;
- TIERED_100_025_200_100: net 7.12, delta +0.68, 11W/13L, DD 3.27.

The fail-closed baseline gate then correctly stopped because frozen accepted V69 is +7.14.

## Critical correction

The previous explanation that 6.44 versus 7.14 was caused by different accounting conventions is rejected.

The exact frozen V69 analyzer at HEAD `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1` was inspected. Its accepted headline uses exit deals and computes `profit + commission + swap + fee`. Current V70 `legacy_accepted_summary()` uses the same formula and returns 6.44.

Therefore the -$0.70 is genuine baseline/replay drift until localized. Do not weaken the 7.14 guard and do not promote EARLY/TIERED yet.

The current and frozen `build_v69_confirm_separation_retest_source.py` blob SHA is identical (`3af2c43c...`), and the V68 parent builder blob is also identical (`8ea68a2f...`). Git compare from frozen V69 to the current branch does not show inherited V67/V68/V69 builder-chain source modifications. No known threshold change explains the drift.

## Action implemented

Added a focused read-only raw-deal audit:

`scripts/audit_v70_baseline_drift_against_accepted_v69.py`

It finds only the accepted V69 ZIP whose SHA256 is exactly:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

and compares accepted V69 LONG `V64_DEALS.csv` against existing V70 deals for all nine months. It reports each differing exit's timestamp, price, profit, commission/swap/fee, reason and PnL delta, then classifies cohort, exit-timing, same-time value, or mixed drift.

Added `tests/test_v70_baseline_drift_audit.py` and wired it into `v70-exit-harvest-quality`. Dedicated V70 CI passed on the code checkpoint before handover sync.

The audit is read-only: no terminal, MetaEditor, Strategy Tester, order or strategy mutation.

## Decision gate

- If accepted and V70 exit timestamps are the same and only price/profit/cost differs, classify contemporaneous tester/feed/fill value drift; then policy deltas may be judged against the same-run V70 baseline only after documenting that baseline shift.
- If exit timestamps differ, treat V70 instrumentation perturbation as the primary suspect. The V70 shadow hook currently runs before hard-loss/ratchet/soft-loss management in `OnTick`; move it after actual exit management and rerun only if raw-deal evidence proves timing drift.
- If entry/cohort differs, do not interpret V70 policies; inspect cohort drift first.

SHORT remains disabled. REAL authorization remains false.

## Next operator action

Do not rerun Strategy Tester or the V70 policy analyzer. Fast-forward to the final exact branch HEAD after this handover sync and run only the new raw-deal audit. It should finish in seconds if the exact accepted V69 ZIP is still present locally. If the exact ZIP is absent, stop there rather than substituting another artifact.
