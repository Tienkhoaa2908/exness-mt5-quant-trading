# V29 Adaptive Expert Lab — workflow

One MT5 run only; no new data exporter.

- 3 chunks × 6 months = Feb-2025 through Jul-2026.
- 12 candidates × 4 virtual books = 48 books per tick stream.
- Independent monthly PnL/risk accounting resets; adaptive expert-performance state carries causally across chunk boundaries.
- Controls: EMA skip20, MACD gap10, BOS/FVG gap8, Trend gap5, EMA+BOS8 router.
- Orthogonal controls: slow 16h+24h momentum with 8h timebox, with/without peak-lock.
- Adaptive: EWMA hl8/10/12 and one fast5-vs-slow20 change-severity probe.
- Rank on USD40@1% and normalized 10k@0.5%, emphasizing positive months, worst month, MTM DD, AvgR, turnover and source mix.
- Existing validated cross-asset range model remains market-state telemetry; it is not used as another fixed hard family gate in this replay.

Promotion requires Windows MetaEditor 0/0, complete 18-month stateful replay, and robust improvement beyond mean return alone. A passing finalist proceeds to PAPER/DEMO forward validation only; LIVE remains forbidden.
