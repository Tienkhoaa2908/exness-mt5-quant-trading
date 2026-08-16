# ADR-027 — Re-entry hysteresis and turnover control before further alpha expansion

## Status

Accepted — 2026-08-16.

## Context

Opportunity Fusion Lab V1 completed 18 independent monthly resets. Adding more signal sources increased trade count and turnover but did not improve the robust USD 40 monthly profile. The standalone EMA H1 peak-lock control remained best by median monthly return.

Sequence diagnostics on the USD 40 @1.00% EMA control found 161 winner -> next-trade loser pairs; 102 occurred when the next same-direction entry arrived within four hours, and 94 of those followed a profitable `PROTECT_STOP` exit. The fusion-all H1 candidate re-entered within four hours on roughly 85% of consecutive-trade pairs and had materially worse median return than EMA control.

This is a churn / hysteresis problem, not evidence that every adjacent losing trade is avoidable.

## Decision

1. Do not promote any Opportunity Fusion candidate.
2. Freeze the proven peak-lock exit:
   - initial stop = 2 ATR;
   - TP = 4R;
   - once MFE >= +1R, protect 50% of peak R.
3. Re-screen only the two stronger entry families:
   - EMA H1 pullback/reclaim;
   - Trend H1 breakout.
4. Pre-register bounded turnover controls:
   - 1h / 2h / 4h cooldown after any exit;
   - 2h / 4h cooldown after a profitable exit;
   - same-direction re-arm after a 0.25 / 0.50 ATR adverse move from the prior profitable exit;
   - combined 2h profit cooldown + 0.25 ATR re-arm;
   - max two entries/day + 2h profit cooldown.
5. Measure turnover explicitly:
   - median trades/month;
   - gross notional turnover / starting capital;
   - re-entries within four hours;
   - post-profit rapid re-entries;
   - post-profit next losses and rapid post-profit losses;
   - churn/cooldown/re-arm/daily-cap rejects.
6. The USD 40 stop-risk ceiling remains 1.00% per trade. Leverage is not increased to compensate for filtered trades.
7. This is virtual tester-only screening. Any finalist must return to native MT5 before promotion.

## Rationale

With trading frictions, optimal policies often include inaction/no-trade regions or gradual adjustment rather than reacting to every marginal signal change. The project-specific evidence shows that broad signal fusion increased activity faster than it increased expectancy, so reducing low-quality repeat entries is a higher-priority experiment than adding another signal family.

## Consequences

A successful candidate must improve the return/turnover/drawdown trade-off, not merely reduce trade count. If churn control lowers turnover but also destroys monthly return, it is rejected.

Real-money live trading remains forbidden.

## Research references

- Gârleanu & Pedersen, *Dynamic Trading with Predictable Returns and Transaction Costs*: optimal dynamic policies trade gradually toward desired positions when trading is costly.
- Novy-Marx & Velikov, *A Taxonomy of Anomalies and Their Trading Costs*: a buy/hold spread—stricter requirements for establishing a new position than for continuing to hold—is an effective simple turnover-mitigation technique.
- Lo, Mamaysky & Wang, *Asset Prices and Trading Volume under Fixed Transactions Costs*: even small fixed costs can generate economically meaningful no-trade regions.