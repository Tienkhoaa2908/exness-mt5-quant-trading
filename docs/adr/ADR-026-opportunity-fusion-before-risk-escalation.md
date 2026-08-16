# ADR-026 — Expand signal opportunity before risk escalation

## Status

Accepted — 2026-08-16.

## Context

Profit Protection Lab V1 confirmed that fixed 2R exits gave back material open profit. The best practical exit variant, EMA H1 with 50%-of-peak lock after +1R and TP4R, eliminated observed `MFE>=1R -> realized<=0R` cases and improved the USD40/1% median monthly return from about +3.54% to +6.32%, while reducing observed max MTM drawdown from about 10.96% to 9.02%.

This improvement remains far below the 15–20% monthly aspiration. Raising stop-risk above 1% was already shown in prior monthly native replays to increase drawdown faster than it improved the median return.

Earlier V4 evidence showed positive long-screen performance for RSI2 trend reversion and fast MACD trend families. These are bounded, pre-existing hypotheses rather than a new unrestricted parameter search.

## Decision

1. Keep the approved research ceiling at 1.00% stop-risk per trade.
2. Freeze the exit geometry for the next virtual gate to the best practical Profit Protection policy: initial stop 2 ATR, TP 4R, after +1R protect 50% of peak R.
3. Reintroduce only previously evidenced signal families: EMA H1, RSI2 trend reversion, MACD 8/21/5 trend and Trend H1.
4. Evaluate standalone and one-position-at-a-time signal-fusion candidates on 18 independent calendar months.
5. Fusion candidates never stack simultaneous positions on XAUUSD; conflicting opposite same-bar signals are skipped. This bounds combined open risk and aligns the research model with a future Netting execution design.
6. Use USD40 books at 0.50%, 0.75% and 1.00% plus a normalized continuous control.
7. Any virtual winner must return to native MT5 validation before promotion.

## Consequences

The next experiment tests whether return can be increased through more independent positive-expectancy opportunities rather than through larger per-trade risk. It deliberately does not add a broad indicator grid, unrestricted optimization, Martingale, grid averaging, or >1% stop-risk.

REAL-MONEY LIVE TRADING remains forbidden.