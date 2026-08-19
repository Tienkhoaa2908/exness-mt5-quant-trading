# V30 18-month feature-lake acceptance + first causal ML benchmark

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: tester-only research; real-money live trading forbidden.

## Runtime acceptance

Uploaded Git Bash result ZIP SHA-256:
`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

The final Git Bash run compiled `MlDlFeatureLakeV1.mq5` with `0 errors, 0 warnings`, then completed and collected both remaining chunks:

- Chunk 2: `2025-08-01 -> 2026-02-01`, run id `ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265`.
- Chunk 3: `2026-02-01 -> 2026-08-01`, run id `ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093`.

Both manifests report tester-only, zero native/external broker orders, 12 candidates, 4 books, 6 months written, V30 bar-feature schema, and no future labels in the EA.

## Canonical 18-month lake QA

Each raw chunk contained exactly one pre-roll row before its requested interval. Canonical trimming used half-open intervals:

- `[2025-02-01, 2025-08-01)`
- `[2025-08-01, 2026-02-01)`
- `[2026-02-01, 2026-08-01)`

After trim/stitch:

- 35,344 M15 feature rows.
- 136 raw V30 feature columns before offline helper columns.
- Coverage: 2025-02 through 2026-07 inclusive (18 months).
- 35,344 unique timestamps; 0 duplicates.
- 0 NaN; 0 Inf.
- All three raw feature schemas are identical.
- Summary rows: 864 total = 18 months x 12 candidates x 4 books.
- Trade ledger rows: 28,128 total across all books; 7,483 in `norm10k_r0p5_continuous`.

Per candidate/book/month, summary-versus-ledger checks produced:

- 0 trade-count mismatches.
- 0 win/loss mismatches.
- Maximum absolute net-PnL discrepancy <= 7e-6 (CSV rounding).
- Maximum absolute AvgR discrepancy <= 6e-6 (CSV rounding).

Expected non-informative/constant fields over the 18-month lake:

- `real_volume = 0`.
- readiness flags are always 1.
- `bb_rsi_dir = 0` throughout.

`spread_bad` is nonzero on only one canonical bar. These are not treated as corruption, but constant fields must be excluded from model training.

## Adaptive-state continuity

State checkpoints are internally continuous.

Chunk 1 -> Chunk 2 observation counts:

- EMA: 181 -> 393 (+212)
- MACD: 79 -> 216 (+137)
- BOS: 69 -> 184 (+115)
- Trend: 108 -> 279 (+171)
- Slow momentum: 210 -> 416 (+206)

Chunk 2 -> Chunk 3:

- EMA: 393 -> 590 (+197)
- MACD: 216 -> 251 (+35)
- BOS: 184 -> 221 (+37)
- Trend: 279 -> 360 (+81)
- Slow momentum: 416 -> 612 (+196)

Replaying the control-trade `r_multiple` ledger through the documented EWMA equations reproduces the checkpoint counts exactly. EWMA values differ by at most about 1.9e-6 because the trade CSV stores rounded R while the EA updates state from higher-precision internal values.

## 18-month strategy evidence (norm10k, monthly-reset research book)

Top aggregate candidates remain:

- `adaptive_ewma_hl8_thr0`: summed monthly return 83.971%, 849 trades, 14/18 positive months, worst month -1.7087%, maximum monthly MTM DD 5.9425%.
- `router_ema_bos8`: summed monthly return 61.489%, 689 trades, 15/18 positive months, worst month -4.2894%, maximum monthly MTM DD 5.8394%.
- `ema_h1_skip20`: summed monthly return 52.1647%, 590 trades, 14/18 positive months.

These figures are research-book evidence, not a promotion decision. Adaptive-router uplift remains confounded by opportunity breadth and turnover.

## Critical offline leakage finding

A naive trade-entry join using `bar_features.time <= entry_time` is invalid for this lake.

`bar_features.time` is the open timestamp of `r[1]`, the just-closed M15 bar, but that row is only written on the first tick of the next bar. Therefore a row stamped `10:45` is not available until approximately `11:00`. Joining an entry at `10:45` or `10:46` to the `10:45` row leaks post-entry bar information.

The initial same-timestamp ML experiment was therefore invalidated and must not be cited.

Correct offline availability is:

`feature_available_time = bar_features.time + 15 minutes`

Trade entries are joined to the latest feature row whose `feature_available_time <= entry_time`.

With this correction, all 7,483 norm-book trades have a causal feature row. For 7,457 trades, the underlying closed bar is exactly 15 minutes old at entry; the longer gaps are session/weekend gaps.

## First corrected causal expected-R benchmark

Dataset:

- norm10k book only: 7,483 trades / 18 months.
- six-month warm-up; OOS months 2025-08 through 2026-07.
- 5,066 pooled OOS trades.
- training for each month includes only trades whose `exit_time` is strictly before the test month starts.
- features: causal V30 bar state plus causal entry-state telemetry; constant fields removed.
- models: Ridge expected-R regression and Logistic win/loss classification.
- thresholds are calibrated from prior training scores only, then applied to the next month. No test-month quantile peeking.

Corrected results:

### Win/loss classification

Candidate-blind logistic:

- mean monthly AUC: 0.5334.
- causal selected AvgR: 0.1888R versus 0.1890R baseline.
- within-candidate threshold AvgR: 0.1805R.
- paired 12-month bootstrap uplift CI crosses zero: approximately [-0.0668R, +0.0804R].

Candidate-aware logistic is similar (mean monthly AUC 0.5418) and does not establish economic uplift.

Conclusion: classification is not useful enough for promotion.

### Expected-R regression

Candidate-blind Ridge:

- mean monthly Spearman: 0.0418 (weak global rank correlation).
- baseline pooled OOS AvgR: 0.1890R on 5,066 trades.
- causal global-threshold selection: 0.2386R on 1,911 trades.
- causal within-candidate threshold selection: 0.2460R on 1,943 trades.
- selected positive months: 9/12.
- worst selected month: -0.2319R average.
- paired month mean uplift versus baseline: +0.0980R.
- 20k paired-month bootstrap interval: approximately [+0.0179R, +0.2052R].

Candidate-aware Ridge is not materially better:

- mean monthly Spearman: 0.0399.
- within-candidate selected AvgR: 0.2375R on 1,940 trades.
- paired-month uplift interval: approximately [+0.0161R, +0.2113R].

Interpretation: the first economically interesting ML signal is expected-R filtering, not win/loss probability. The small difference between candidate-blind and candidate-aware variants suggests the result is not explained only by candidate base rates. However, the evidence is still too fragile for promotion: only 12 OOS months, weak rank correlation, one test month with zero selections under the global regression threshold, and the worst selected month is not improved.

## Feature-stability clue

Standardized Ridge coefficients are dominated by adaptive-state slope/level combinations and normalized market-state features. Several signs are stable across all 12 expanding folds, including components of EMA/BOS/MACD EWMA state, `dist_ema10_atr`, M5 range/volatility, and tick-range state. Because the raw EWMA horizons are highly collinear, coefficient signs must not be interpreted individually as causal effects.

The next target-engineering step should explicitly construct low-dimensional state-change features such as fast-minus-slow EWMA, EWMA slope/severity, family-relative score, volatility/range regime, and signal-family interaction terms, then rerun the same strict OOS economic gate.

## Decision

- V30 18-month feature lake: ACCEPTED for offline research.
- Runtime automation: ACCEPTED for this data acquisition task; no further MT5 run is required for the current 18-month study.
- Win/loss classifier: REJECT for promotion.
- Linear expected-R filter: PROMISING RESEARCH LEAD, not promotion-ready.
- Any ML/DL experiment that joins by raw `bar_features.time` without the +15-minute availability shift: INVALID.
- Next: repair the offline label/join utilities to encode feature availability explicitly, add causal target/state engineering, then run tabular nonlinear and true-sequence GRU/TCN/PatchTransformer walk-forward tests on the corrected lake.
