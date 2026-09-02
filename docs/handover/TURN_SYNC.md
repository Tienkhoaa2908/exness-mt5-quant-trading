# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 05:10 (+07)

## User input

Operator ran the V69 MFE/giveback recovery at exact checkpoint:

`12c97d81d6846b2b0c81cad234d698c25c9a3341`

The run completed PASS, reproduced accepted V69 development deal identity and sent zero orders.

The user then asked for the current status and explicitly pushed to stop repeating long diagnostic loops and move the project forward faster.

## Operator output — valid evidence

Accepted development identity reproduced:

`24 trades / 10W / 14L / +$7.14`.

All 24 deals matched a `V64_NOISE_SHADOW` row by entry timestamp.

Profit-ratchet events inside actual entry->exit windows:

- `PROFIT_LOCK` event trades `9`;
- modified trades `9`;
- modify-failed trades `0`.

The run itself was read-only:

- strategy changed `0`;
- orders sent `0`;
- SHORT remained disabled;
- REAL authorization remained false.

## Critical source-audit correction

The initial MFE/giveback output appeared to show very large profit excursion and severe giveback. That interpretation is rejected after source audit.

`V64NoiseStart()` begins its noise shadow at actual fill, but `V64UpdateNoiseShadows()` does not terminate that shadow at the actual deal exit. The shadow remains alive until its synthetic 3x3 stop/target matrix resolves or `InpV64NoiseShadowMaxMinutes=480` is reached.

Therefore `V64_NOISE_SHADOW.max_pnl/min_pnl` is a post-entry synthetic path metric, not actual position-lifetime MFE/MAE.

Consequences:

- old median MFE winner/loser values are invalid as actual-trade MFE;
- old median giveback and MFE-capture ratios are invalid for exit tuning;
- old `22/24 MFE >= $2` and `17/22 realized below $1` counts are invalid as actual-trade threshold evidence;
- extreme values such as `$29`, `$46`, `$118` can occur after the real trade has already closed;
- the valid in-trade event evidence is the `9/9` successful logged profit-lock modify attempts and the actual deal economics.

This is a diagnostic-attribution defect, not a broker or strategy-execution defect.

Do not tune V69 exit thresholds from the old noise-shadow MFE output.

## Decision

Do not continue the previous chain of read-only analyzers.

Do not loosen entry filters yet.

Run one decisive, ordered-tick V70 replay that:

1. keeps the V69 entry cohort and actual exit behavior unchanged;
2. tracks high-water/low-water only while the actual owned position is open;
3. evaluates several exit-harvest policies simultaneously in shadow;
4. produces direct economics for each policy on the same actual-entry cohort;
5. either identifies one candidate worth promoting or closes the exit-harvest hypothesis.

This avoids four separate tester campaigns and removes the V64 post-exit attribution problem.

## V70 branch and implementation

New branch created from the exact green V69 demo checkpoint:

`agent/v70-exit-harvest-research`

Parent:

`12c97d81d6846b2b0c81cad234d698c25c9a3341`

Pre-handover V70 implementation checkpoint:

`968976e33eddc2ae205a882ff3eea4b7d3dc92ef`

Files added:

- `scripts/build_v70_exit_harvest_shadow_source.py`;
- `scripts/analyze_v70_exit_harvest_shadow.py`;
- `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH.py`;
- `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh`;
- `tests/test_v70_exit_harvest_research.py`;
- `.github/workflows/v70_exit_harvest_quality.yml`.

### Preserved actual strategy contract

V70 research keeps:

- XAUUSDm M15;
- LONG only;
- lot `0.01`;
- V69 entry state machine;
- separation `>= $1.30`;
- confirmation age `>=30s`;
- target `+$3.50`;
- inherited actual profit ratchet `+$2 -> about +$1`;
- actual V69-equivalent exit behavior unchanged;
- SHORT disabled;
- REAL authorization false.

The V70 shadow helper cannot call `PositionClose`, `PositionModify`, `.Buy()` or `.Sell()`.

### True position-lifetime excursion

V70 starts its exit shadow only when an actual owned position exists, updates cash PnL every tick while that position remains open, and ends when the actual position disappears.

The V70 analyzer explicitly does not consume `V64_NOISE_SHADOW`.

### Four simultaneous shadow policies

- `BASELINE_200_100`: idealized current `+$2` arm / `+$1` floor validation lane;
- `EARLY_100_025`: `+$1` arm / `+$0.25` floor;
- `MID_150_050`: `+$1.50` arm / `+$0.50` floor;
- `TIERED_100_025_200_100`: early `+$1/+0.25`, then upgrade to `+$1` floor after `+$2`.

Each policy records its first arm/upgrade/trigger in ordered real-tick replay. It does not alter the actual tester position.

The analyzer reports actual economics and policy economics including:

- net PnL;
- PF;
- realized drawdown;
- changed-trade count;
- baseline winners cut by the candidate;
- baseline losses improved by the candidate;
- true in-position MFE/MAE counts.

The same run covers all Sep 2025-May 2026 LONG months on real tick model 4.

## CI

At pre-handover checkpoint `968976e33eddc2ae205a882ff3eea4b7d3dc92ef` all six workflows completed successfully:

- `v70-exit-harvest-quality` run `33687927019` — success;
- `v69-upstream-diag-quality` run `33687927023` — success;
- `v69-forward-quality` run `33687926961` — success;
- `v69-quality` run `33687926978` — success;
- `v68-quality` run `33687926942` — success;
- full `quality` run `33687926995` — success.

Handover synchronization commits follow that checkpoint. Resolve the final branch HEAD and require all six exact-head workflows `completed/success` before operator execution.

## Current status

Completed/localized:

- broker transport;
- live zero-trade cause;
- all-bar selector opportunity;
- downstream LONG funnel;
- cycle economics;
- V64-noise-shadow attribution bug.

Current active work:

`V70_TRUE_POSITION_LIFETIME_EXIT_HARVEST_REPLAY`.

This is not another natural-trade waiting gate. It is one deterministic Strategy Tester campaign with four candidate exit shadows in parallel.

## Next operator action

After the final V70 HEAD is exact-CI-green:

1. close MT5 and MetaEditor once because this run needs Strategy Tester and MetaEditor compile;
2. fast-forward only to the exact final `agent/v70-exit-harvest-research` SHA;
3. export `V70_EXIT_HARVEST_EXPECTED_HEAD` to that SHA;
4. run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once;
5. return the final true-excursion and four `POLICY_*` summaries plus `V70_EXIT_HARVEST_RESEARCH=PASS`, or the exact FATAL.

Decision after the replay:

- if no shadow policy improves the baseline without unacceptable winner damage, close exit-harvest research and return to entry/re-entry quality;
- if one policy materially improves reused development economics, promote only that policy into a separate actual-exit semantic branch and replay actual tester execution;
- do not call the reused Sep-May result independent evidence;
- do not enable SHORT;
- do not authorize REAL.
