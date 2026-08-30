# ADR-065 — V63 Profit-Quality + Structural-Risk-Zone Research

Status: accepted for Strategy Tester research only. No REAL-money authorization.

## Context

V62 increased recent four-week actual entry count from the tiny V61 sample to 11 trades, but only 3 won. The isolated-pass month net was about +$1.14 with PF about 1.14, average winner about +$3.08 and average loser about -$1.01. Week4 was 0W/3L and erased most earlier gains. V62 produced zero SHORT broker trades in the recent bullish month. Its four strict SHORT signals still had structural risk above the permitted band after refinement.

The operator's practical research objective is materially higher profit: roughly three quality trades per week is acceptable if winners are large enough and losses remain small. A useful reference case is two +$3.5 winners and one approximately -$1 loser, which is about +$6 for that week. This is a research objective, not a promised return or optimization guarantee.

V62 also had a pending-lifecycle defect: repeated same-direction M15 signals reset the 240-minute pending timestamp, so TTL could be extended indefinitely.

## Decision

V63 preserves fixed lot 0.01 and bidirectional direction-isolated testing, but changes entry and risk handling.

1. Planned structural cash risk is tightened to $0.60-$1.05. The lower minimum remains far above the invalid ultra-tight stop observed in V60; the lower maximum leaves headroom because V62 showed that realized loss can exceed planned stop risk.
2. An emergency cash-loss guard is set around $1.10. It is a market-close safety layer and cannot guarantee an exact realized loss because fast movement/slippage remains possible.
3. Actual cash target is +$3.50. The existing +$2 -> lock +$1 ratchet remains the control management policy. Existing $2/$3/$4 tick-level shadow paths remain diagnostic comparators.
4. Pending TTL is anchored to the first M15 arm. Repeated same-direction signals may be logged as refresh evidence but may not reset first-arm time.
5. Immediately before refined entry the EA rebuilds current causal H4/H1/M15 features and reruns the current directional selector. A stale setup cannot enter after its original regime disappears.
6. Existing ADX/DI/MACD information is used more decisively rather than adding arbitrary confluence points. Entry is vetoed when DI and MACD both oppose the trade, or when weak ADX combines with non-aligned M15/BOS evidence. A fully opposite M15 structure/BOS/trend state is also vetoed.
7. V63 replaces the V62 EMA20-retest-first logic with structural-risk-zone entry. The EA waits until the current market price plus the current valid structural stop naturally produces the allowed 0.01 cash risk. Only then does a closed M1 turn authorize submission. No stop is fabricated merely to fit the cash budget.
8. Actual benchmark windows remain the four fixed complete August 2026 weeks for direct V62 comparison. Each week still has independent LONG-only and SHORT-only Model=4 real-tick passes.
9. To obtain valid SHORT evidence without forcing shorts into a bullish month, V63 also runs a dedicated Model=2 directional screen from 2025-09-01 through 2026-08-29. It selects the four most recent non-benchmark weeks with at least 8 strict SHORT signals and SHORT share >=60%. Selection uses no PnL. Those four weeks receive SHORT-only Model=4 real-tick passes.
10. Total real-tick passes are therefore 12: eight fixed benchmark passes plus four bearish-window SHORT passes.

## Profit/frequency reporting

The analyzer reports each benchmark week separately, LONG and SHORT separately, and the isolated combined sum. It explicitly reports average trades per benchmark week, number of weeks with at least 3 trades, positive weeks, weeks netting at least $5 and at least $6, actual average win/loss and maximum realized loss.

The approximately 3-trades/$6-week figures are research goals only. V63 must not stop trading, widen risk, or select windows based on realized PnL to hit them.

## SHORT semantics

The same directional scoring framework remains mirrored for LONG/SHORT. Symmetry of rules does not imply equal trade counts in every market regime. The extra bearish-window protocol exists specifically to observe SHORT execution when the higher-timeframe regime is actually bearish.

## Safety

- Strategy Tester only.
- REAL-money authorization remains false.
- Do not interpret isolated-pass sums as a concurrent account equity curve.
- Do not widen the stop budget merely to increase frequency or force SHORT fills.
- Do not promote a target, veto, or risk policy from a tiny sample without fresh Model=4 evidence.
