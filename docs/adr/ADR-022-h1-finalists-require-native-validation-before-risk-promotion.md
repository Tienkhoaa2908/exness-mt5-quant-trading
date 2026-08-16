# ADR-022 — H1 finalists require native validation before risk promotion

Date: 2026-08-16

## Context

QualityExitLabV1 screened 16 pre-registered variants across seven non-overlapping 1–3 month windows and four capital/risk books. H1 trend alignment was more robust than tighter SL or larger TP alone. Virtual USD 40 / 1.00% results were strongest for `ema_h1_2atr_2r` and most stable for `trend_h1_2atr_2r`.

The virtual lab does not exactly reproduce every native rolling cash result. Previous native rolling runs also had zero margin rejects, so higher leverage is not the main missing component; minimum-lot/risk granularity and strategy expectancy are more important.

## Decision

1. REAL-MONEY LIVE TRADING remains forbidden.
2. Promote only `trend_h1_2atr_2r` and `ema_h1_2atr_2r` to a native rolling gate.
3. Keep stop=2 ATR and TP=2R frozen for that gate.
4. Validate both finalists across the same seven 1–3 month windows with native MT5 CTrade, generated Every Tick, XAUUSDm/M15, dynamic broker-session preflight.
5. Native normalized risk remains 0.50%; translate native ledgers afterward to USD 40 at 0.50%, 0.75%, and 1.00% strict-target stop-risk.
6. 1.00% remains the aggressive research ceiling. No >1.00% stop-risk research in the current phase.
7. Use tester leverage 1:200 as a conservative margin-stress environment; leverage must not be used as a substitute for edge.
8. Only after native validation may a combined H1 Trend + H1 EMA shared-risk/adaptive-risk portfolio be tested.

## Consequences

The project tests the most promising signal-quality improvement without reopening a broad parameter search. The 15–20% 1–3 month aspiration remains a research target, not a guarantee.