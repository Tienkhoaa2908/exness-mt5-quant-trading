# V31.1 handover — ready for exact MT5 USD40 tournament

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`

## Current gate

V31.1 is ready for a Windows MT5 Strategy Tester run. It is not a promotion and has no live-order path.

Safety invariants remain unchanged: REAL-MONEY LIVE TRADING FORBIDDEN; no `OrderSend`/`CTrade`; no Martingale/grid/doubling; research risk ceiling 1.00%/trade.

## Why V31.1 exists

The older USD40 research books reset balance to USD40 each month. V31.1 adds a continuous-capital interpretation for the 1.00%-risk book so the test starts with USD40 once and carries ending capital into the next month. Month-end liquidation remains enabled so monthly target measurement is explicit.

Target runtime book: `usd40_r1p0_cent_continuous`.

MT5 tester config: Deposit=40 USD, leverage assumption 1:200, XAUUSDm M15, 2026-02-01 -> 2026-08-01.

## Model modes

- baseline
- CatBoost expected-R
- ExtraTrees expected-R
- DeepMLP 64-32-16
- LinearSVM/LinearSVR
- CatBoost AND ExtraTrees
- majority 2-of-4

All model modes restore the exact same adaptive-state checkpoint before launch.

## Causal tape

The tape is rebuilt from the accepted V30 MT5 feature/trade folders. Training entries use latest `feature_available_time <= entry_time`. Gate inference is keyed to actual current M15 bar starts and uses latest `feature_available_time <= current_bar_start`, which avoids the prior session/weekend-gap bug.

Pinned Linux reference tape SHA-256:
`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

Expected V31.1 source SHA-256:
`45ace4bd7465dbfb8a1b5670b67d372643b1eea057b1d7a44d80b91caf2b7c3e`

Starting adaptive state SHA-256:
`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`

## Run entrypoint

`runtime/v31_mt5_model_gate/BOOTSTRAP_V31_ONE_SHOT_GIT_BASH.sh`

It updates/clones the repo, calls `RUN_V31_1_EXACT_MT5_USD40_GIT_BASH.sh`, builds the isolated pinned Python environment, rebuilds models/tape, compiles each tester-only EA, runs seven MT5 passes, collects outputs, analyzes exact MT5 numbers, and emits one ZIP.

Primary decision comparison is always the same candidate: `adaptive_ewma_hl8_thr0`. Best-candidate-per-mode output is exploratory only.

## Exact evidence required

The analyzer reports starting/ending capital, compounded and monthly returns, count of >=15% months, worst month, full-period max MTM DD, trades, AvgR, PF, rejects and turnover. 15%/month is an aspirational gate, not a guarantee; risk must not be raised to manufacture the target.
