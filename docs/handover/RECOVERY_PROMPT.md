# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch: `agent/v31-ai-router-mt5-gate`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/uncontrolled grid/doubling.
- Không secrets/login/token/account IDs.
- Stop-risk research ceiling = 1.00% per trade.
- V31 is Strategy Tester / virtual-book research only.

## Accepted V30 foundation

Accepted V30 source SHA:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile accepted: `0 errors / 0 warnings`.

Canonical 18m lake:

- 35,344 M15 bars, 2025-02→2026-07;
- 136 raw fields;
- 0 duplicates / NaN / Inf;
- 864 summary rows;
- 28,128 ledger trades;
- 7,483 norm-book trades.

Critical timing rule:

`feature_available_time = bar_features.time + 15 minutes`

Never join trade entry against raw same-timestamp bar feature without this availability shift.

Duplicate opportunity rule: 7,483 norm candidate-trades correspond to only 1,972 unique `(entry_time,direction)` opportunities; ~79.3% groups are duplicated. Unweighted catalog ML metrics are exploratory.

V30 decisions: direct classification rejected; MLP/GRU/TCN/PatchTransformer did not establish robust economic uplift; expected-R filtering with candidate/family context is the useful lead.

## V31 frozen AI router

Branch:
`agent/v31-ai-router-mt5-gate`

V31 MQL catalog = original 12 baselines + 3 AI synthetic routers:

- `ai_nn_distilled_router` (CI12)
- `ai_linear_svr_router` (CI13)
- `ai_rff_kernel_router` (CI14)

Total = 15 candidates × 4 virtual books.

Frozen 73-D input = 42 causal bar/state + 19 safe entry-state + 12 candidate one-hot.

Models:

1. DNN `73-96-48-24-1` ReLU, threshold `0.15744125843048096`.
2. Linear SVR, threshold `-0.10337714735872365`.
3. RFF RBF approximation, 384 components, gamma 0.004 + weighted Ridge, threshold `0.16803128`.

Training labels end before 2025-07-01. July-2025 scores only calibrate thresholds. No threshold is tuned inside MQL.

Deployment hashes:

- MQL source `cef304997fc342740c15101d64a610d6265a4835a4cb601a741113868a078f0f`
- model data `44c8edd55fc5a1b18fe5ec5d0a3454d95600f23d8c3f06ae6048e1c4d16211f3`
- NN weights `6e977ff55b9ae7ddf5ffa8103642fa882a6a47cdc2ef0f9fe6f16582e242c8f3`
- SVM weights `8b94f800959b32465302a8eb50c58fff82071368cf3310788c4c3fdb9cebf650`
- RFF weights `36905a57761ec216e2ca92ac87a2a9a23bd241bace4a86a87124ccb6f2ffe710`
- packed tar.gz `fbcf83f04d2e8661bc36ebba2bea66c172cbc4c08d4b13e74df45a8b9174b9e7`
- Jul-2025 start state `5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`

Local artifact test after packing: 6/6 PASS. Bash syntax PASS. Windows V31 compile/tester remains PENDING until user runs the one-shot Git Bash gate.

## User economic target

Research target:

- starting virtual capital `$40`;
- aspirational 15% average monthly return;
- max 1.00% risk/trade.

Do not guarantee the return and do not increase risk above 1% to force it.

Existing accepted V30 `$40 / 1%` adaptive-HL8 baseline averages about 7.45% monthly and hits >=15% in only 5/18 months, so target is not currently met.

Offline V31 DNN development result (~59.4% coverage, ~0.318R selected AvgR) is only model-selection evidence; it is not an MT5 `$40` return result.

## Exact next action

Do not start new offline retuning before the implementation gate.

Run the repo one-shot runner:

`runtime/v31_ai_router_mt5_gate/RUN_V31_AI_ROUTER_MT5_GIT_BASH.sh`

It must:

1. reconstruct and SHA-verify the packed frozen release;
2. locate accepted MT5 data folder from the exact V30 source SHA;
3. copy V31 MQL + model headers;
4. compile and require `0 errors / 0 warnings`;
5. backup current Common Files adaptive state;
6. load exact state after Jul-2025;
7. run `XAUUSDm M15`, MT5 `Every tick` generated ticks, 2025-08-01→2026-08-01;
8. collect V31 locator, monthly summary, trades, bar features, manifest, compile log, start/final state;
9. require exactly 720 monthly-summary rows = 12 × 15 × 4;
10. restore user state and create one upload ZIP.

If runner fails before MT5 starts, fix the wrapper/compile issue rather than asking for manual tester work. If it completes MT5 and checkpoint is complete, a rerun must package from checkpoint instead of rerunning tester.

## Evaluation after ZIP upload

Primary book: `usd40_r1p0_cent`.

Compare DNN, linear SVR, RFF and best baseline using:

- 12 monthly returns;
- mean/median monthly return;
- months >=15%;
- positive months;
- worst month;
- max monthly MTM DD;
- trades, profit factor, AvgR;
- volume rejects and 1:200 margin rejects;
- turnover and concentration;
- robustness at 0.5% and 0.75% risk books.

Mean >=15% alone is not a pass. Risk/breadth/execution quality must also be acceptable.

The Aug-2025→Jul-2026 interval is a development/implementation backtest because offline research has already inspected it. A future untouched chronological holdout remains required before PAPER/DEMO. LIVE remains forbidden.

## Read first on recovery

- `docs/handover/CURRENT_STATE.md`
- `docs/research/v31_ai_router_offline_selection_and_mt5_gate.md`
- `models/v31_ai_router/MODEL_RELEASE.json`
- `models/v31_ai_router/MODEL_META.json`
- `runtime/v31_ai_router_mt5_gate/README_GIT_BASH.md`
- `runtime/v31_ai_router_mt5_gate/RUN_V31_AI_ROUTER_MT5_GIT_BASH.sh`
- `tests/test_v31_ai_router_artifacts.py`

Historical V29/V30 release incidents remain lessons learned only; do not reintroduce stale/broken artifacts.
