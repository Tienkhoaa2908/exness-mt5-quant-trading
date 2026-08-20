# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/grid/loss doubling.
- Research stop-risk ceiling: 1.00%/trade.
- Không native/external broker orders trong current research gates.

## Accepted V30 data/runtime

V30 `MlDlFeatureLakeV1.mq5` source SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile: `0 errors / 0 warnings`.

Canonical 18-month M15 feature lake after half-open trim/stitch:

- 35,344 rows, 2025-02 through 2026-07;
- 136 raw fields;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in accepted raw lake;
- 864 monthly-summary rows;
- 28,128 total trade-ledger rows;
- adaptive state continuous across the three chunks.

Final acquisition ZIP SHA-256:

`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Mandatory causal contract:

`feature_available_time = bar_features.time + 15 minutes`

Trade/current-bar inference may only use the latest row with availability <= decision time. Across weekend/session gaps, a gate tape must be keyed by the actual current M15 bar start, not by blindly adding 15 minutes to the previous row timestamp.

## Accepted V31.1 exact-MT5 evidence

V31.1 is the accepted first exact Strategy Tester comparison of ML/NN/SVM gating on a **continuous USD40 virtual research account**.

Uploaded V31.1 result ZIP SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

All seven passes:

- compiled `0 errors / 0 warnings`;
- MT5 returned rc=0;
- fresh collection completed;
- manifest `tester_only=1`;
- `native_broker_orders=0`;
- `external_broker_orders=0`;
- `continuous_usd40=1`.

Exact common test contract:

- XAUUSDm, M15;
- 2026-02-01 -> 2026-08-01;
- Strategy Tester Deposit = USD40;
- continuous book `usd40_r1p0_cent_continuous`;
- risk target <=1.00% of current book balance per trade;
- leverage assumption 1:200;
- same accepted adaptive state restored before every model pass;
- month-end liquidation retained.

V31.1 causal model tape SHA-256:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

It matched the pinned reference byte-for-byte on Windows.

### Primary same-candidate result

Frozen primary candidate: `adaptive_ewma_hl8_thr0`.

| Mode | End USD | Geo/month | Max MTM DD | Trades | AvgR | Ledger PF |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 |
| DeepMLP 64-32-16 | 60.4393 | 7.1215% | 7.3551% | 146 | 0.3329R | 1.8037 |
| CatBoost | 51.2744 | 4.2254% | 11.8421% | 172 | 0.1559R | 1.3845 |
| CatBoost AND ExtraTrees | 47.3229 | 2.8415% | 12.2095% | 118 | 0.1930R | 1.3749 |
| majority 2-of-4 | 46.1485 | 2.4117% | 18.1616% | 202 | 0.1286R | 1.1828 |
| ExtraTrees | 45.6841 | 2.2392% | 14.7440% | 134 | 0.1359R | 1.2692 |
| LinearSVM / SVR | 44.0550 | 1.6223% | 9.7890% | 179 | 0.0952R | 1.1296 |

Profit factor is computed from exact trade-ledger `total_pnl`. The first V31.1 analyzer used the wrong optional name `net_pnl` and printed NaN; `scripts/analyze_v31_1_mt5_usd40.py` has been repaired.

### Decision from V31.1

- Baseline remains the return winner.
- DeepMLP is a **quality/risk winner**, not a return winner: materially higher AvgR/PF and lower DD/turnover, but its 50%-score gate removes too much profitable breadth.
- CatBoost, ExtraTrees, LinearSVM and simple voting are rejected as primary binary entry gates on this exact-MT5 comparison.
- No mode meets the aspirational 15% geometric monthly target. USD40 compounded at 15% for six months would be ~USD92.52; baseline ends at ~USD62.36.
- Do not raise risk/leverage to force the target.

Primary baseline ledger still shows meaningful excursion/capture information: mean MFE ~1.33R versus realized mean ~0.24R, but prior Profit Protection Lab already showed exit-only improvements do not reach the monthly objective. Opportunity-adjusted alpha remains a major bottleneck.

Evidence:

- `docs/research/v31_1_exact_mt5_usd40_results.md`
- `docs/research/v31_1_exact_mt5_usd40_model_gate.md`

## Current next gate — V32 DeepMLP keep-rate sweep

V32 is a bounded **development** sweep on the already inspected February-July 2026 period. It is not fresh confirmation.

Question: can the same V31.1 DeepMLP preserve more profitable breadth at a broader threshold while retaining some of its DD/AvgR/PF advantage?

Exact MT5 modes:

- baseline
- DeepMLP keep50
- keep60
- keep70
- keep80
- keep90

Same Deposit=USD40, continuous book, <=1.00%/trade risk ceiling, same state and same exact period.

Pinned V32 source SHA-256:

`ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`

Pinned V32 nested causal tape SHA-256:

`8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`

Offline score-only diagnostics suggest the V31 median gate is over-aggressive; e.g. the ~90%-keep region preserves much more realized R. This is only a development clue. Exact MT5 is required because gating changes trade/adaptive paths.

V32 runtime:

- `runtime/v32_mlp_keep_sweep/BOOTSTRAP_V32_ONE_SHOT_GIT_BASH.sh`
- `runtime/v32_mlp_keep_sweep/RUN_V32_DEEP_MLP_KEEP_SWEEP_GIT_BASH.sh`

V32 preregistration:

- `docs/research/v32_deep_mlp_keep_sweep_plan.md`

After V32, freeze or reject the threshold region. Do not continue endlessly tuning February-July. Any selected rule must face a genuinely fresh chronological holdout before promotion claims.

If V32 cannot materially improve the exact-MT5 return/quality tradeoff, move away from binary entry gating toward neural risk/exit control plus genuinely independent opportunity generation/allocation. LIVE remains forbidden.
