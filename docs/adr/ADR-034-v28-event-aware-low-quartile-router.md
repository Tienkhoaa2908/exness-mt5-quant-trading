# ADR-034 — V28 event-aware low-quartile router

## Decision
Use USD high-impact event schedule/family clocks only as a market-range regime input. Mechanical strategies remain the sole direction owner.

For V28 stateful MT5 replay, promote only the natural 25th-percentile low-range boundary. Do not replay a large optimized threshold grid.

The replay catalog contains six frozen controls plus four event-aware routes: EMA low-quartile veto, low-quartile MACD switch, low-quartile BOS switch, and low-quartile MACD vs normal EMA+BOS router.

## Rationale
The event-aware 2h+4h range score is positive in 13/13 OOS months and adds statistically positive paired monthly rank-correlation uplift versus the price/cross-asset base. Trade-ledger screening shows EMA skip20 has near-zero/negative expectancy in the low quartile in both early and later partitions while MACD gap10 remains positive.

Hard multi-band family selection and direct direction ML are rejected because they do not survive stability checks.

## Safety
REAL-MONEY LIVE TRADING = FORBIDDEN. Tester-only virtual books. Stop-risk research ceiling 1.00%/trade. Frozen peak-lock exit.