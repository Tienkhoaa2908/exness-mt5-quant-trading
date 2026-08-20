# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/grid/loss doubling.
- Research stop-risk ceiling: 1.00%/trade.
- Không native/external broker orders trong current research gates.
- PAPER/DEMO only after gates. LIVE remains forbidden.
- Multiple virtual candidates are research only; any later combined same-symbol controller must keep aggregate stop-risk <=1.00%.

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

Trim each raw chunk before concatenation because later chunks contain pre-roll rows.

Mandatory causal rule:

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

Entry-snapshot future-path prediction was weak: expected-R Spearman +0.0249; MFE -0.0050; adverse/MAE -0.0366; giveback -0.0132. Decision: do not enlarge entry MLPs merely to predict exit path; sequence telemetry is required.

## Accepted V34 Parallel Alpha Lab exact-MT5 evidence

V34/V35 ZIP SHA:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted generated V34 source SHA:

`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

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

SMC remains a positive but weak/high-turnover independent-alpha research lane. Price Action is marginal. Current Wyckoff and L1/tick-path microstructure proxies are rejected; do not label the latter true L2/L3 order flow.

The accepted adaptive baseline also shows a speed/capture bottleneck: median hold ~157.7 minutes, mean hold ~326.7 minutes, average giveback ~1.081R and average MFE ~1.296R. This motivates V38 fast-harvest research without deleting the baseline.

## V35 generic AI all-expert router — REJECTED

Feb-Jul 2026, continuous USD40:

- baseline: USD62.36 end, +7.68% geo/month, DD 10.82%, 222 trades, +0.240R, PF 1.558;
- V35 router: USD24.49 end, -7.85% geo/month, DD 39.71%, 571 trades, -0.105R, PF 0.788.

The generic router lost money in 6/6 months. Do not revive it by threshold/model-size tuning on the same period.

## Accepted V36 true intra-trade sequence-DL diagnostic

Uploaded V36/V37 ZIP SHA:

`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Mean chronological Feb-Jul 2026 metrics:

| Model | Future-delta Spearman | Final-R Spearman | Hold AUC | Protect AUC |
|---|---:|---:|---:|---:|
| GRU48 | +0.0187 | +0.5246 | 0.6426 | 0.6150 |
| causal TCN48 | -0.0116 | +0.4767 | 0.6152 | 0.5524 |
| **Transformer48x2** | **+0.0403** | **+0.5148** | **0.6757** | **0.6771** |

Direct future-delta regression remains weak, while Transformer hold/protect classification is stable: both AUCs >0.5 in all six months.

Development-only clue: current R >= +1R with Transformer `p_hold < 0.10` gives 603 first triggers; original final exit averages 0.205R below the trigger mark, 79.3% finish below it, and mean avoided giveback is positive in all six inspected months. This is not PnL evidence because intervention changes subsequent path/state.

V36 evidence is preserved. V38 does not replace or discard the sequence-AI lane.

## V37 dedicated SMC quality gate — REJECTED / redesign

Current generic keep60-style SMC filter is rejected. HistGB and ExtraTrees reduce AvgR; MLP retains too little SMC sumR with insufficient stability. If SMC continues, redesign by direction/regime/structure rather than threshold tuning.

## Current exact-MT5 gate — V38 Fast Harvest Lab

V38 changes the research objective from merely maximizing terminal R per trade to testing whether XAUUSD economics improve by harvesting the impulse sooner. It is an **incremental exit-only layer** built from the accepted V34 source; the original 17 candidates remain present and the adaptive baseline is a mandatory control.

Six bounded fast-exit clones of `adaptive_ewma_hl8_thr0` are preregistered:

1. `v38_adaptive_fast_tp0p50`: close at +0.50R;
2. `v38_adaptive_fast_tp0p75`: close at +0.75R;
3. `v38_adaptive_fast_tp1p00`: close at +1.00R;
4. `v38_adaptive_fast_gb0p25_after0p75`: after MFE >=0.75R, close while profitable on 0.25R giveback;
5. `v38_adaptive_velocity_decay_after0p50`: causal 60-second R samples; after MFE >=0.50R and current >=0.25R, close on bounded negative/flat velocity decay;
6. `v38_adaptive_timebox30m`: close at first tick at/after 30 minutes.

Hard stop remains before the new fast-exit logic. Existing V34 protection/TP remains active when a fast rule does not fire. Entry/router logic, 2ATR initial stop geometry and book risk fractions are unchanged.

Exact development contract:

- XAUUSDm M15, Every Tick / Model=0;
- 2025-08-01 to 2026-08-01;
- Deposit USD40, leverage 1:200;
- continuous USD40 decision book;
- accepted state-after-chunk1;
- tester-only; no native/external broker orders;
- one V38 MT5 pass evaluates the accepted control plus all fast virtual candidates on the same tick stream.

Before any V38 result is interpreted, the control must reproduce accepted V34: 12 months, 563 trades, final USD107.432645, and the accepted monthly trade-count/ending-capital path.

V38 additionally exports `intra_trade_m1_fast.csv` for the untouched control candidate, using completed prior-minute tick aggregates plus the causally available current mark. It records current R/MFE/MAE/giveback, one-minute delta R, tick count/imbalance, mid-price net/path/range and spread. This extends — not replaces — V36: the next AI controller should focus on 5–15 minute continuation/giveback and speed-aware exits.

Read `docs/research/v38_fast_harvest_lab_plan.md`.

## Decision stack

- Accepted absolute-return baseline: `adaptive_ewma_hl8_thr0`.
- Frozen risk-efficiency challenger: `adaptive_ewma_hl8_thr0 + DeepMLP keep60`.
- V35 generic router: reject.
- SMC/ICT: positive independent specialist, research-only.
- V37 current SMC ML gate: reject/redesign.
- V36 Transformer sequence classifier: preserved promising AI evidence.
- V38 Fast Harvest Lab: current exact-MT5 development gate.
- Aspirational 15% geometric/month target remains unmet. Never raise stop-risk above 1.00% to force it.
