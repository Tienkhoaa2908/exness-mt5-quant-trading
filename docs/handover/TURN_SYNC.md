# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 02:25 (+07)

## User input

Operator ran the enhanced read-only upstream diagnostic at exact checkpoint:

`931caf8949564ecaad65a524a9f55f16f044593d`

MT5 remained running. The diagnostic completed cleanly with no orders and REAL authorization false.

## Exact operator evidence

Pending-state/event funnel across preserved sources:

- analyzed sources `8`;
- total `V64_EVENTS.csv` data rows `0`;
- sources with event rows `0`;
- `PENDING_ARM=0`;
- `MICRO_ENTRY_ARM=0`;
- `MICRO_ENTRY_ZONE_TOUCH=0`;
- `MICRO_ENTRY_PENETRATION=0`;
- `POST_ZONE_CONFIRM_WAIT=0`;
- `POST_ZONE_REVERSAL_CONFIRM=0`;
- `POST_CONFIRM_SEPARATION=0`;
- `POST_CONFIRM_RETEST_READY=0`;
- `POST_CONFIRM_ENTRY_READY=0`;
- natural closed V69 deals `0`;
- upstream classification `INITIAL_SETUP_OR_PENDING_ARM_BLOCK`.

Pre-pending ENTRY_EVAL:

- richest root: `Common\Files\mt5_quant\_v69_forward_previous_20260901_140447_333776Z`;
- richest-root rows `46`;
- raw rows summed across four roots `83`;
- roots with rows `4`;
- classification `DIRECTION_ISOLATION_BLOCK_BEFORE_PENDING_ARM`;
- blocker `direction_isolated_out`;
- decision reasons `{"short_edge": 46}`;
- reject reasons `{"direction_isolated_out": 46}`;
- selected directions `{"-1": 46}`;
- diagnostic PASS;
- launcher PASS;
- MT5 can remain running `1`;
- orders sent `0`;
- REAL authorization `0`.

## Decisive interpretation

The live no-trade path is now localized more precisely for the richest preserved source.

Those 46 evaluations did not fail at broker execution, reclaim confirmation, separation or retest. The inherited selector selected direction `-1`; V69's frozen LONG-only isolation then logged `direction_isolated_out` and returned before `PENDING_ARM`.

Code review of inherited V59 selector confirms `short_edge` requires:

- `h1_trend == -1 && h4_trend != 1`;
- at least one short trigger (BOS/CHOCH, FVG, liquidity sweep, order-block retest, or aligned pullback/M15 trend);
- short score >= configured minimum;
- short-minus-long score edge >= configured minimum.

Thus `short_edge` is a real selector eligibility result, not a cosmetic label. It does not prove profitable SHORT expectancy and does not authorize SHORT.

## Remaining ambiguity

The raw `83` ENTRY_EVAL rows across four roots cannot yet be treated as 83 unique market evaluations. FILE_COMMON telemetry rotation can preserve copies of the same rows in multiple roots.

The next diagnostic must exact-row deduplicate all roots and answer:

1. how many unique evaluations exist;
2. whether any unique LONG selector rows exist outside the richest 46-row source;
3. whether SHORT selections consistently coincide with the selector-defined short HTF regime and short-trigger state;
4. how long/short score relations and component directions behave by root/time.

## Code work this turn

Diagnostic-only changes were added to `agent/v69-one-shot-prospective-demo`. Frozen V69 strategy semantics were not changed.

### Analyzer

`scripts/analyze_v69_pre_pending_eval.py` now:

- aggregates all current/archive ENTRY_EVAL roots;
- exact-row deduplicates copied archive rows;
- mirrors V59 HTF-regime predicates;
- mirrors V59 trigger predicates from logged fields;
- reports LONG/SHORT score relation;
- reports H1/H4 trend distributions;
- reports direction by HTF regime and trigger state;
- reports component-direction counts;
- reports score min/max/mean and long-minus-short margin;
- reports per-source summaries.

### Runtime

`RUN_V69_UPSTREAM_SIGNAL_DIAG.py` protocol advanced to v4 and prints:

- `V69_PRE_PENDING_ALL_RAW_ROWS`;
- `V69_PRE_PENDING_ALL_UNIQUE_ROWS`;
- `V69_PRE_PENDING_ALL_DUPLICATE_ROWS_REMOVED`;
- `V69_PRE_PENDING_ALL_CONTEXT` and next action;
- aggregate decision/reject/direction counts;
- HTF regime, trigger-state and score-relation counts;
- H1/H4 trends;
- direction grouped by HTF/trigger;
- component directions;
- score summary;
- per-root source summary.

The runtime remains strictly read-only: no MetaEditor, no MT5 restart, no order calls, no strategy changes.

### Tests and CI incident

New tests cover:

- exact-row dedup across rotated roots;
- mixed LONG/SHORT aggregate evidence;
- all-short-edge / short-HTF-regime abstention classification;
- v4 runtime marker contract.

Checkpoint `85572066021b0f90f30e242d20f5e21c0d239116` had one CI failure caused only by a stale static source-string assertion. All substantive new aggregation tests had already passed.

The assertion was corrected without changing runtime semantics.

Corrected code checkpoint:

`56787feaf6370da4cd766d917ad602bdb40f01fa`

All five workflows on that exact code checkpoint completed successfully:

- `v69-upstream-diag-quality`;
- `v69-forward-quality`;
- `v69-quality`;
- `v68-quality`;
- full `quality`.

## Economic direction after the next read-only run

If all deduplicated unique rows are `short_edge` in selector-defined short HTF regime:

- frozen V69 LONG was abstaining consistently with its inherited direction selector;
- do not loosen LONG merely to manufacture turnover;
- do not activate the old rejected SHORT implementation;
- move to economic research on LONG regime availability/quality and, only as a separate research line, a newly validated SHORT/successor architecture.

If any unique LONG selector rows exist:

- inspect their reject reasons and earliest downstream gate;
- `no_complete_archetype` means candidate/archetype construction is the next bottleneck;
- `invalid_arm_structural_stop` means M15 stop geometry is the next bottleneck;
- pending eval without `PENDING_ARM` requires state/telemetry integration review.

## Safety and strategy status

- frozen V69 semantics unchanged;
- DEMO execution transport PASS;
- LONG only;
- SHORT disabled/rejected;
- no automatic REAL promotion;
- REAL authorization false;
- no order sent by current diagnostic work.

## Next operator action

After this documentation sync resolves to a final exact CI-green branch HEAD:

1. leave MT5 running;
2. fast-forward only to the exact final HEAD;
3. run `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh` once;
4. return the markers from `V69_PRE_PENDING_ALL_RAW_ROWS=` through `V69_PRE_PENDING_ALL_SOURCE_SUMMARY=` plus final PASS/FATAL;
5. do not wait for another natural trade and do not rerun the execution probe.
