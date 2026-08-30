# ADR-070 — V68 V67 holdout stability research

Status: research / Strategy Tester only.

## Context

Accepted V67 evidence on head `782b44a566c772f833cb666ead1bbb21ce150b75` compiled LONG and SHORT with `0 errors, 0 warnings` and completed all 12 frozen Model=4 passes. Evidence ZIP SHA256 is `545b0baecba5f9ce077b692be90803623b23106b41eca43ef2728214c4d3707b`.

V67 benchmark LONG produced 4 trades, 3 wins / 1 loss, net `+$6.81`, PF about `6.82`, with three positive weeks, one flat week and no negative benchmark week. The single LONG loss was `-$1.17`; only one LONG loser occurred within 60 seconds. The LONG loser did not become a stop-then-later-target case in the independent noise shadow. Bearish SHORT produced one trade, one loss, `-$1.10`; that SHORT stop later reached all shadow targets, so SHORT remains unvalidated.

The post-zone penetration + closed-M1 reclaim change therefore appears technically promising, but the sample is too small to justify further parameter tuning or promotion.

## Decision

V68 is validation-only. There is no strategy threshold change relative to V67.

Generated V68 MQL must normalize byte-for-byte back to generated V67 MQL after reverting only these observability/runtime substitutions:

- version `68.00` -> `67.00`;
- magic `680068` -> `670067`;
- FILE_COMMON root `v68_v67_holdout_stability` -> `v67_post_zone_reclaim_quality`;
- trade comment `V68 HOLDOUT` -> `V67 RECLAIM`.

All entry, stop, target, trend, microstructure, penetration, reclaim, TTL, profit-lock and loss-control logic remains unchanged.

## Holdout protocol

Run direction-isolated Model=4 real-tick tests for every calendar month from 2025-09 through 2026-05. Each month is tested LONG and SHORT independently.

Windows:

- 2025-09-01 -> 2025-10-01;
- 2025-10-01 -> 2025-11-01;
- 2025-11-01 -> 2025-12-01;
- 2025-12-01 -> 2026-01-01;
- 2026-01-01 -> 2026-02-01;
- 2026-02-01 -> 2026-03-01;
- 2026-03-01 -> 2026-04-01;
- 2026-04-01 -> 2026-05-01;
- 2026-05-01 -> 2026-06-01.

Total = 18 Model=4 passes.

These months exclude the June-July-August windows used directly in V64-V67 calibration/evidence. They are a holdout relative to the V67 calibration sequence, not a claim that no earlier project version ever inspected those dates.

## Evaluation

LONG and SHORT remain independent lanes. No lane is promoted because the opposite lane is profitable.

There is no fixed trades-per-week quota and no fixed weekly-dollar-profit quota. The primary evidence is:

- net expectancy and PF;
- number of positive, negative and flat months;
- median and worst monthly PnL;
- monthly dispersion and negative-month streaks;
- realized drawdown and max single loss;
- losing-trade duration, especially <=15/30/60 seconds;
- stage conversion from micro arm through reclaim to order;
- independent noise-shadow stop-first vs target-first behavior.

## Safety

V68 is Strategy Tester research only. REAL-money authorization is false. Do not `git clean`, do not `stash pop` while MT5/tester work is active, and do not rerun older milestones merely for recovery.
