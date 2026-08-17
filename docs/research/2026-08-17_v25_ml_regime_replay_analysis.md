# 2026-08-17 — V25 ML Regime Replay Lab V1 analysis

## Runtime evidence

Uploaded output ZIP SHA-256: `baff90eccfaac70abaa15b30d6132c535160e2b8ab96b65fd290cba968754078`.

- bundle schema: `mt5_quant_ml_regime_replay_lab_v1_bundle`;
- internal SHA-256 manifest: 21/21 PASS;
- MetaEditor: 0 errors / 0 warnings;
- 2 chunks, 12 monthly resets, Aug-2025 → Jul-2026;
- 12 candidates × 4 books = 576 monthly rows;
- 17,635 executed virtual trades across all books/candidates;
- tester-only; native/external broker orders = 0;
- frozen OOF range-score SHA-256 `5d8a6cc45074833a60d7e82b6a56f7ae72a9f4e0153b623cc439756751b16c91`;
- fold manifest SHA-256 `ed26b87484e1c4782614c64294520bc7fb3e6728c10f08fa77c8fe2d097739a7`.

## USD40 @ 1% results

`ema_h1_base` remains the highest median-return candidate on this 12-month horizon:
- median +5.8576%/month;
- mean +4.7476%;
- positive 8/12;
- max MTM DD 8.7792%;
- mean AvgR ~0.1594;
- median turnover ~138.10x initial capital/month.

The strongest ML efficiency candidate is `ml_switch_ema_bos8_p75`:
- median +5.6288%;
- mean +4.9954%;
- positive 10/12;
- max MTM DD 7.3121%;
- mean AvgR ~0.1942;
- median turnover ~112.99x.

Relative to EMA base, `ml_switch_ema_bos8_p75`:
- mean return +0.248 percentage points/month;
- positive months +2;
- max DD ~16.7% lower;
- AvgR ~21.8% higher;
- turnover ~18.2% lower;
- median return ~0.229 percentage points/month lower.

Paired monthly return difference is not statistically decisive: 7 wins / 5 losses versus EMA base; paired bootstrap 95% CI for mean difference includes zero and two-sided Wilcoxon p is ~0.91.

Relative to the non-ML `router_ema_bos8`, `ml_switch_ema_bos8_p75` raises median return ~0.38 points, lowers max DD ~6.1%, raises AvgR ~11.9% and lowers turnover ~28.8%, but mean return is ~0.84 points lower. Therefore ML has not proven a robust return uplift over the router control.

`ml_ema_skip20_low75` is the clearest abstention/quality result. Relative to `ema_h1_skip20`:
- median +0.13 points;
- mean -0.20 points;
- max DD ~21.8% lower;
- AvgR ~22.5% higher;
- turnover ~29.8% lower.

Exact-entry matching shows the ML low-75 gate excluded about 100 USD40@1% EMA-skip20 trades with average R only ~+0.021R, while the 294 common trades averaged ~+0.245R. This is evidence that the OOF range score carries useful trade-quality information even though fewer opportunities prevent a clear return increase.

## Regime interpretation

The p67 threshold is too loose for switching. Multi-family p67 routers generally add churn and/or low-quality breakout exposure. `ml_switch_ema_multi_p67` is rejected: mean ~+2.81%, worst month ~-10.86%, max DD ~16.0%, turnover ~178x.

A post-hoc diagnostic on the frozen OOF scores shows a more specific pattern:
- EMA-skip20 trades with `range_pct >= 0.75` are near-flat on average;
- the control subset with `range_pct >= 0.80` is negative on average;
- `range_pct` 0.85–0.95 contains the clearest EMA deterioration;
- BOS/Trend/Donchian directional continuation becomes stronger mainly in the extreme-high predicted-range region, not across the whole >=0.67 or >=0.75 region.

A bivariate diagnostic is stronger: EMA-skip20 trades with `range_pct >= 0.90` and `vol_pct >= 0.75` are a small, materially negative subset in this sample. BOS4 observations in the same extreme regime are positive, but sample size is small. These thresholds are **discovery only** because they were inspected after V25 results and must not be described as confirmed alpha.

## Decision

1. Do not let ML predict Buy/Sell directly; directional models remain weak.
2. Keep ML as a regime/abstention layer.
3. `ml_switch_ema_bos8_p75` is a provisional efficiency finalist, not a return winner.
4. `ml_ema_skip20_low75` validates that OOF range score can remove low-expectancy EMA opportunities.
5. Do not promote any p67 multi-family router.
6. Any next same-sample threshold refinement is screening only and must be followed by untouched forward validation.
7. REAL-MONEY LIVE TRADING remains forbidden; stop-risk ceiling remains 1.00%/trade.

## Forward gate

The next confirmation-quality evidence should come from a period not used to select V25 routing thresholds. Current Aug-2026 data is the earliest candidate forward period. If another replay screen is run first, label it explicitly as post-V25 discovery and freeze the resulting policy before evaluating subsequent forward data.
