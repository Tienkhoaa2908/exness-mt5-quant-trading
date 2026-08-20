# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/grid/loss doubling.
- Research stop-risk ceiling: 1.00%/trade.
- Không native/external broker orders trong current research gates.

## Accepted V30 data/runtime

Accepted `MlDlFeatureLakeV1.mq5` source SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile: `0 errors / 0 warnings`.

Canonical 18-month M15 lake:

- 35,344 rows, 2025-02 through 2026-07;
- 136 raw fields;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in accepted raw lake;
- 864 monthly-summary rows;
- 28,128 total ledger rows;
- adaptive state continuous across three chunks.

Final acquisition ZIP SHA-256:

`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Mandatory causal contract:

`feature_available_time = bar_features.time + 15 minutes`

Trade/current-bar inference uses only the latest row available by decision time. Across session/weekend gaps, model tapes are keyed by actual current M15 bar start using causal as-of availability.

## Accepted V31.1 exact-MT5 milestone

Uploaded V31.1 ZIP SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

Seven complete MT5 Strategy Tester passes: baseline, CatBoost, ExtraTrees, DeepMLP 64-32-16, LinearSVM/SVR, CatBoost AND ExtraTrees, majority 2-of-4.

All compiled 0/0, MT5 rc=0, tester-only, no native/external broker orders, continuous USD40. Common contract: XAUUSDm M15, 2026-02-01 -> 2026-08-01, Deposit=USD40, `usd40_r1p0_cent_continuous`, <=1.00% risk target/trade, leverage assumption 1:200, identical starting state before every pass.

Primary `adaptive_ewma_hl8_thr0`:

- baseline: end USD62.3573, geo 7.6807%/month, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579;
- DeepMLP keep50: end USD60.4393, geo 7.1215%, DD 7.3551%, 146 trades, AvgR 0.3329R, PF 1.8037;
- CatBoost / ExtraTrees / LinearSVM / simple voting materially underperform as primary binary gates and are rejected in that role.

V31.1 causal tape SHA:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

Read `docs/research/v31_1_exact_mt5_usd40_results.md`.

## Accepted V32 development sweep

Uploaded V32 ZIP SHA-256:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Six complete passes: baseline and DeepMLP keep50/60/70/80/90. All compile 0/0, MT5 rc=0, tester-only, no native/external orders, six months written, continuous USD40.

V32 source SHA:

`ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`

V32 nested causal tape SHA:

`8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`

It matched the reference byte-for-byte.

### Primary `adaptive_ewma_hl8_thr0`

| Mode | End USD | Geo/month | Max DD | Trades | AvgR | PF | Turnover/$40 |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 | 1045.67x |
| **keep60** | **62.1444** | **7.6193%** | **7.3639%** | **153** | **0.3250R** | **1.8326** | **764.42x** |
| keep80 | 60.9896 | 7.2834% | 9.9301% | 191 | 0.2502R | 1.6374 | 883.29x |
| keep70 | 60.9569 | 7.2738% | 9.0562% | 179 | 0.2695R | 1.6670 | 857.14x |
| keep50 | 60.4393 | 7.1215% | 7.3551% | 146 | 0.3329R | 1.8037 | 728.65x |
| keep90 | 53.2804 | 4.8942% | 16.3281% | 210 | 0.1699R | 1.3828 | 840.60x |

keep60 is the bounded development winner for the preregistered primary lane. Relative to baseline it finishes only ~0.34% lower in capital while reducing max DD ~31.9%, trades ~31.1% and turnover ~26.9%; AvgR rises ~35.4%, PF ~17.6%, and return/DD ~45.5%.

It still does **not** improve the explicit 15%-month target: keep60 has 1/6 months >=15% versus baseline 2/6. No V32 mode reaches 15% geometric/month. Do not raise risk to force the target.

Important: nested model-score masks do not create nested realized trade sets because a filtered trade changes later adaptive/one-position state. Exact MT5 replay remains mandatory.

Exploratory only: `adaptive_ewma_hl12_thr0p05 + keep80` ends USD66.6393, geo 8.8792%/month, DD 7.0573%, AvgR 0.3128R, PF 1.8086. It is post-hoc candidate/threshold selection and cannot replace primary evidence.

Read:

- `docs/research/v32_deep_mlp_keep_sweep_plan.md`
- `docs/research/v32_deep_mlp_keep_sweep_results.md`

## Frozen confirmation lane

Freeze `adaptive_ewma_hl8_thr0 + DeepMLP keep60` exactly. Do not tune its threshold again on February-July 2026. A promotion claim requires a genuinely fresh complete chronological holdout versus the frozen baseline.

## V33 development lane

Binary gating has reached diminishing returns. V33 moves the neural signal toward **policy control** rather than adding another larger classifier.

Plan:

- shared neural state with targets for expected R, MFE, MAE and giveback;
- bounded soft-risk actions that never exceed 1.00% stop-risk;
- bounded exit routing between fixed-4R behavior and previously studied profit-protection policies;
- source/regime conditioning because primary adaptive-router ledgers show EMA/slow-momentum healthy while Trend20 remains weak;
- exact MT5 remains the economic judge because policy changes alter later adaptive state/opportunities;
- complementary independent opportunity generation/allocation remains necessary to move materially toward the aspirational 15% monthly objective.

Read `docs/research/v33_neural_policy_controller_plan.md`.

PAPER/DEMO only after gates. LIVE remains forbidden.
