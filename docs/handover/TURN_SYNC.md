# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 03:21 (+07)

## User input

Operator successfully ran the read-only V69 selector-coverage recovery at exact checkpoint:

`4f584ec4b8207c3f3ea2d7a9e3a95b27bcc91f60`

MT5 remained running. No MetaEditor was required, no orders were sent, frozen strategy semantics were unchanged and REAL authorization remained false.

## Exact operator evidence

Directional-core identity:

- exact match `true`;
- no function mismatches;
- no threshold mismatches;
- checked feature helpers, scoring, `V64BuildFeatures`, `V64SelectDirection`;
- checked `InpV64MinDirectionalScore` and `InpV64MinScoreEdge`.

All-bar coverage:

- unique M15 rows `23,526`;
- first `2025.09.01 00:00:00`;
- last `2026.08.28 20:45:00`;
- feature ready `100%`;
- LONG selected `3,576`;
- SHORT selected `1,744`;
- neutral `18,206`;
- LONG `15.2002%` of all bars;
- SHORT `7.4131%`;
- neutral `77.3867%`;
- LONG share among directional selections `67.218%`;
- SHORT share `32.782%`;
- HTF regimes: LONG `9,235`, neutral `8,157`, SHORT `6,134`.

Decision reasons:

- `long_edge=3576`;
- `short_edge=1744`;
- `regime_neutral=12669`;
- `score_below_threshold=3497`;
- `no_trigger=2040`.

Monthly selected directions:

- 2025-09: LONG `630`, SHORT `0`, neutral `1383`;
- 2025-10: LONG `512`, SHORT `121`, neutral `1475`;
- 2025-11: LONG `278`, SHORT `91`, neutral `1454`;
- 2025-12: LONG `478`, SHORT `35`, neutral `1492`;
- 2026-01: LONG `579`, SHORT `9`, neutral `1334`;
- 2026-02: LONG `232`, SHORT `85`, neutral `1513`;
- 2026-03: LONG `51`, SHORT `365`, neutral `1616`;
- 2026-04: LONG `200`, SHORT `172`, neutral `1559`;
- 2026-05: LONG `57`, SHORT `265`, neutral `1600`;
- 2026-06: LONG `14`, SHORT `425`, neutral `1569`;
- 2026-07: LONG `105`, SHORT `172`, neutral `1815`;
- 2026-08: LONG `440`, SHORT `4`, neutral `1396`.

Recovery classification:

`LONG_SELECTOR_COVERAGE_PRESENT`

## Decisive interpretation

The hypothesis that frozen V69 LONG is inactive because its direction selector is globally too restrictive is rejected.

Across the all-bar historical screen, LONG was selected more often than SHORT and represented `67.218%` of directional selections. Opportunity availability is strongly regime-dependent instead: LONG selection was abundant in several Sep-Feb months, collapsed in Mar-Jun 2026, and recovered sharply in Aug.

The earlier live `83/83 short_edge` sample therefore describes a bearish observed window, not a globally SHORT-only selector.

Do not loosen LONG direction thresholds merely to increase turnover. Do not enable historical SHORT from the bearish live sample.

## Methodological correction

`3,576` LONG-selected M15 bars are not `3,576` independent tradable setups.

Adjacent closed bars can remain LONG-selected while one pending setup/state machine is active. The actual downstream funnel additionally applies archetype construction, structural-stop validation, pending micro-entry logic, zone touch/penetration, reversal confirmation, V69 separation/retest and preflight.

Therefore `24 / 3,576` is not a valid setup conversion rate.

The next denominator must be actual `PENDING_ARM` cycles, with selector bars/streaks retained only as context.

## Code work this turn

A new read-only downstream LONG funnel recovery was added to `agent/v69-one-shot-prospective-demo`.

Implementation checkpoints:

- `a1d05e88e83f01adf346ce088a4dfa18b822fe7c` — cycle-based funnel analyzer/runtime/tests;
- `3685ec2cce1029cc5b535bfa7b9b69954e35f4aa` — accepted-evidence fail-closed guard and regression test.

Files:

- `scripts/analyze_v69_downstream_long_funnel.py`;
- `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py`;
- `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_downstream_long_funnel.py`;
- extended `.github/workflows/v69_upstream_diag_quality.yml`.

The analyzer reports:

- LONG selector rows and contiguous 15-minute LONG streaks as context only;
- initial LONG ENTRY_EVAL reject reasons;
- number of actual `PENDING_ARM` cycles;
- per-cycle reach through `MICRO_ENTRY_ARM`, zone touch, penetration, reversal confirmation, V69 separation, V69 retest-ready, entry-ready and `REFINED_ENTRY`;
- terminal/invalidation reasons;
- largest consecutive-stage loss;
- actual V69 deal identity and month-by-month funnel.

Safety/evidence guards:

- exact branch/HEAD contract;
- clean worktree required;
- no MT5 or MetaEditor launch;
- zero order path;
- accepted development evidence must reproduce `24 trades / 10W / 14L / +$7.14` within cash tolerance;
- ZIP fallback, if needed, must match accepted SHA256 `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`;
- strategy changes `0`;
- independent edge evidence `0`;
- counterfactual profitability of rejected cycles `not proven`.

## CI

The initial downstream implementation checkpoint `a1d05e88e83f01adf346ce088a4dfa18b822fe7c` passed all five workflows.

The identity-guard checkpoint `3685ec2cce1029cc5b535bfa7b9b69954e35f4aa` passed the dedicated `v69-upstream-diag-quality` tests and the relevant legacy workflows; final handover commits follow it. Resolve the final branch HEAD and require all five exact-head workflows `completed/success` before operator execution.

## Safety and strategy status

- frozen V69 semantics unchanged;
- DEMO execution transport PASS;
- live `83/83` directional evaluations were SHORT-selected and correctly isolated out by LONG-only runtime;
- all-bar historical selector coverage contains substantial LONG opportunity;
- downstream diagnostic is read-only;
- SHORT remains disabled/rejected;
- REAL authorization false;
- no automatic REAL promotion.

## Next operator action

After final handover HEAD is exact-CI-green:

1. leave MT5 running;
2. fast-forward only to the exact final branch HEAD;
3. export `V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD` to that exact SHA;
4. run `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY_GIT_BASH.sh` once;
5. return output from `V69_DOWNSTREAM_ACCEPTED_DEVELOPMENT_IDENTITY=` / `V69_DOWNSTREAM_SELECTOR_LONG_ROWS_DEVELOPMENT=` through `V69_DOWNSTREAM_FUNNEL_RECOVERY=PASS`, or the exact FATAL;
6. if evidence identity fails, do not override it and do not regenerate MT5 evidence blindly;
7. do not rerun the execution probe, selector coverage, or upstream no-trade diagnostic.

After the funnel result, localize the dominant gate. Do not change that gate until rejected-cycle counterfactual price outcomes show whether it is removing edge or mostly removing noise.
