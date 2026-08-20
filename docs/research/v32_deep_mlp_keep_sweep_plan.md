# V32 — DeepMLP keep-rate exact-MT5 sweep

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: Strategy Tester / virtual-book research only. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Why V32 exists

V31.1 is the first accepted exact-MT5 comparison of the model gate on a continuous USD40 research account.

Primary candidate `adaptive_ewma_hl8_thr0`:

- baseline: USD40 -> USD62.3573, 7.6807% geometric/month, max MTM DD 10.8159%, 222 trades, AvgR 0.2401R, ledger PF 1.5579;
- DeepMLP 50%-score gate: USD40 -> USD60.4393, 7.1215% geometric/month, max MTM DD 7.3551%, 146 trades, AvgR 0.3329R, PF 1.8037.

Therefore the DeepMLP contains useful quality/risk information, but the median-score binary gate removes too much profitable breadth. CatBoost, ExtraTrees, LinearSVM and simple voting are materially weaker as primary binary gates and are not carried forward into this threshold-bracketing experiment.

V32 asks one bounded question:

> Can the same frozen causal DeepMLP recover baseline-or-better return at a broader keep rate while preserving some of its DD / AvgR / turnover advantage?

It does **not** add a larger network, more families, more risk, or a new objective.

## Development-only status

V32 reuses the already inspected 2026-02 through 2026-07 exact-MT5 period. It is a **development sweep**, not fresh confirmation and not promotion evidence.

The purpose is to select/falsify a bounded threshold region. Any selected threshold must later be frozen before a genuinely fresh chronological holdout.

## Model and causal protocol

The network is the same V31.1 tabular MLP:

- hidden layers: 64 -> 32 -> 16;
- target: realized `r_multiple`;
- inverse `(entry_time,direction)` opportunity-multiplicity weighting;
- six-month warm-up;
- previous month = score-calibration month;
- model fit only on trades whose `exit_time` is before calibration-month start;
- threshold derived only from the frozen-model calibration score distribution;
- absolute threshold applied to the following month;
- no test-month quantile peeking;
- current-bar inference state uses latest `feature_available_time <= actual M15 bar start T`.

## Bounded keep-rate ladder

One nested tape stores five thresholds:

- bit 0: keep 50% of calibration-score distribution;
- bit 1: keep 60%;
- bit 2: keep 70%;
- bit 3: keep 80%;
- bit 4: keep 90%.

Because the thresholds are nested, broader modes differ only in how much of the same DeepMLP score distribution they retain.

Pinned Linux reference tape:

`8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`

Expected: 23,616 data rows plus header.

## Exact MT5 contract

All six modes use:

- `XAUUSDm`, M15;
- `2026-02-01 -> 2026-08-01`;
- Strategy Tester Deposit = USD40;
- continuous book = `usd40_r1p0_cent_continuous`;
- 1.00% research risk ceiling per trade;
- leverage assumption 1:200;
- identical adaptive-state checkpoint after 2026-01 restored before every mode;
- month-end liquidation retained;
- no native/external broker orders.

Modes:

1. baseline
2. `mlp_keep50`
3. `mlp_keep60`
4. `mlp_keep70`
5. `mlp_keep80`
6. `mlp_keep90`

V32 deterministic tester-only source SHA-256:

`ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`

Accepted starting state SHA-256:

`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`

## Primary decision metrics

Primary same-candidate comparison remains:

`adaptive_ewma_hl8_thr0`

Final values come from MT5 `monthly_summary.csv` and `trades.csv`, not Python-reconstructed PnL:

- ending USD;
- total and geometric monthly return;
- months >=15%;
- positive months;
- worst month;
- full-period max MTM DD;
- trade count;
- AvgR;
- ledger profit factor from `total_pnl`;
- volume/margin rejects;
- gross turnover / starting USD40;
- return / max DD.

## Development selection rule

Do not select by return alone.

A useful threshold region should, at minimum:

1. recover a material share of baseline ending capital / geometric return;
2. retain some DeepMLP quality advantage in AvgR or PF;
3. avoid DD materially worse than baseline;
4. not increase turnover beyond baseline merely to manufacture return.

If no broader threshold improves the return/quality tradeoff, reject binary DeepMLP entry gating as the next architecture.

## What follows V32

- If one bounded threshold clearly dominates the V31.1 median gate and is competitive with baseline, freeze it before a fresh chronological holdout; do not tune again on February-July.
- If V32 fails, move the neural signal away from all-or-nothing entry rejection toward causal risk/exit control and complementary-opportunity allocation.
- Historical profit-protection work already showed exit-only cannot deliver the 15% monthly objective by itself.
- The 15% monthly objective is aspirational evidence, not a guarantee. Risk must not be raised above 1.00% merely to force the number.
