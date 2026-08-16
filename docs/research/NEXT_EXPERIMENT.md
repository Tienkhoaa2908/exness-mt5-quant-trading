# NEXT EXPERIMENT — Opportunity Fusion Lab V1

## Why

Profit Protection Lab V1 confirmed the open-profit giveback problem and found a materially better exit: `ema_h1_lock_50pct_peak_after_1r_tp4r`. On the USD40 / 1.00% book it raised median monthly return from about +3.54% for fixed EMA 2R to +6.32%, reduced observed max MTM DD from about 10.96% to 9.02%, and eliminated the measured `MFE>=1R -> realized<=0R` cases.

That improvement still falls well short of the 15–20% monthly aspiration. The next bottleneck is opportunity-adjusted alpha, not higher leverage or larger stop-risk.

## Goal

Increase the number of independent positive-evidence signal opportunities per month while:

- keeping stop-risk <=1.00%;
- keeping at most one position per candidate on XAUUSD;
- freezing the best profit-protection exit;
- avoiding a new unrestricted parameter grid.

## Candidate catalog

Standalone:

1. `ema_h1_peaklock`
2. `rsi2_regime_peaklock`
3. `rsi2_h1_peaklock`
4. `macd_fast_regime_peaklock`
5. `macd_fast_h1_peaklock`
6. `trend_h1_peaklock`

Fusion:

7. `fusion_ema_rsi2h1_peaklock`
8. `fusion_ema_macdh1_peaklock`
9. `fusion_ema_rsi2h1_macdh1_peaklock`
10. `fusion_all_h1_peaklock`

All candidates use initial stop = 2 ATR, TP = 4R, and after MFE reaches +1R the stop protects 50% of peak R.

## Signal sources

- EMA H1: EMA10 pullback/reclaim with EMA10 > EMA50 > EMA200 (reverse for short), confirmed by closed-H1 trend alignment.
- RSI2 regime: close above EMA200 and RSI(2) <= 10 for long; reverse below EMA200 / RSI(2) >= 90 for short.
- RSI2 H1: RSI2 regime plus closed-H1 alignment.
- MACD fast regime: MACD(8,21,5) signal-line cross in the direction of EMA200 regime.
- MACD H1: MACD regime plus closed-H1 alignment.
- Trend H1: 20-bar breakout with EMA20/50/300 alignment plus closed-H1 alignment.

Same-bar same-direction source signals become one fused entry with a source mask. Opposite same-bar sources are conflict-rejected. A fusion candidate never stacks simultaneous same-symbol positions.

## Books / monthly evidence

Each candidate runs four books:

- normalized USD10k @0.50%;
- USD40 @0.50%;
- USD40 @0.75%;
- USD40 @1.00%.

Run 18 independent calendar months from 2025-02 through 2026-07 using three six-month generated-tick MT5 chunks. USD40 min/step is modeled at 0.0001 standard-lot equivalent and margin is stressed at 1:200. No upward volume rounding.

## Decision metrics

Primary:

- median / mean USD40 monthly return;
- positive-month ratio;
- >=10%, >=15%, >=20% hit rates;
- worst / best month;
- max MTM DD;
- PF / AvgR / win rate;
- trade count, source mix, conflict rejects and volume rejects;
- 2025 vs 2026 stability.

Promotion requires a material improvement over `ema_h1_peaklock`, not one exceptional month. Virtual candidates are never deployable directly; any winner must return to native MT5 validation.

## Reliability

Run `scripts/run_opportunity_fusion_lab_v1.cmd`.

The runner uses heartbeat, bounded watchdog, broker-unavailable detection, one retry, LocalAppData checkpoint reuse and Common Files recovery. The new MQL source has local static QA but must be compiled/run on Windows before runtime PASS can be claimed.

REAL-MONEY LIVE TRADING remains forbidden.