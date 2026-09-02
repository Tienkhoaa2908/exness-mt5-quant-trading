# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 06:50 (+07)

## User input

Operator supplied the complete first nine-month V70 Windows replay from checkpoint `6d4095f1903f15077fdf805fda1f4485f4ffd314`.

The campaign itself succeeded through source generation, MetaEditor compile (`0 errors, 0 warnings`), and all nine Sep 2025-May 2026 real-tick tester months. Raw evidence directories were written for every month.

The first Python post-processing printed 24 trades, economic round-trip net `+$6.44`, all-zero `TRUE_EXCURSION`, policy lines, then failed closed against the legacy accepted `+$7.14` headline.

## Classification

Do not use any policy number from that first analyzer output. The apparent `EARLY_100_025` delta is invalid.

Source audit identified two analyzer/harness defects, not a strategy/broker/tester failure:

1. Real `V64_EVENTS.csv` numeric fields are `value1/value2/value3`; V70 read `v1/v2/v3`, so excursion and policy trigger numeric values became zero.
2. The accepted V69 headline and full economic round-trip PnL use different cost accounting conventions. The accepted identity is 24/10/14/~+$7.14 under legacy exit-row accounting; honest policy economics use entry+exit explicit costs and produced `+$6.44` on this cohort.

## Fixes completed

V70 now:

- parses real `value1/value2/value3` event columns;
- tests the real telemetry schema;
- reports `legacy_accepted_identity` separately from `economic_roundtrip_actual`;
- gates accepted V69 identity using legacy 24/10/14/~+$7.14;
- compares policy economics consistently against the full round-trip baseline;
- fails closed if true excursion/policy telemetry remains all-zero.

## Fast-path improvement

A second full nine-month tester campaign is no longer the primary recovery path because the raw tester evidence already exists and the defects were in post-processing.

V70 now supports:

`V70_REANALYZE_EXISTING=1`

This mode:

- SHA-pins local `OUTPUT_V70/V70ExitHarvestShadowLong.mq5` against the current builder output;
- requires all nine existing monthly run directories;
- requires non-empty `V64_DEALS.csv` and `V64_EVENTS.csv` in each;
- requires `V70_EXIT_SHADOW_START` and `V70_EXIT_SHADOW_END` lifecycle markers;
- runs only the corrected analyzer and fail-closed guards;
- skips MT5 locator/process gate, MetaEditor compile and Strategy Tester launch.

Expected fast-path markers:

- `V70_EXISTING_EVIDENCE_SOURCE_IDENTITY=PASS`
- `V70_EXISTING_EVIDENCE_MONTHS=PASS count=9`
- `V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS`
- `V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS`
- `V70_EXISTING_EVIDENCE_REANALYSIS=1`
- `V70_EXIT_HARVEST_RESEARCH=PASS`

If source/evidence integrity fails, only then run the full nine-month tester fallback.

## Current code state

Active branch: `agent/v70-exit-harvest-research`.

Existing-evidence reanalysis code/test checkpoint before this handover synchronization:

`a30ed2b77ec38fa82a2d184cd1db39002c1ea205`

All six exact-head checks on that checkpoint completed successfully, including full `quality`, V70 exit-harvest static, V69 forward/static, V68 static and upstream read-only.

No strategy semantics changed. SHORT remains disabled. REAL authorization remains false.

## Next operator action

After resolving the final branch HEAD created by this handover sync and verifying all six exact-head workflows are green:

1. fast-forward to the exact final HEAD;
2. export `V70_EXIT_HARVEST_EXPECTED_HEAD` to that SHA;
3. export `V70_REANALYZE_EXISTING=1`;
4. run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once;
5. return the two evidence-integrity markers, legacy/economic baseline lines, `TRUE_EXCURSION`, four corrected `POLICY_*` lines, both PASS guards and final V70 PASS.

This should be a seconds-scale reanalysis, not another tester campaign. MT5/MetaEditor state is irrelevant to this reanalysis path.
