# ADR-038 — Causal feature availability and opportunity-weighted ML gates

## Status

Accepted for research — 2026-08-20.

## Context

V30 produced an accepted 18-month M15 bar feature lake and a trade ledger for the frozen V29/V30 virtual strategy catalog. Two research-specific hazards were discovered during offline ML validation.

First, the bar-feature timestamp is not the feature-availability timestamp. The EA exports `r[1]`, the just-closed M15 bar, and stores that bar's open time. A row stamped 10:45 is only known when the 10:45-11:00 bar has closed. Joining by raw timestamp can therefore leak the entry bar.

Second, the virtual catalog contains many candidate variants that enter at the same `(entry_time, direction)`. In the norm book, 7,483 candidate-trades collapse to only 1,972 unique opportunities over 18 months; approximately 79% of opportunity groups contain multiple candidate variants. Treating every candidate-trade as an independent training/economic observation materially overweights repeated opportunities.

The first strict nonlinear tournament initially produced attractive ExtraTrees/HistGradientBoosting expected-R filtering results. After inverse opportunity-multiplicity weighting, the uplift weakened materially. When data were collapsed to unique opportunity groups, common-state ExtraTrees/HistGradientBoosting models no longer cleared the paired-month robustness gate. Sequence GRU/TCN/PatchTransformer models also failed to beat the tabular controls.

## Decision

### 1. Feature availability is explicit

For V30 M15 lake rows:

`feature_available_time = bar_features.time + 15 minutes`

A trade entry may only use a feature row when:

`feature_available_time <= entry_time`

Raw `bar_features.time <= entry_time` joins are invalid for ML evidence.

### 2. Future labels preserve missing horizons

Offline labels are valid only when the entire requested future horizon exists. Incomplete tail horizons remain missing. A missing future return must never be converted implicitly to a negative/zero class.

### 3. Monthly ML threshold calibration is causal

For each OOS test month:

- the immediately previous month is the score-calibration month;
- model fitting uses only trades completed before the calibration month starts;
- the frozen model scores the calibration month;
- the threshold is computed from calibration scores only;
- the absolute threshold is then applied to the next test month;
- no test-month percentile/quantile peeking;
- no random K-fold.

### 4. Opportunity duplication must be audited

Every trade-level ML tournament over a multi-candidate catalog must report unique `(entry_time, direction)` groups and their multiplicity distribution.

Unweighted candidate-trade results are exploratory only when repeated opportunity groups exist.

At least one of the following controls is mandatory before a promotion claim:

- inverse group-multiplicity sample weights so each underlying opportunity contributes approximately unit total training weight; or
- a unique-opportunity model where repeated candidate variants are collapsed before fitting.

### 5. Universal model gates require unique-opportunity evidence

A model claimed to predict common market opportunity quality must survive the unique-opportunity control. If only candidate/trade-context models survive, the evidence must be described as family/candidate-specific rather than universal market-state edge.

### 6. Economic metrics take precedence over AUC

Promotion gates focus on causal OOS economic utility, including:

- selected AvgR versus baseline;
- total sumR retention;
- actual opportunity/trade coverage;
- positive/worst month behavior;
- paired-month uplift bootstrap;
- turnover/opportunity breadth;
- drawdown/tail-loss diagnostics where valid.

Classification AUC by itself is not promotion evidence.

### 7. Current model decision

- Win/loss/tail classifiers: rejected for promotion.
- GRU/TCN/PatchTransformer: no escalation on the current 18-month lake.
- Unweighted ExtraTrees catalog filter: not promotion evidence because duplication materially amplifies results.
- Inverse-opportunity-weighted expected-R filtering: promising but weaker; only the approximately 50%-keep target remains statistically positive in the current 12-month OOS sample.
- Unique-opportunity common-state models: do not clear the robustness gate.

Therefore no universal ML gate is promoted.

### 8. Next research gate is family-specific

The next offline experiment will test family-specific expected-R filtering under inverse-opportunity weighting and the same frozen monthly calibration protocol. EMA/router/slow-momentum families are positive leads; BOS/FVG is a negative/control family because the current weighted filter degrades it.

Only if the family-specific filter survives will a new Strategy Tester/tick-level re-simulation be justified.

## Consequences

- Existing experiments that used raw feature timestamps without the +15-minute availability shift are invalidated.
- Future model code must expose the availability timestamp explicitly rather than relying on naming convention.
- Duplicate-opportunity counts become a mandatory QA field for catalog-based ML.
- More complex model capacity cannot bypass data-independence and economic robustness gates.
- No additional MT5 run is required for the current offline gate.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. This ADR concerns offline research and Strategy Tester validation only. It does not authorize native broker orders, removal of tester guards, Martingale/grid/doubling, or risk above the 1.00% research ceiling.
