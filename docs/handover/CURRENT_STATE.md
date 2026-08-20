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

## Accepted V34 Parallel Alpha Lab exact-MT5 evidence

Uploaded V34/V35 ZIP SHA-256:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

V34 compile 0/0 and exact MT5 completed for 2025-08 through 2026-07, Deposit USD40, continuous book3. Manifest confirms tester-only, no native/external broker orders.

Integrity:

- 816 monthly rows = 12 months x 17 candidates x 4 books;
- 34,508 trade-ledger rows;
- 266,613 intra-trade M15 telemetry rows;
- summary/ledger trade-count mismatch = 0;
- max PnL/AvgR reconciliation error ~6e-6.

Continuous USD40 results:

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | 107.43 | 8.58% | 9.90% | 563 | 0.215R | 1.501 |
| **v34_smc_ict_causal** | **66.83** | **4.37%** | **15.58%** | **1,077** | **0.066R** | **1.108** |
| v34_specialist_confluence | 56.60 | 2.93% | 21.30% | 860 | 0.043R | 1.094 |
| v34_price_action_causal | 50.86 | 2.02% | 20.72% | 1,158 | 0.028R | 1.051 |
| v34_tick_microstructure_proxy | 35.24 | -1.05% | 35.25% | 620 | -0.044R | 0.956 |
| v34_wyckoff_proxy_causal | 25.53 | -3.67% | 43.53% | 527 | -0.128R | 0.798 |

Decision:

- SMC/ICT is a positive but weak/high-turnover independent-alpha research lane, not a primary replacement.
- Price Action is marginal only.
- current Wyckoff and L1/tick-path microstructure proxies are rejected.
- microstructure remains a proxy, not true L2/L3 order flow.

SMC monthly-return correlation to `adaptive_ewma_hl8_thr0` is low (~0.13), so diversification/routing research is justified only with aggregate risk capped; never stack full 1% risk from multiple same-symbol agents.

Read `docs/research/v34_v35_exact_mt5_results.md`.

## V35 AI all-expert meta-router — REJECTED

V35 compile 0/0 and exact MT5 completed for 2026-02 through 2026-07. Cross-run reproducibility PASS: all 17 common norm-book candidates match V34 exactly on entry, exit, direction and R over the overlap period.

Primary comparison, continuous USD40:

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | 62.36 | +7.68% | 10.82% | 222 | +0.240R | 1.558 |
| **v35_ai_all_expert_meta_router** | **24.49** | **-7.85%** | **39.71%** | **571** | **-0.105R** | **0.788** |

The router lost money in every test month. Generic cross-expert expected-R routing is rejected; do not retune thresholds/model size on the same February-July period.

## Current next gate — V36 true intra-trade sequence DL

V34 telemetry is now accepted and available:

- V34 total telemetry rows: 266,613;
- norm-book telemetry covers 9,077 / 9,457 trades = 95.98%; the uncovered 380 trades exited before the first post-entry M15 telemetry point;
- covered sequence length median 9, p75 20, p90 32, p95 44, max 422.

V36 models:

- GRU48;
- true causal dilated TCN48;
- small Transformer encoder with positional information.

V36 must use:

- causal market-state join `feature_available_time <= telemetry_time`;
- candidate identity/context;
- train-only scaling over real timesteps only;
- explicit padding mask;
- future incremental R from current mark as the primary regression target, plus hold/protect classification heads;
- chronological folds with trades in training fully exited before the embargo/calibration month.

V36 remains diagnostic. No reconstructed/offline PnL is promotion evidence. If sequence heads are stable, convert exactly one bounded hold/protect/exit hypothesis into tester-only MT5 and compare against the frozen baseline/challenger.

## Parallel research lane — dedicated SMC quality filter

Do not revive the failed V35 generic router. A dedicated SMC filter may use only prior exact-MT5 SMC outcomes plus causal entry/regime features, with chronological validation and aggregate-risk-aware MT5 replay. The goal is to improve SMC AvgR/PF and reduce its 1,077-trade turnover while preserving its low correlation to the baseline.

## Current decision stack

- Frozen risk-efficiency challenger: `adaptive_ewma_hl8_thr0 + DeepMLP keep60`.
- Baseline remains economically stronger in absolute return on the viewed period.
- V35 generic router: reject.
- SMC/ICT: research-only positive specialist.
- Price Action: marginal/research-only.
- Wyckoff proxy: reject.
- L1 microstructure proxy: reject/redesign.
- V36 sequence exit DL: next diagnostic.
- Aspirational 15% geometric/month objective remains unmet; never raise stop-risk above 1.00% merely to force the target.

PAPER/DEMO only after gates. LIVE remains forbidden.
