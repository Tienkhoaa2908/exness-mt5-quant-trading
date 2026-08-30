# ADR-062 — V60 Small-Loss Cash-Target Research

Status: ACCEPTED FOR RESEARCH IMPLEMENTATION

## Context

V59 proved that the standalone engine can trade both LONG and SHORT with fixed 0.01 lot, but its realized performance remained poor because the architecture still tolerated losses that were large relative to a USD40 book while waiting for large 3R winners.

The V59 diagnostic also exposed two structural issues:

1. H4-neutral conditions were allowed as long as H4 was not explicitly opposite. That is too loose for a trend-following baseline.
2. The premium/discount mapping overlapped: `range_location <= 0.55` assigned LONG before the `>= 0.45` SHORT branch could run, creating an unintended LONG bias in the 45%-55% middle region.

The user-approved research priority is now loss-first: reduce both loss frequency and loss magnitude. A trade that repeatedly captures USD2 with small losses can be preferable to a low-hit-rate architecture that waits for very large winners.

## Decision

### 1. Loss-first objective

V60 is evaluated primarily on:

- win rate;
- average loss USD;
- maximum single-trade loss USD;
- count of losses worse than USD1.00 and USD1.25;
- profit factor;
- net USD;
- realized drawdown;
- LONG/SHORT attribution.

Large nominal RR is not the primary objective.

### 2. Fixed lot remains 0.01

`InpV60FixedLot = 0.01` remains invariant for this research branch.

Risk reduction must therefore come from setup selection, entry location, structural invalidation and exit quality rather than reducing lot size.

### 3. Do not fake a $1 stop

V60 does not move a stop inside the true structural invalidation merely to manufacture a USD1 loss cap.

The stop remains based on the latest confirmed causal M15 swing plus a small ATR buffer. The exact loss at 0.01 is calculated with `OrderCalcProfit`.

If the true structural stop requires more than USD1.25 of loss, the setup is rejected.

This means:

- preferred loss is around USD1;
- hard structural-risk admission cap is USD1.25;
- a setup needing USD3-USD5 of structural room is skipped rather than traded with a fake tight stop;
- lot is not reduced below 0.01.

### 4. Primary target is $2

The actual tester order uses a USD2 cash profit target. The price level is solved from `OrderCalcProfit` for the fixed 0.01 lot rather than approximated from points.

The same real-tick path shadow-tests USD2, USD3 and USD4 profit targets so the research can determine whether larger targets improve expectancy without requiring three separate MT5 passes.

### 5. Conditional soft-loss cut around $1

A floating loss near USD1 is not an unconditional market-order exit. V60 closes early only when the loss threshold is reached and causal closed-bar evidence also shows either:

- structural/BOS-CHoCH reversal against the position; or
- M15 trend + MACD + DI momentum reversal against the position.

This is intended to reduce average loss without turning ordinary noise into forced exits.

The hard structural stop remains in place and is already limited by the USD1.25 setup-admission cap.

### 6. Strict higher-timeframe trend alignment

A LONG setup requires H1 bullish and H4 bullish.

A SHORT setup requires H1 bearish and H4 bearish.

H4 neutral no longer qualifies as trend confirmation.

The engine remains symmetric; a bullish regime is not forced to create SHORT trades and a bearish regime is not forced to create LONG trades.

### 7. Premium/discount symmetry fix

Recent confirmed swing range location is mapped as:

- `<= 0.45`: discount / LONG evidence;
- `>= 0.55`: premium / SHORT evidence;
- `0.45 .. 0.55`: neutral.

This removes the V59 overlapping threshold that biased the middle range toward LONG.

### 8. Spread budget follows target economics

Because structural risk is intentionally small, spread is no longer limited to a percentage of stop risk. V60 caps spread cash against the profit target economics:

`allowed_spread = min(max_spread_cash, primary_target_cash * max_spread_target_pct)`.

The default target is USD2 and the default target-fraction cap is 15%.

### 9. Validation breadth

The screen phase uses MT5 Model=2 only to locate recent strict-trend feasible windows and does not inspect PnL.

Final evidence uses MT5 Model=4 real ticks over four windows:

- two LONG-aligned weeks;
- two SHORT-aligned weeks.

Window selection is based on strict H4/H1-aligned feasible setup presence, not profitability.

The analyzer counts completed round trips from closing deals rather than counting both entry and exit deals as separate trades.

## Promotion criteria are intentionally not fixed yet

V60 is a research milestone. Results must first show whether the small-loss architecture actually improves loss frequency, average loss and net expectancy across both directions.

No result from a single week or a small sample is sufficient for REAL promotion.

## Non-goals

- V60 is not authorization for REAL-money activation.
- V60 does not guarantee that a USD2 target is optimal.
- V60 does not force a trade when structural invalidation is too expensive.
- V60 does not reduce lot below 0.01.
- V60 does not use future bars to define swings, structure or direction.
