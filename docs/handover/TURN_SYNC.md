# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 02:55 (+07)

## User input

Operator ran the aggregate read-only upstream diagnostic at exact checkpoint:

`9ca2ac66b4c82f5b2f5c51184259d7147486c5a9`

MT5 remained running. No MetaEditor was required, no orders were sent and REAL authorization remained false.

## Exact operator evidence

Pending/event funnel remained empty:

- analyzed sources `8`;
- total event rows `0`;
- `PENDING_ARM=0`;
- all reclaim/separation/retest/entry-ready stages `0`;
- natural closed V69 deals `0`.

Aggregate pre-pending evidence:

- raw ENTRY_EVAL rows `83`;
- unique rows `83`;
- duplicates removed `0`;
- `decision_reason=short_edge`: `83/83`;
- `reject_reason=direction_isolated_out`: `83/83`;
- selected direction `-1`: `83/83`;
- `SHORT_HTF_REGIME`: `83/83`;
- H1 trend `-1`: `83/83`;
- H4 trend `-1`: `83/83`;
- `SHORT_SCORE_HIGHER`: `83/83`;
- trigger state: `SHORT_TRIGGER_ONLY=59`, `BOTH_TRIGGERS=24`;
- long score min/mean/max `-11 / -7.6265 / -1`;
- short score min/mean/max `8 / 10.2892 / 15`;
- long-minus-short min/mean/max `-25 / -17.9157 / -9`;
- aggregate context `ALL_UNIQUE_EVALS_SHORT_EDGE_IN_SHORT_HTF_REGIME`;
- diagnostic PASS and launcher PASS.

Component telemetry still contained some local bullish cues, especially `location_dir=+1` on `65/83` and bullish liquidity sweep on `19/83`, but broad directional evidence remained strongly bearish: H1/H4 were both `-1` on every row, MACD was `-1` on `79/83`, DI was `-1` on `76/83`, and short score beat long score by at least 9 on every row.

## Locked interpretation

The observed no-trade path is no longer ambiguous for recorded directional evaluations.

Frozen V69 LONG-only correctly abstained because the unchanged selector selected SHORT on all 83 unique evaluations. V69 then rejected the opposite direction before `PENDING_ARM` by design.

Therefore:

- broker execution is not the blocker;
- reclaim confirmation is not the blocker for these rows;
- separation/retest is not the blocker for these rows;
- no preserved LONG selector candidate exists among the 83 recorded evaluations;
- do not loosen LONG just to manufacture trades;
- do not enable the rejected historical SHORT path.

## Remaining observability gap

The 83 rows are **not all closed M15 bars**.

Code review of inherited V62/V69 `EvaluateBar` proves it returns before `V64_ENTRY_EVAL.csv` when feature building fails or selector returns `d==0`. Therefore the candidate telemetry cannot estimate calendar opportunity coverage.

The next question is all-bar selector coverage: among every closed M15 bar, what fraction is feature-ready, LONG-selected, SHORT-selected or neutral, and how does that vary by month/regime?

## Code work this turn

A new read-only selector-coverage recovery path was added on `agent/v69-one-shot-prospective-demo`:

- `scripts/analyze_v69_selector_coverage_recovery.py`;
- `runtime/v69_selector_coverage_recovery/RUN_V69_SELECTOR_COVERAGE_RECOVERY.py`;
- `runtime/v69_selector_coverage_recovery/RUN_V69_SELECTOR_COVERAGE_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_selector_coverage_recovery.py`;
- extended `.github/workflows/v69_upstream_diag_quality.yml`.

The recovery tool does **not** run MT5 tester or MetaEditor. It reuses existing local V64 all-bar screen evidence if available.

Before reuse it generates frozen V69 and compares exact normalized directional functions and score thresholds against the V64 all-bar screen source. Any mismatch is fatal. It also checks the actual local V64 screen source again at operator runtime rather than trusting CI alone.

If identity passes, it reports:

- unique M15 rows and date span;
- feature-ready vs feature-not-ready bars;
- selected LONG/SHORT/neutral counts and percentages;
- LONG/SHORT share among directional selections;
- decision reasons;
- HTF regime counts;
- trigger-state counts;
- score distributions;
- month-by-month coverage.

This output is explicitly `DEVELOPMENT_COVERAGE_ONLY=1` and `INDEPENDENT_EDGE_EVIDENCE=0`.

## CI

Code checkpoint `2666bc8520afd850dc6fd32f29c101e2bd01cbe3` passed the new `v69-upstream-diag-quality` workflow.

A further regression checkpoint `c39d18b77f543a3d83cfefe0601beb931cf8e83f` generates both repository builders in CI and proves the V64 all-bar screen directional core + score thresholds match frozen V69 exactly. `v69-upstream-diag-quality` passed on that checkpoint.

After this handover sync, resolve the final branch HEAD and require all five exact-head workflows green before giving the operator the recovery launcher.

## Safety and strategy status

- frozen V69 semantics unchanged;
- DEMO execution transport PASS;
- current observed directional evaluations all SHORT-selected;
- LONG-only abstention is working as designed for those evaluations;
- SHORT remains disabled/rejected;
- no automatic REAL promotion;
- REAL authorization false;
- selector-coverage recovery is read-only and sends no orders.

## Next operator action

After the documentation-sync HEAD is exact-CI-green:

1. leave MT5 running;
2. fast-forward only to the exact final HEAD;
3. export `V69_SELECTOR_COVERAGE_EXPECTED_HEAD` to that SHA;
4. run `runtime/v69_selector_coverage_recovery/RUN_V69_SELECTOR_COVERAGE_RECOVERY_GIT_BASH.sh` once;
5. return output from `V69_SELECTOR_DIRECTIONAL_CORE_IDENTITY=` through `V69_SELECTOR_COVERAGE_RECOVERY=PASS`, or the exact FATAL message;
6. if V64 evidence is absent, do not stop MT5 to regenerate it;
7. if identity mismatches, do not override the fail-closed check;
8. do not rerun the upstream diagnostic or execution probe.
