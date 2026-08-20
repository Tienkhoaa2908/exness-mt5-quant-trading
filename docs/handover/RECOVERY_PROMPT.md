# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch: `agent/v30-ml-dl-feature-lake`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Do not remove tester/live guards.
- No Martingale/uncontrolled grid/loss doubling.
- Do not commit/request credentials or secrets.
- Do not call native/external broker orders for research screening.
- Stop-risk research ceiling: 1.00%/trade.

## Accepted V30 data

V30 `MlDlFeatureLakeV1.mq5` SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Canonical feature lake: 35,344 unique M15 rows from 2025-02 through 2026-07, 136 raw fields, no duplicate timestamps, no NaN/Inf in accepted raw lake, 28,128 ledger rows. Windows compile 0/0.

Causal rule:

`feature_available_time = bar_features.time + 15 minutes`

All trade/current-bar inference uses only features available by decision time. Across session gaps, use actual current M15 bar times with causal as-of joins.

## Accepted V31.1 exact-MT5 evidence

ZIP SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

Seven complete MT5 passes: baseline, CatBoost, ExtraTrees, DeepMLP 64-32-16, LinearSVM/SVR, CB+ET, majority 2-of-4. All compile 0/0, MT5 rc=0, tester-only, continuous USD40, no native/external broker orders.

Primary `adaptive_ewma_hl8_thr0`:

- baseline: USD62.3573 end, 7.6807% geo/month, 10.8159% DD, 222 trades, 0.2401R AvgR, PF 1.5579;
- DeepMLP keep50: USD60.4393, 7.1215%, 7.3551% DD, 146 trades, 0.3329R, PF 1.8037;
- CatBoost/ExtraTrees/LinearSVM/simple voting rejected as primary binary gates.

V31.1 tape SHA:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

## Accepted V32 development evidence

Uploaded V32 ZIP SHA-256:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Six complete exact-MT5 passes: baseline, DeepMLP keep50/60/70/80/90. All compile 0/0, MT5 rc=0, tester-only, no native/external broker orders, continuous USD40.

V32 source SHA:

`ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`

V32 nested causal tape SHA:

`8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`

Primary `adaptive_ewma_hl8_thr0`:

- baseline: USD62.3573 end, geo 7.6807%, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579, turnover 1045.67x/$40;
- **keep60**: USD62.1444, geo 7.6193%, DD 7.3639%, 153 trades, AvgR 0.3250R, PF 1.8326, turnover 764.42x/$40;
- keep70: USD60.9569, geo 7.2738%, DD 9.0562%;
- keep80: USD60.9896, geo 7.2834%, DD 9.9301%;
- keep50: USD60.4393, geo 7.1215%, DD 7.3551%;
- keep90: USD53.2804, geo 4.8942%, DD 16.3281%.

keep60 is the frozen primary threshold lead: only ~0.34% lower ending capital than baseline while max DD falls ~31.9%, trades ~31.1%, turnover ~26.9%; AvgR rises ~35.4% and PF ~17.6%.

It does not solve the return target: keep60 has 1/6 months >=15% versus baseline 2/6; no V32 mode reaches 15% geometric/month.

Nested score masks do not produce nested realized trade sets because filtering changes subsequent adaptive/one-position state. Never replace exact MT5 replay with subset arithmetic.

Exploratory only: `adaptive_ewma_hl12_thr0p05 + keep80` ends USD66.6393, geo 8.8792%, DD 7.0573%, AvgR 0.3128R, PF 1.8086. This is post-hoc and not primary confirmation evidence.

Read:

- `docs/research/v32_deep_mlp_keep_sweep_plan.md`
- `docs/research/v32_deep_mlp_keep_sweep_results.md`

## Current work split

### Frozen confirmation lane

Freeze `adaptive_ewma_hl8_thr0 + DeepMLP keep60`. Do not retune February-July 2026. Require a genuinely fresh complete chronological holdout versus frozen baseline before any promotion claim.

### V33 development lane

Move neural research from a global binary rejector toward a bounded policy controller:

- shared neural targets: expected R, MFE, MAE, giveback;
- soft-risk actions bounded at <=1.00% stop-risk;
- bounded exit routing using existing fixed-4R and previously studied profit-protection families;
- source/regime conditioning;
- complementary independent opportunity generation/allocation;
- exact MT5 remains the final economic judge.

Read `docs/research/v33_neural_policy_controller_plan.md`.

Do not increase risk/leverage to force the aspirational 15% monthly target. PAPER/DEMO only after gates. LIVE remains forbidden.

Historical runner lessons remain active: missing helpers, `dt.minute -> dt.min`, stale/corrupt recovery blobs, MSYS path-conversion bugs, UTF-16 compile logs, and Bash `set -u` dependent-local declarations must not be reintroduced.
