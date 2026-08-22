# V28 later confirmation: fixed range router rejected; V29 direction

Ngày: 2026-08-19.

## Policy note

This is historical V28/V29 research evidence. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The no-native-order/1.00%-risk constraints in this research sequence were phase-specific and are not a permanent prohibition on researching or preparing production/live trading with real capital.

## Runtime/data evidence

Latest V3 user diagnostic ZIP SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`.

Calendar extraction was eventually closed rather than repeatedly asking the user to rerun the exporter.

## Later confirmation without retuning V28 threshold

The cross-asset range model was frozen through Feb-2026 and scored Mar-May 2026 without retuning the natural V28 0.25 threshold.

The range/regime layer generalized strongly, but the incremental USD-calendar uplift did not confirm in Mar-May. Calendar remained useful context/telemetry rather than a mandatory alpha block.

## Fixed V28 low25 routing hypothesis fails

Later confirmation reversed the earlier screening premise that low25 was the weak EMA state. Family × scalar-range mapping was nonstationary.

Decision: reject the existing V28 preregistered low25 stateful replay. Do not rerun that obsolete V28 replay.

## Other ML gates checked

Frozen cross-asset direction classification remained modest; EMA trade-level meta-labeling collapsed near random in later confirmation; future path/trend-efficiency prediction was weak. ML therefore remained better suited to continuous market-state estimation than direct Buy/Sell ownership in this historical sequence.

## V29 orthogonal-alpha screening

A multi-horizon slow-momentum expert was screened from existing MT5 bars without requesting new user data. Central construction used server 00:00/08:00 decisions, 16h+24h trailing-return agreement, next-bar entry, 8h max hold, 2ATR initial stop and TP4R.

Recent-year expectancy was positive but longer history exposed regime dependence. This was a promising orthogonal expert, not a universally-on replacement.

## V29 architecture decision

1. Keep the validated ML range model as a continuous state feature.
2. Add a different slow multi-horizon momentum expert.
3. Maintain existing EMA/BOS/MACD/Trend experts as independent shadow books.
4. Use change-point severity to control adaptation speed rather than Buy/Sell direction.
5. Use nonstationary online-expert allocation/switching-cost-aware logic rather than fixed `range_pct -> family` lookup.
6. Evaluate worst-window/DD/turnover penalties, not mean return alone.
7. Keep fast-reversion/changepoint expert experimental until conditional edge is stable.

## Next gate at that time

Create V29 Adaptive Change-Point + Multi-Horizon Expert Lab offline first, without requesting more MT5 data, then provide only one MT5 replay batch after freezing the candidate catalog.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
