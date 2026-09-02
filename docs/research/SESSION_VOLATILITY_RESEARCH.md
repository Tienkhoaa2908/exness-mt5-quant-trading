# Session-volatility research direction

Status: development research only; not part of frozen V69 and not authorization for REAL money.

## Motivation

The next architecture should explicitly model time-of-day/session regime instead of treating all intraday minutes as economically equivalent. The main hypothesis is that trend/impulse setups have different expectancy during high-liquidity session overlaps and around scheduled macro releases than during quiet hours.

## External evidence to reproduce internally

- MarketMilk exposes per-hour volatility statistics and identifies the most/least volatile hours for individual symbols, including XAU/USD.
- BabyPips describes the New York morning as the most active part of that session and highlights the London/New York overlap as a high-liquidity period for USD pairs.
- LBMA describes London and New York as the two principal gold-market centres. London bullion market-making hours are 08:00-17:00 London time.
- XAU/USD is effectively traded nearly around the clock at retail CFD venues, so the research variable should be session/liquidity regime, not a simplistic open/closed flag.

## Research design

Do not scrape or depend on MarketMilk at runtime. Reproduce the useful idea from our own MT5 data.

For each symbol and 15-minute/hour bucket, calculate on rolling, past-only windows:

1. median and percentile true range / ATR-normalized range;
2. realized absolute return;
3. spread in cash and spread/range ratio;
4. directional persistence after session open (15/30/60/120 minutes);
5. breakout follow-through versus reversal rate;
6. MFE/MAE and net expectancy of the existing setup family;
7. sample size and confidence bands;
8. separate weekday and DST-aware session labels.

Candidate session labels:

- ASIA;
- LONDON_OPEN;
- LONDON_CORE;
- LONDON_NEW_YORK_OVERLAP;
- NEW_YORK_OPEN;
- NEW_YORK_CORE;
- NEW_YORK_LATE;
- ROLLOVER/LOW_LIQUIDITY.

For early September 2026, Vietnam is UTC+7, New York is on EDT (UTC-4), and London is on BST (UTC+1). Approximate local windows therefore place the London/New York overlap around 19:00-23:00 Vietnam time. Code must derive DST-aware times rather than hard-code these offsets.

## Trading hypothesis

A successor should use session regime as a conditioning feature/gate, not as a guaranteed-profit rule. Example research question:

`HTF regime -> session liquidity regime -> setup identity -> reclaim -> separation -> retest -> post-retest quality -> entry`

Possible gates/features to test:

- only accept continuation entries when current rolling hourly volatility is above the symbol's own historical percentile threshold but spread/range remains efficient;
- distinguish high-volatility trend expansion from high-volatility whipsaw using directional efficiency / close-location / M1-M5 impulse persistence;
- suppress late-session entries when spread/range deteriorates;
- avoid hard-coding New York as always superior: learn expectancy by symbol/session from historical data and then validate prospectively.

## Methodology boundary

This is a new development research track. Do not alter frozen V69 while diagnosing its live execution path. Any session-conditioned successor needs walk-forward/holdout discipline and must not reuse the V69 development replay as independent evidence.
