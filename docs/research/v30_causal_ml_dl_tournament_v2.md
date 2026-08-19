# V30 causal ML/DL tournament V2 — strict calibration, duplication audit, sequence controls

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: offline/tester-only research. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Purpose

This checkpoint extends the accepted V30 18-month feature lake after the causal availability correction documented in `v30_18m_feature_lake_acceptance_and_first_ml.md`.

The objective is not to maximize AUC. The gate is whether a model can causally reduce low-quality opportunities while preserving enough realized R, with chronological walk-forward validation and without test-month threshold peeking.

## Causal data contract

The V30 EA writes `r[1]`, the just-closed M15 bar, but stamps the row with that bar's open timestamp. Therefore the offline availability contract is:

`feature_available_time = bar_features.time + 15 minutes`

A trade may only use the latest feature row with `feature_available_time <= entry_time`.

The repaired offline utility also keeps incomplete future labels as missing values. In particular, tail rows with no complete future horizon must not be silently converted to class `0`.

Canonical data used by this tournament:

- 35,344 causal M15 rows across 2025-02 through 2026-07.
- 136 raw V30 fields before offline engineered/helper columns.
- 7,483 trades in `norm10k_r0p5_continuous`.
- 7,473 trades have a complete 64-bar causal sequence.
- zero causal join violations.

## Engineered state features

The V2 utility adds low-dimensional causal state-change features rather than treating highly correlated EWMA horizons as independent facts. Examples include:

- expert `fast5 - slow20`;
- `hl8 - slow20` and `fast5 - hl8`;
- observation-confidence transforms;
- confidence-weighted expert change;
- cross-expert mean/std and relative expert state;
- short/long realized-volatility ratio;
- normalized M1/M5 range and return context;
- tick path-efficiency/change fraction/spread variation;
- DI spread, signal activity/imbalance, MACD normalized by ATR;
- causal clock encodings.

Constant/non-informative lake fields are excluded from model fitting.

## Strict walk-forward protocol

There are 12 OOS test months: 2025-08 through 2026-07, after a six-month warm-up.

For each test month:

1. The immediately preceding month is the **score-calibration month**.
2. Model fitting uses only trades whose `exit_time` is strictly before the calibration month starts.
3. The calibration month's outcomes are not used to choose the score threshold.
4. The frozen model scores the calibration month; a fixed score threshold is derived from those scores.
5. That absolute threshold is applied unchanged to the next test month.
6. No random K-fold and no test-month percentile/quantile selection is allowed.

This intentionally makes the fitted model one month stale. The design is conservative but directly deployable as a causal monthly decision rule.

Baseline across the 12 OOS months:

- 5,066 candidate-trades.
- pooled AvgR: 0.189049R.
- pooled sumR: 957.72205R.

## Tabular expected-R tournament

### Engineered-state tree models

At the original approximately-40%-keep calibration target, the strongest unweighted catalog-trade models were:

| Model | Candidate identity | Actual coverage | Selected AvgR | SumR retention | Mean monthly uplift | 95% paired-month bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|
| ExtraTrees | yes | 43.01% | 0.2893R | 65.83% | +0.1317R | [+0.0375R, +0.2339R] |
| ExtraTrees | no | 42.81% | 0.2780R | 62.95% | +0.0773R | [+0.0105R, +0.1435R] |
| HistGradientBoosting | yes | 46.76% | 0.2714R | 67.12% | +0.1144R | [+0.0516R, +0.2179R] |
| HistGradientBoosting | no | 46.78% | 0.2623R | 64.91% | +0.1081R | [+0.0448R, +0.2126R] |

The unweighted ExtraTrees candidate-aware run also improved the worst selected monthly AvgR to approximately -0.0394R and had mean monthly Spearman around 0.0896.

### Linear, static neural, and market-only controls

- Engineered Ridge remains unstable under the stricter calibration protocol: selected AvgR is around 0.27R, but its paired-month CI crosses zero.
- Static MLP: selected AvgR 0.1970R, CI crosses zero.
- Market-only HistGradientBoosting and ExtraTrees controls do not establish robust uplift.
- Raw-expert Ridge fails materially.

The ablation is more informative than tree impurity importance: the useful tree-model signal requires engineered expert state plus market/trade context; market-only state is insufficient.

### Tail-loss classifier

A separate tail-loss classification target remains weak:

- HistGradientBoosting mean monthly AUC about 0.5336.
- ExtraTrees mean monthly AUC about 0.5477.

Expected-R filtering remains the more useful target than win/loss or tail classification.

## True-sequence DL tournament

All sequence models use a true causal 64-bar history ending at the latest bar available at entry, plus safe static entry context. No future bar is flattened into the sample.

Results:

| Model | Actual coverage | Selected AvgR | SumR retention | 95% paired-month uplift CI |
|---|---:|---:|---:|---:|
| GRU64 | 36.38% | 0.2003R | 38.55% | [-0.0779R, +0.1416R] |
| causal TCN64 | 43.56% | 0.1825R | 42.06% | [-0.2817R, +0.0823R] |
| Patch Transformer64 | 41.83% | 0.1570R | 34.74% | crosses zero |

The 18-month lake does not justify DL escalation. None of GRU, TCN, or Patch Transformer beats the stronger tabular tree controls under the same causal decision protocol.

## Feature clue — not a causal claim

ExtraTrees impurity importance averaged across the 12 folds assigns roughly:

- 55.3% to market/microstructure state;
- 33.6% to engineered/raw expert state;
- 11.0% to safe trade-entry static context;
- about 0.1% to candidate one-hot identity.

Individual recurring clues include day-of-week encoding, entry close location, slow-momentum direction, BOS/EMA relative expert state, cross-expert change dispersion, M1/M5 range/return context, and tick-range/path state.

