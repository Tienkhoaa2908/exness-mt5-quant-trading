# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/grid/loss doubling.
- Research stop-risk ceiling: 1.00%/trade.
- Không native/external broker orders trong current research gates.

## Accepted V30 data/runtime

Accepted `MlDlFeatureLakeV1.mq5` SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile 0/0. Canonical 18-month M15 lake: 35,344 unique rows, 2025-02 through 2026-07, 136 raw fields, 0 duplicate timestamps, 0 NaN/Inf, 28,128 ledger rows, adaptive state continuous.

Final acquisition ZIP SHA-256:

`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Mandatory causal contract:

`feature_available_time = bar_features.time + 15 minutes`

All decisions use only the latest feature row available by decision time; session/weekend gaps require causal as-of joins keyed by actual current M15 bar starts.

## Accepted V31.1 exact-MT5 evidence

ZIP SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

Seven complete exact-MT5 model passes. Primary `adaptive_ewma_hl8_thr0`:

- baseline: USD40 -> USD62.3573, geo 7.6807%/month, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579;
- DeepMLP keep50: USD60.4393, geo 7.1215%, DD 7.3551%, 146 trades, AvgR 0.3329R, PF 1.8037;
- CatBoost, ExtraTrees, LinearSVM and simple voting rejected as primary binary gates.

V31.1 causal tape SHA: `0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`.

## Accepted V32 development evidence

ZIP SHA-256:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

V32 source SHA: `ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`.
V32 nested tape SHA: `8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`.

Primary keep-rate result:

| Mode | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 |
| **DeepMLP keep60** | **62.1444** | **7.6193%** | **7.3639%** | **153** | **0.3250R** | **1.8326** |

Freeze `adaptive_ewma_hl8_thr0 + DeepMLP keep60` for future fresh confirmation. Do not retune February-July 2026. No current mode meets the aspirational 15% geometric/month objective; do not increase risk to force it.

## Accepted V33 multi-task diagnostic

Uploaded ZIP SHA-256:

`16db78c40543495c790d83019999169d566206a591cc4ec570c6b7056df8fefa`

12 chronological OOS months / 4,845 rows:

- expected-R Spearman +0.0249;
- MFE Spearman -0.0050;
- adverse/MAE Spearman -0.0366;
- giveback Spearman -0.0132.

Decision: entry-snapshot neural features are not sufficient for stable MFE/MAE/giveback prediction. Do not merely enlarge the MLP. True exit-DL requires intra-trade sequences.

Read `docs/research/v33_multitask_diagnostic_results.md`.

## Current exact-MT5 gate — V34 Parallel Alpha Lab

V34 expands independent opportunity generation before any risk escalation. New causal specialists:

1. SMC/ICT: confirmed swings, BOS, liquidity sweeps, recent FVG, displacement, premium/discount;
2. Price Action: engulfing/pin, breakout, inside-break, compression;
3. Wyckoff proxy: range location, spring/upthrust, effort/absorption proxies;
4. tick microstructure proxy: tick-direction imbalance, mid-path efficiency, M1 path state, spread stability;
5. specialist confluence.

The microstructure specialist is an **L1/tick-path proxy**, not true L2/L3 order flow. Current V30 `real_volume=0`; no institutional-orderflow claim is allowed without real depth data.

Pinned V34 causal tape, 2025-08-01 -> 2026-08-01:

- 23,617 rows plus header;
- SHA-256 `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.

Pinned V34 deterministic tester-only source SHA:

`8d3700911e2fe680a2a4b02994680e812825ab6cf517bf509aaa4ac230526a77`

One exact MT5 pass evaluates the original 12 candidates plus five new specialists on the same ticks/execution engine, Deposit USD40, continuous book3 at <=1.00% current-balance stop-risk. It also exports `intra_trade_m15.csv` for later true sequence research.

Read `docs/research/v34_parallel_alpha_lab_plan.md`.

## V35 AI all-expert meta-router

V35 trains only after V34 exact outcomes exist. Expert pool = five existing source families (EMA, MACD, BOS/FVG, Trend20, slow momentum) + five V34 specialists.

Training labels are V34 exact-MT5 norm-book `r_multiple`; duplicate `(entry_bar,direction)` opportunities are inverse-weighted. ExtraTrees + HistGradientBoosting + MLP 64-32-16 score active experts. Previous-month calibration threshold is frozen into the next test month; no test-month quantile peeking.

Pinned V35 deterministic source SHA:

`663d97b9345341aa98827e5da31ad441792f944d7c597b7a91bd94c6485e6709`

Offline router scores are not PnL evidence. V35 returns to exact MT5 for final economics.

Read `docs/research/v35_all_expert_meta_router_plan.md`.

## V36 true intra-trade sequence DL

V36 is already implemented but must wait for V34 telemetry. It uses actual open-position M15 sequences and trains:

- GRU48;
- causal dilated TCN48;
- Transformer48x2.

Targets: final R, future additional upside >=0.5R, future giveback >=0.5R. Validation is chronological and train-only scaled. V36 is diagnostic only; any useful policy must return to a tester-only MT5 EA.

Read `docs/research/v36_sequence_exit_dl_plan.md`.

## Runtime

Primary next one-shot runner:

- `runtime/v34_parallel_alpha/BOOTSTRAP_V34_V35_ONE_SHOT_GIT_BASH.sh`
- `runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh`

It runs V34 exact MT5, collects/analyzes, trains V35 from exact V34 outcomes, then runs V35 exact MT5 and emits one ZIP. Checkpoints use `MT5_DONE.txt` so a collection failure must not double-run the tester or double-advance adaptive state.

After V34/V35 evidence is accepted, V36 can run read-only from the V34 intra-trade telemetry.

PAPER/DEMO only after gates. LIVE remains forbidden.
