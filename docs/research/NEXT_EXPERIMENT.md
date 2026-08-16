# NEXT EXPERIMENT — Monthly Quality / Exit Re-screen V1

## Why

Monthly H1 Native V1 is complete. USD 40 at 1.00% stop-risk produced median monthly returns of only about +2.43% (Trend) and +3.69% (EMA). Hit rates for >=15% were 3/18 and 1/18.

The practical monthly target is therefore not met. Exploratory 2.00% replay still produced median monthly returns below 10% while increasing worst-month losses and drawdown materially, so risk escalation is not the next step.

## Goal

Re-rank the already pre-registered entry-quality and exit variants for the one-month horizon before inventing new parameters.

## Batch

Run the exact Windows-proven `QualityExitLabV1.mq5` source over 18 independent calendar months, 2025-02 through 2026-07.

Each monthly run evaluates 16 variants x four independent books:
- normalized USD 10,000 continuous @0.50%;
- USD 40 cent-equivalent @0.50%;
- USD 40 cent-equivalent @0.75%;
- USD 40 cent-equivalent @1.00%.

The catalog includes baseline 2ATR/2R, 1.5ATR stops, 2.5R/3R exits, break-even runner, ADX, H1 alignment, price-quality filters, and combined quality variants.

## Decision metrics

- median/mean monthly USD 40 return;
- positive-month ratio;
- >=15% and >=20% hit rates;
- worst/best month;
- MTM DD;
- PF / AvgR / win rate;
- signal participation under tiny-capital lot quantization;
- 2025 vs 2026 stability.

No virtual candidate is deployable. Any finalist returns to native MT5 validation.

## Reliability

Runner uses a LocalAppData checkpoint and reuses validated completed months after interruption. One infrastructure failure must not force all 18 runs to rerun. Diagnostic ZIP includes checkpoint and recent MT5 logs.

REAL-MONEY LIVE TRADING remains forbidden.
