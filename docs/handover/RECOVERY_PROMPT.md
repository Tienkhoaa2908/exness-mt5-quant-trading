# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch: `agent/v30-ml-dl-feature-lake`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Do not remove tester/live guards.
- No Martingale/uncontrolled grid/loss doubling.
- Do not commit/request login/password/token/secret.
- Do not call native/external broker orders for research screening.
- Stop-risk research ceiling: 1.00%/trade.

## Accepted V30 source/data

Accepted V30 `MlDlFeatureLakeV1.mq5` SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile: `0 errors / 0 warnings`.

Canonical 18m M15 lake:

- 35,344 unique rows, 2025-02 through 2026-07;
- 136 raw fields;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in accepted raw lake;
- 28,128 total ledger trades;
- state continuous across three chunks.

Critical causal rule:

`feature_available_time = bar_features.time + 15 minutes`

Trade/current-bar decisions use only features available by decision time. Across session gaps, score tape is keyed by actual current M15 bar start and uses an as-of availability join.

## Accepted V31.1 exact-MT5 milestone

User-uploaded V31.1 bundle SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

Seven complete Strategy Tester passes are accepted:

- baseline
- CatBoost
- ExtraTrees
- DeepMLP 64-32-16
- LinearSVM / LinearSVR
- CatBoost AND ExtraTrees
- majority 2-of-4

All passes compile 0/0, MT5 rc=0, collection PASS, tester-only, no native/external broker orders, continuous USD40.

Common exact contract:

- XAUUSDm M15;
- 2026-02-01 -> 2026-08-01;
- Deposit=USD40;
- `usd40_r1p0_cent_continuous`;
- <=1.00% risk target per trade;
- leverage assumption 1:200;
- identical state-after-Jan restored before each pass;
- month-end liquidation retained.

V31.1 tape SHA-256:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

Primary candidate `adaptive_ewma_hl8_thr0`:

- baseline: end USD62.3573, geo 7.6807%/month, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579;
- DeepMLP: end USD60.4393, geo 7.1215%/month, DD 7.3551%, 146 trades, AvgR 0.3329R, PF 1.8037;
- CatBoost: end USD51.2744, geo 4.2254%;
- CB+ET: end USD47.3229, geo 2.8415%;
- majority: end USD46.1485, geo 2.4117%;
- ExtraTrees: end USD45.6841, geo 2.2392%;
- LinearSVM: end USD44.0550, geo 1.6223%.

V31.1 decision:

- baseline = return winner;
- DeepMLP = useful quality/risk signal but 50%-score binary gate overfilters profitable breadth;
- CatBoost / ExtraTrees / LinearSVM / voting = reject as primary binary gates;
- 15% geometric/month target FAIL for all modes;
- never increase risk above 1.00% merely to force target.

Analyzer note: trade-ledger PnL field is `total_pnl`. The original report printed PF NaN because it looked for `net_pnl`; repaired analyzer now uses `total_pnl` with guarded legacy fallback.

Read:

- `docs/research/v31_1_exact_mt5_usd40_results.md`
- `scripts/analyze_v31_1_mt5_usd40.py`

## V32 current next action

Next gate is **V32 DeepMLP keep-rate exact-MT5 sweep**. Do not add more model families before this bounded test.

Purpose: bracket how destructive the binary DeepMLP threshold is using the same model at nested keep rates:

- baseline
- keep50
- keep60
- keep70
- keep80
- keep90

This reuses February-July 2026 and is explicitly a **development sweep, not fresh confirmation**.

V32 source SHA-256:

`ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`

V32 nested tape SHA-256:

`8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356`

Starting state SHA-256:

`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`

Runtime files:

- `runtime/v32_mlp_keep_sweep/BOOTSTRAP_V32_ONE_SHOT_GIT_BASH.sh`
- `runtime/v32_mlp_keep_sweep/RUN_V32_DEEP_MLP_KEEP_SWEEP_GIT_BASH.sh`
- `runtime/v32_mlp_keep_sweep/state_after_chunk2.csv`
- `scripts/build_v32_deep_mlp_keep_source.py`
- `scripts/build_v32_deep_mlp_keep_tape.py`
- `scripts/analyze_v32_deep_mlp_keep_mt5.py`
- `docs/research/v32_deep_mlp_keep_sweep_plan.md`

The V32 runner should reuse the existing V31.1 pinned Python environment when available, compile every EA at 0 errors / 0 warnings, restore identical state before each mode, checkpoint completed MT5 modes, and emit one final ZIP.

After V32:

1. if a bounded keep-rate materially improves the baseline-vs-quality tradeoff, freeze it;
2. do not tune February-July again;
3. require a genuinely fresh chronological holdout before promotion claims;
4. if binary gating still fails, shift neural research toward causal risk/exit control plus independent opportunity generation/allocation;
5. prior profit-protection evidence already says exit-only is insufficient;
6. PAPER/DEMO only after gates; LIVE remains forbidden.

Historical V29 runner/artifact incidents remain lessons learned: missing helpers, `dt.minute -> dt.min`, stale/corrupt recovery blobs, MSYS path-conversion bugs, and Bash `set -u` dependent-local declarations must not be reintroduced.
