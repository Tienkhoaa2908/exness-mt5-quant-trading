# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/grid/loss doubling.
- Research stop-risk ceiling: 1.00%/trade.
- Không native/external broker orders trong current research gates.
- PAPER/DEMO only after gates. LIVE remains forbidden.

## Accepted V30 canonical data

Accepted `MlDlFeatureLakeV1.mq5` SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Canonical M15 lake:

- 35,344 unique rows, 2025-02-01 through 2026-07-31;
- 136 raw fields;
- 0 duplicate timestamps;
- 0 NaN/Inf in accepted raw lake;
- 28,128 trade-ledger rows;
- adaptive state continuous.

Mandatory stitch contract:

- chunk1 `[2025-02-01, 2025-08-01)`;
- chunk2 `[2025-08-01, 2026-02-01)`;
- chunk3 `[2026-02-01, 2026-08-01)`.

Never concatenate the raw chunk rows globally without first applying these half-open boundaries; each later chunk contains a pre-roll row.

Mandatory causal contract:

`feature_available_time = bar_features.time + 15 minutes`

All inference uses latest features satisfying `feature_available_time <= decision_time`.

## Accepted V31.1 / V32 exact-MT5 gate

V31.1 ZIP SHA:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Primary `adaptive_ewma_hl8_thr0`, Feb-Jul 2026, continuous USD40:

| Mode | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 |
| **DeepMLP keep60** | **62.1444** | **7.6193%** | **7.3639%** | **153** | **0.3250R** | **1.8326** |

Freeze `adaptive_ewma_hl8_thr0 + DeepMLP keep60` for future genuinely fresh confirmation. Do not retune Feb-Jul 2026.

## Accepted V33 entry-snapshot multi-task diagnostic

ZIP SHA:

`16db78c40543495c790d83019999169d566206a591cc4ec570c6b7056df8fefa`

Entry-snapshot neural prediction of future path was weak: expected-R Spearman +0.0249; MFE -0.0050; adverse/MAE -0.0366; giveback -0.0132. Decision: do not enlarge entry MLPs; sequence telemetry is required for exit control.

## Accepted V34 Parallel Alpha Lab exact-MT5 evidence

V34/V35 ZIP SHA:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Integrity:

- V34/V35 compile 0/0;
- exact MT5 complete;
- tester-only, no native/external orders;
- V34 816 monthly rows, 34,508 trades, 266,613 intra-trade M15 telemetry rows;
- summary/ledger counts reconcile;
- all 17 common V34/V35 candidates reproduce exactly over the overlap period.

Continuous USD40 V34, 12 months:

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | 107.43 | 8.58% | 9.90% | 563 | 0.215R | 1.501 |
| **v34_smc_ict_causal** | **66.83** | **4.37%** | **15.58%** | **1,077** | **0.066R** | **1.108** |
| v34_specialist_confluence | 56.60 | 2.93% | 21.30% | 860 | 0.043R | 1.094 |
| v34_price_action_causal | 50.86 | 2.02% | 20.72% | 1,158 | 0.028R | 1.051 |
| v34_tick_microstructure_proxy | 35.24 | -1.05% | 35.25% | 620 | -0.044R | 0.956 |
| v34_wyckoff_proxy_causal | 25.53 | -3.67% | 43.53% | 527 | -0.128R | 0.798 |

SMC is a positive but weak/high-turnover specialist. Its monthly-return correlation to the adaptive baseline is low (~0.13), so it remains an independent-alpha research lane. Price Action is marginal. Current Wyckoff and L1/tick-path microstructure proxies are rejected. Never call the latter true L2/L3 order flow.

## V35 generic AI all-expert router — REJECTED

Feb-Jul 2026, continuous USD40:

- baseline: USD62.36 end, +7.68% geo/month, DD 10.82%, 222 trades, +0.240R, PF 1.558;
- V35 router: USD24.49 end, -7.85% geo/month, DD 39.71%, 571 trades, -0.105R, PF 0.788.

The generic router lost money in 6/6 months. Do not retune its thresholds or make the same router deeper on Feb-Jul.

## Accepted V36 true intra-trade sequence-DL diagnostic

Uploaded V36/V37 ZIP SHA:

`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

V36 used the corrected canonical 35,344-row V30 stitch, true sequence masking and chronological folds for Feb-Jul 2026.

Mean chronological metrics:

| Model | Future-delta Spearman | Final-R Spearman | Hold AUC | Protect AUC |
|---|---:|---:|---:|---:|
| GRU48 | +0.0187 | +0.5246 | 0.6426 | 0.6150 |
| causal TCN48 | -0.0116 | +0.4767 | 0.6152 | 0.5524 |
| **Transformer48x2** | **+0.0403** | **+0.5148** | **0.6757** | **0.6771** |

Interpretation:

- direct future-incremental-R regression remains too weak for continuous expected-R control;
- high final-R correlation is partly mechanical because current unrealized R already contains information about final R;
- Transformer hold/protect classification is materially stronger and stable: both AUCs >0.5 in all 6 months.

Development-only first-trigger diagnostic: among trade paths where current unrealized R is at least +1.0R and Transformer `p_hold < 0.10`, 603 first triggers occur. The original final exit is on average 0.205R below the trigger mark; 79.3% of triggered trades finish below the trigger mark; mean avoided giveback is positive in all six inspected months. This is not PnL evidence because intervening exits change subsequent state/path.

Decision: Transformer sequence classification is **promising enough for one bounded exact-MT5 exit-policy test**. No promotion before exact replay.

Read `docs/research/v36_v37_results.md`.

## V37 dedicated SMC quality gate — REJECTED / redesign

Same uploaded ZIP SHA as V36.

OOS Feb-Jul 2026, prior-month keep60-style threshold:

- HistGB selected AvgR -0.0497R, uplift -0.0679R, 1/6 uplift-positive months;
- ExtraTrees selected AvgR -0.0587R, uplift -0.0768R, 0/6 uplift-positive months;
- MLP selected AvgR +0.0254R vs baseline +0.0181R, but total selected sumR only +3.44R vs baseline +10.74R and monthly stability is insufficient.

Decision: do not send current V37 generic SMC filter to MT5. If SMC continues, use regime/direction/structure-specific redesign rather than threshold tuning.

## Current next gate — V38 neural exit/protection exact MT5

The next economic gate should use the sequence classifier only after a trade is already profitable; no risk increase. Candidate hypothesis:

- apply to the adaptive primary path;
- require current unrealized R >= +1.0R;
- very low Transformer hold probability triggers a bounded profit-protection action;
- compare against the exact baseline under the same USD40 continuous book, <=1% stop-risk and execution mechanics;
- development sweep may bracket a small fixed set of low `p_hold` thresholds, but any winner must be frozen before fresh confirmation.

MQL5 natively supports ONNX model execution and Strategy Tester validation, so V38 may use tester-only ONNX inference rather than approximating the sequence model with subset arithmetic.

## Decision stack

- Frozen risk-efficiency challenger: `adaptive_ewma_hl8_thr0 + DeepMLP keep60`.
- Baseline remains stronger in absolute return on the viewed period.
- V35 generic router: reject.
- SMC/ICT: positive independent specialist, research-only.
- V37 current SMC ML gate: reject/redesign.
- Price Action: marginal.
- Wyckoff proxy: reject.
- L1 microstructure proxy: reject/redesign.
- V36 Transformer sequence classifier: promising development signal; next exact-MT5 exit gate.
- Aspirational 15% geometric/month target remains unmet. Never raise stop-risk above 1.00% to force it.
