# V62 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v62-direction-isolated-entry-refinement-research`
- V62 is Strategy Tester research only. REAL-money authorization remains false.

## Accepted V61 evidence motivating V62

Accepted V61 evidence/source head: `65cb308818a835c25e5fff17d8d71351ab901267`.
Accepted V61 evidence ZIP SHA256: `1a421abe21d2879c25dd2ea1e46cd3ce29308c25d0e364bb611d53b1d0ba571f`.

V61 dedicated screen covered 23,526 M15 rows from 2025-09-01 through 2026-08-28 and observed 3,576 LONG plus 1,744 SHORT strict directional signals. Thus the directional engine is not long-only.

V61 Model=4 execution over its selected windows produced four feasible trades, all LONG: 3 wins / 1 loss, net about `+$6.39`, PF about `8.26`, average win about `+$2.42`, average loss `-$0.88`, maximum loss `-$0.88`. Profit-lock modification succeeded three times and failed zero times. Shadow `$3` outperformed `$2` in that tiny sample; `$4` failed.

Critical limitation: V61 did not direction-isolate its real-tick passes. LONG trades could occur in SHORT-labelled weeks. Therefore V61 contains no valid SHORT broker-PnL evidence.

Within the two V61 SHORT-labelled windows there were 38 SHORT directional signals but zero feasible SHORT entries at the `$0.75-$1.25` structural-risk band. Among candidates reaching cash-risk calculation, approximate SHORT risk ranged from `$2.39` minimum to `$4.94` median and about `$9.66` maximum. Both M15 and M5 stop sources remained too far from market entry. This motivates entry refinement rather than widening the risk cap.

## V62 frozen objective

User approved both requirements:

1. validate actual SHORT as well as LONG execution;
2. seek more trades while preserving the small-loss priority.

V62 keeps:

- XAUUSDm M15
- fixed lot `0.01`
- structural risk band `$0.75-$1.25`
- primary target `+$3`
- profit ratchet `+$2 -> protect +$1`
- strict H4/H1 trend logic and symmetric directional scoring
- `OrderCheck()` before simulated broker submission
- tester-only scope

V62 does **not** widen the stop budget merely to force frequency.

## V62 entry-refinement architecture

- M15 signal arms a pending setup instead of entering immediately.
- Pending setup is direction-isolated at generated-EA level.
- Closed M5 data must show trend-aligned retrace/retest near EMA20.
- Closed M1 data must show a turn back in the trade direction.
- Structural stop/target and 0.01 cash risk are recalculated at the refined market price.
- If structural risk remains outside `$0.75-$1.25`, the setup waits or expires.
- Pending setup expires after 240 minutes.
- A setup is cancelled if structural invalidation is breached before entry.
- No fabricated tighter stop is allowed.

## Fixed one-month validation protocol

No PnL-based window selection is used. The latest four complete weeks available in August 2026 are fixed:

- week1: 2026.08.03 -> 2026.08.08
- week2: 2026.08.10 -> 2026.08.15
- week3: 2026.08.17 -> 2026.08.22
- week4: 2026.08.24 -> 2026.08.29

Each week runs two independent Model=4 real-tick passes:

- LONG-only expert (`InpV62AllowedDirection=+1`)
- SHORT-only expert (`InpV62AllowedDirection=-1`)

Total: exactly 8 real-tick passes.

The analyzer reports each week and direction separately, then monthly LONG, monthly SHORT, and a combined isolated-pass sum. The combined isolated-pass sum is not a concurrent account equity curve.

## Required V62 files

- `scripts/build_v62_direction_isolated_entry_refinement_source.py`
- `scripts/analyze_v62_direction_isolated_entry_refinement.py`
- `runtime/v62_direction_isolated_entry_refinement/RUN_V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT.py`
- `runtime/v62_direction_isolated_entry_refinement/START_V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT_GIT_BASH.sh`
- `tests/test_v62_direction_isolated_entry_refinement_static.py`
- `docs/adr/ADR-064-v62-direction-isolated-entry-refinement-research.md`
- this handoff

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60/V61 merely to recover V62.
- Do not use `git clean`.
- Do not `stash pop` while runtime/tester work is active.
- Do not overwrite accepted historical evidence.
- Do not arm or execute REAL-money trading.
- Do not claim Windows PASS until both V62 direction-specific sources compile MetaEditor 0/0 and all eight Model=4 passes complete with evidence ZIP.
- Do not interpret an isolated-pass LONG+SHORT sum as concurrent portfolio equity.
- If SHORT still has zero refined entries, inspect pending/refinement rejection counts before changing the loss budget.

## What a new chat should do next

1. Read this file and `docs/handoff/V61_RECOVERY_STATE.md`.
2. Resolve the latest exact head of `agent/v62-direction-isolated-entry-refinement-research`.
3. Verify GitHub Actions on that exact head.
4. Run only the V62 launcher after MT5 and MetaEditor are closed.
5. Require MetaEditor `0 errors, 0 warnings` for LONG and SHORT experts.
6. Require eight `V62_REAL_TICK_PASS_DONE` markers and an evidence ZIP.
7. Analyze week1/week2/week3/week4 separately; within each week analyze LONG and SHORT separately.
8. Focus on trade count, win rate, average loss, max loss, SHORT refined-entry count, pending expiry/invalidation reasons and refinement wait reasons.
