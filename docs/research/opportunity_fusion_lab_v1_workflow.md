# Opportunity Fusion Lab V1 workflow

## Purpose

Test whether the USD40 monthly return profile can improve by increasing independent high-quality signal opportunity while keeping the strongest profit-protection exit fixed and maintaining at most one position per candidate on XAUUSD.

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

All candidates use initial stop = 2 ATR, TP = 4R and 50%-of-peak profit lock after MFE reaches +1R.

## Signal definitions

- EMA H1: EMA10 pullback/reclaim with EMA10 > EMA50 > EMA200 (reverse for short), confirmed by closed H1 close/EMA50/EMA200 alignment.
- RSI2 regime: close above EMA200 and RSI(2) <= 10 for long; reverse below EMA200 / RSI(2) >= 90 for short.
- RSI2 H1: RSI2 regime plus the closed-H1 alignment filter.
- MACD fast regime: MACD(8,21,5) signal-line cross in the direction of EMA200 regime.
- MACD H1: MACD regime plus closed-H1 alignment.
- Trend H1: 20-bar breakout with EMA20/50/300 alignment plus closed-H1 alignment.

Fusion uses the first valid allowed signal while flat. Same-bar same-direction signals are treated as one entry with their source mask recorded. Opposite same-bar signals are a conflict and are skipped.

## Risk / books

Four independent books per candidate:

- normalized USD10k @ 0.50%;
- USD40 cent-equivalent @ 0.50%;
- USD40 cent-equivalent @ 0.75%;
- USD40 cent-equivalent @ 1.00%.

USD40 volume min/step is modeled as 0.0001 standard-lot equivalent. Margin stress uses 1:200. No upward volume rounding.

## Runtime

Three six-month MT5 generated-tick runs. EA performs monthly resets internally. Runner inherits heartbeat, bounded watchdog, one retry, broker-unavailable detection, checkpoint reuse and Common Files recovery.

## Decision metrics

Primary:

- median USD40 monthly return at each risk book;
- positive-month ratio;
- >=10%, >=15%, >=20% hit rates;
- worst/best month;
- max MTM DD;
- median PF and AvgR;
- source mix, conflicts, trade count and volume rejects;
- 2025 vs 2026 stability.

Promotion requires improvement over `ema_h1_peaklock`, not merely one exceptional month. Virtual candidates are never deployed directly; native MT5 validation is mandatory.