# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Research/Strategy Tester dùng virtual books, không Martingale/grid/doubling, không secrets/logins. Stop-risk research ceiling vẫn 1.00% mỗi trade.

## Accepted V30 data/runtime

V30 `MlDlFeatureLakeV1.mq5` source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows MetaEditor đã PASS `0 errors / 0 warnings`.

Accepted 18-month lake sau canonical trim/stitch:

- 35,344 M15 rows, 2025-02 → 2026-07;
- 136 raw features;
- 0 duplicate timestamps, 0 NaN, 0 Inf;
- 864 monthly-summary rows = 18 × 12 × 4;
- 28,128 trades toàn catalog;
- 7,483 `norm10k_r0p5_continuous` trades;
- summary ↔ ledger counts khớp, PnL/AvgR chỉ lệch CSV rounding.

Mandatory causal contract:

`feature_available_time = bar_features.time + 15 minutes`

Trade entry chỉ được dùng feature row có `feature_available_time <= entry_time`. Mọi experiment bỏ +15 phút là invalid leakage.

Heavy duplicate-opportunity confound vẫn phải được kiểm soát: 7,483 norm-book candidate-trades chỉ tương ứng 1,972 unique `(entry_time,direction)` opportunities; ~79.3% groups duplicated.

## V30 model conclusions

- win/loss/tail classification: rejected;
- static MLP: no robust uplift;
- GRU/causal TCN/PatchTransformer: no robust uplift;
- universal common market-state gate: chưa established;
- expected-R filtering + family/candidate context là lead tốt hơn direct classification.

Không model V30 nào được promote.

## V31 AI Router Lab — current research branch

Primary branch:
`agent/v31-ai-router-mt5-gate`

V31 được tạo để test trực tiếp nonlinear AI inside MT5, không chỉ offline dataframe scoring.

Catalog V31:

- 12 V30 baseline candidates giữ nguyên;
- candidate 12: `ai_nn_distilled_router`;
- candidate 13: `ai_linear_svr_router`;
- candidate 14: `ai_rff_kernel_router`;
- total = 15 candidates × 4 virtual books = 60 books.

AI input contract = 73 dimensions:

- 42 causal bar/market/expert-state fields;
- 19 safe entry-state fields;
- 12 candidate one-hot fields.

Frozen models:

1. Distilled DNN: `73 -> 96 -> 48 -> 24 -> 1`, ReLU, threshold `0.15744125843048096`.
2. Linear SVR expected-R control, threshold `-0.10337714735872365`.
3. RBF approximation teacher: 384 random Fourier features, gamma `0.004`, weighted Ridge, threshold `0.16803128`.

Training labels end before `2025-07-01`. July-2025 scores only are used to freeze thresholds. MT5 development/implementation interval is `2025-08-01 -> 2026-08-01`.

V31 deployment SHA-256:

- `V31AiRouterLabV1.mq5`: `cef304997fc342740c15101d64a610d6265a4835a4cb601a741113868a078f0f`
- `V31AiModelData.mqh`: `44c8edd55fc5a1b18fe5ec5d0a3454d95600f23d8c3f06ae6048e1c4d16211f3`
- `V31AiNnWeights.mqh`: `6e977ff55b9ae7ddf5ffa8103642fa882a6a47cdc2ef0f9fe6f16582e242c8f3`
- `V31AiSvmWeights.mqh`: `8b94f800959b32465302a8eb50c58fff82071368cf3310788c4c3fdb9cebf650`
- `V31AiRffWeights.mqh`: `36905a57761ec216e2ca92ac87a2a9a23bd241bace4a86a87124ccb6f2ffe710`
- packed release tar.gz SHA: `fbcf83f04d2e8661bc36ebba2bea66c172cbc4c08d4b13e74df45a8b9174b9e7`
- start state after Jul-2025 SHA: `5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`

Local release QA before Windows:

- deployment/reconstruction hash checks PASS;
- manual DNN/SVR/RFF inference parity checks PASS in development;
- repo artifact tests 6/6 PASS after packed-release refactor;
- Bash runner `bash -n` PASS;
- static safety scan has no native/external order path.

Windows V31 compile/tester evidence is still PENDING. Do not claim V31 compile PASS or MT5 performance until user returns the generated ZIP.

## Economic target

Research target from user:

- starting capital: `$40`;
- aspirational target: `15%` average monthly return;
- risk ceiling: max 1.00% per trade.

Existing V30 `$40 / 1%` `adaptive_ewma_hl8_thr0` baseline averages about 7.45%/month over accepted 18-month monthly-reset evidence and reaches 15% in only 5/18 months. Therefore current accepted system does NOT meet 15%/month.

The V31 gate evaluates the primary `usd40_r1p0_cent` book and also checks 0.5%/0.75% robustness. Mean >=15% alone is insufficient: median, hit-rate, worst month, MTM drawdown, volume/margin rejects, turnover and month concentration must also be acceptable.

## V31 offline evidence — development only

Before MT5 implementation, frozen DNN candidate-trade scoring over Aug-2025→Jul-2026 showed approximately:

- coverage 59.4%;
- selected AvgR 0.318R vs ~0.189R baseline;
- selected sumR retention ~99.95%;
- paired-month uplift interval roughly `[+0.043R,+0.196R]`.

RFF teacher was also positive; linear SVR was weaker. These are not `$40` MT5 performance numbers and cannot establish the 15% target because opportunity duplication, overlapping catalog paths, virtual sizing, margin/volume rejects and full tester exit semantics must be evaluated inside MT5.

## Current next gate

Run exactly one V31 Strategy Tester batch:

- `XAUUSDm`, M15;
- MT5 `Every tick` generated tester ticks;
- `2025-08-01 -> 2026-08-01`;
- 15 candidates × 4 virtual books;
- expected 720 monthly-summary rows;
- compile gate must be `0 errors / 0 warnings` before tester launches.

The runner backs up/restores the user's current adaptive state and creates one ZIP. If a complete checkpoint exists it packages without rerunning MT5.

After ZIP upload, formal evaluation will compare DNN, linear SVR, RFF router and best baseline on `$40 / 1%`, plus risk robustness at 0.5%/0.75%.

This historical interval is an implementation/development backtest because it has already been inspected offline; it is not pristine confirmation. A future untouched holdout remains required before PAPER/DEMO. LIVE remains forbidden.

## Evidence / runtime

- `docs/research/v31_ai_router_offline_selection_and_mt5_gate.md`
- `models/v31_ai_router/MODEL_META.json`
- `models/v31_ai_router/MODEL_RELEASE.json`
- `models/v31_ai_router/release/v31_model_release.tar.gz.b64`
- `runtime/v31_ai_router_mt5_gate/RUN_V31_AI_ROUTER_MT5_GIT_BASH.sh`
- `tests/test_v31_ai_router_artifacts.py`

Historical V29/V30 compile/release incidents remain lessons learned; do not reuse broken stale artifacts.
