# V31 AI Router — one-shot MT5 Strategy Tester gate

Safety: **Strategy Tester / virtual books only. REAL-MONEY LIVE TRADING IS FORBIDDEN.**

This runtime compiles and backtests `V31AiRouterLabV1` on `XAUUSDm M15` over the frozen historical implementation interval `2025-08-01 -> 2026-08-01`.

Models inside the same EA:

- distilled deep ReLU network, `73 -> 96 -> 48 -> 24 -> 1`;
- linear SVR expected-R control;
- RBF-kernel approximation via 384 random Fourier features + Ridge teacher.

All models are frozen before the test interval. Training labels end before `2025-07-01`; score thresholds are fixed from July-2025 score distributions only. The V31 test interval is used as an implementation/economic development backtest, not as a new pristine statistical holdout because model development has already inspected this historical period offline.

The EA also keeps the 12 V30 baseline candidates. It writes 15 candidates x 4 virtual books each month. The `$40` books are:

- `usd40_r0p5_cent` — 0.50% risk/trade;
- `usd40_r0p75_cent` — 0.75% risk/trade;
- `usd40_r1p0_cent` — 1.00% risk/trade.

The research ceiling remains 1.00% risk per trade. The `15%/month` figure is a target gate, not a promised return.

The tester configuration uses MT5 `Every tick` generated ticks. It must not be described as 12 months of broker real-tick history.

## What the runner does

1. Locates the accepted MT5 data folder by the exact V30 source SHA.
2. Verifies the V31 EA/model-artifact SHA-256 values.
3. Copies the V31 source and frozen model headers into `MQL5/Experts/mt5_quant`.
4. Compiles with MetaEditor and requires `0 errors / 0 warnings`.
5. Backs up the user's current adaptive state.
6. Loads the exact state checkpoint after July 2025.
7. Runs one MT5 Strategy Tester interval: `2025-08-01 -> 2026-08-01`.
8. Collects `bar_features.csv`, `monthly_summary.csv`, `trades.csv`, `manifest.txt`, compile log, and final state.
9. Requires 12 months x 15 candidates x 4 books = 720 summary rows.
10. Restores the user's pre-run adaptive state and creates one ZIP for upload.

If a complete checkpoint exists, rerunning the Bash script packages it again without rerunning MT5.