MDI is biased and correlated features share/split importance. This is only a feature-engineering clue. The market-only ablation and the duplication tests below are stronger evidence.

## Critical duplicate-opportunity confound

The norm-book catalog is not 7,483 independent market opportunities.

Grouping by `(entry_time, direction)` gives:

- full 18 months: 7,483 candidate-trades but only 1,972 unique opportunity groups;
- mean multiplicity: 3.795 candidate variants per opportunity;
- 79.31% of groups contain more than one candidate-trade;
- maximum multiplicity: 11.

For the 12 OOS months:

- 5,066 candidate-trades;
- only 1,347 unique `(entry_time, direction)` opportunities;
- mean multiplicity: 3.761;
- 79.29% of groups are duplicated across candidates.

This is not temporal leakage, but it materially overweights repeated catalog opportunities during training and economic aggregation. Therefore unweighted candidate-trade results cannot be used as promotion evidence by themselves.

## Inverse-opportunity-weighted ExtraTrees

Training was repeated with each candidate-trade weighted by:

`1 / count(entry_time, direction)`

so each underlying opportunity contributes approximately unit total training weight.

Results with a global calibration threshold:

| Calibration keep target | Actual coverage | Selected AvgR | SumR retention | Mean monthly uplift | 95% paired-month bootstrap CI |
|---|---:|---:|---:|---:|---:|
| 40% | 49.05% | 0.2501R | 64.91% | +0.0613R | [-0.0157R, +0.1305R] |
| 50% | 58.63% | 0.2569R | 79.66% | +0.0720R | [+0.0156R, +0.1272R] |

The 40%-target result no longer clears the paired-month robustness gate. The 50%-target result survives, but is substantially weaker than the original unweighted catalog result and its worst selected month remains approximately -0.1986R.

This materially downgrades the initial ExtraTrees claim.

Candidate-level diagnostics for the weighted 50%-target run suggest heterogeneous behavior:

- `ema_h1_skip20`: roughly 55% kept, AvgR about 0.170R -> 0.294R, about 95% sumR retained.
- `router_ema_bos8`: roughly 55% kept, 0.167R -> 0.279R, about 92% sumR retained.
- `slow_mom_timebox`: roughly 59% kept, 0.182R -> 0.305R, about 99% sumR retained.
- `adaptive_ewma_hl8_thr0`: roughly 59% kept, 0.200R -> 0.247R, about 73% sumR retained.
- BOS/FVG degrades under the same filter and should not inherit a universal gate.

These are diagnostics for the next family-specific test, not promotion decisions.

## Unique-opportunity-group model

A stronger de-duplication control collapses each `(entry_time, direction)` group to one market opportunity. The target is mean R across candidate variants in that group. A training opportunity is allowed only when the maximum exit time of all member trades is before the calibration boundary.

Applying the group decision back to the catalog gives:

| Model | Keep target | Selected AvgR | SumR retention | 95% paired-month uplift CI |
|---|---:|---:|---:|---:|
| ExtraTrees | 40% | 0.2128R | 52.73% | [-0.0554R, +0.0627R] |
| ExtraTrees | 50% | 0.2153R | 61.04% | [-0.0489R, +0.0501R] |
| HistGradientBoosting | 40% | 0.2715R | 65.86% | [-0.0257R, +0.1612R] |
| HistGradientBoosting | 50% | 0.2652R | 75.85% | [-0.0387R, +0.1550R] |

All paired-month intervals cross zero.

Therefore the current lake does **not** establish a universal common market-opportunity quality model. The stronger signal appears to require family/candidate-specific entry context and is partially amplified by repeated catalog opportunities.

## Threshold robustness before weighting

For completeness, the unweighted ExtraTrees candidate-aware model was not a single-threshold accident. Global prior-month thresholds at 40% and 50% keep targets both produced strong catalog-level results:

- 40% target: actual coverage about 43.45%, selected AvgR about 0.2990R, sumR retention about 68.71%, paired-month CI approximately [+0.040R, +0.248R].
- 50% target: actual coverage about 51.66%, selected AvgR about 0.2863R, sumR retention about 78.23%, paired-month CI approximately [+0.059R, +0.194R].

However, the inverse-multiplicity and unique-opportunity controls take precedence over these attractive unweighted figures.

## Tests

Local deterministic research tests:

- 5 tests PASS.
- incomplete-horizon classification labels remain missing;
- causal trade join selects the previous closed bar rather than the current bar;
- target columns are excluded from model features;
- walk-forward calibration/test boundaries obey the frozen-model protocol;
- GRU/TCN/PatchTransformer forward shapes pass.

One PyTorch nested-tensor warning from the Transformer implementation is non-fatal.

## Decision

1. V30 18-month feature lake remains ACCEPTED for offline research.
2. The causal availability rule `bar timestamp + 15 minutes` is mandatory.
3. Win/loss/tail classification remains REJECTED for promotion.
4. Sequence DL escalation is REJECTED on current evidence; GRU/TCN/PatchTransformer do not beat tabular controls.
5. Unweighted catalog-level ExtraTrees uplift is **not promotion evidence** because opportunity duplication materially inflates the apparent robustness.
6. A weaker expected-R signal survives inverse-opportunity weighting around a 50%-keep calibration target, but unique-opportunity common-state models do not clear the robustness gate.
7. No universal ML gate should be applied across all strategy families.
8. Next offline gate: family-specific, inverse-opportunity-weighted expected-R filtering, with explicit holdout diagnostics for EMA/router/slow-momentum families and a negative-control/exclusion check for BOS/FVG.
9. Only if that family-specific gate survives should the filter be taken back to MT5 for tick-level re-simulation. No additional MT5 run is required yet.
10. REAL-MONEY LIVE TRADING remains forbidden.
