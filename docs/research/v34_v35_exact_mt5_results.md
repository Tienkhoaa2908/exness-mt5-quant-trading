# V34/V35 exact-MT5 results

Date: 2026-08-20

## Accepted artifact

Uploaded ZIP SHA-256:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

ZIP integrity PASS, 24 files. V34 and V35 checkpoints both contain `DONE.txt` and `MT5_DONE.txt`.

V34 compile: `0 errors, 0 warnings`.
V35 compile: `0 errors, 0 warnings`.
Both MT5 Strategy Tester runs completed and were collected successfully.

Safety manifest gates for both runs:

- `tester_only=1`
- `native_broker_orders=0`
- `external_broker_orders=0`
- `continuous_usd40=1`
- XAUUSDm / M15
- stop-risk ceiling unchanged; no Martingale/grid/loss doubling.

## Integrity QA

V34:

- 12 months, 17 candidates x 4 books = 816 monthly rows;
- 34,508 trade-ledger rows;
- 266,613 intra-trade telemetry rows;
- monthly-summary vs ledger trade-count mismatches: 0;
- max absolute net-PnL reconciliation error: ~6e-6;
- max absolute AvgR reconciliation error: ~6e-6.

V35:

- 6 months, 18 candidates x 4 books = 432 monthly rows;
- 16,917 trade-ledger rows;
- 129,107 intra-trade telemetry rows;
- monthly-summary vs ledger trade-count mismatches: 0;
- max absolute net-PnL reconciliation error: ~6e-6;
- max absolute AvgR reconciliation error: ~6e-6.

Cross-run reproducibility check: for the 17 candidates common to V34 and V35, every norm-book trade from 2026-02 through 2026-07 matches exactly on entry time, exit time, direction and `r_multiple`. This confirms adding the V35 candidate did not perturb the other virtual books.

V34 norm-book telemetry covers 9,077 / 9,457 trades (95.98%). The uncovered 380 trades exited before the first post-entry M15 telemetry point. Median covered sequence length = 9 rows; p75=20, p90=32, p95=44, max=422.

## V34 specialist results — continuous USD40 book

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | 107.43 | 8.58% | 9.90% | 563 | 0.215R | 1.501 |
| **v34_smc_ict_causal** | **66.83** | **4.37%** | **15.58%** | **1,077** | **0.066R** | **1.108** |
| v34_specialist_confluence | 56.60 | 2.93% | 21.30% | 860 | 0.043R | 1.094 |
| v34_price_action_causal | 50.86 | 2.02% | 20.72% | 1,158 | 0.028R | 1.051 |
| v34_tick_microstructure_proxy | 35.24 | -1.05% | 35.25% | 620 | -0.044R | 0.956 |
| v34_wyckoff_proxy_causal | 25.53 | -3.67% | 43.53% | 527 | -0.128R | 0.798 |

SMC/ICT is the only new standalone specialist with a material positive 12-month result, but it is not promotion-ready: it has much higher turnover, weaker AvgR/PF and larger DD than the current adaptive baseline. Its monthly return correlation with `adaptive_ewma_hl8_thr0` is low (~0.13), so it remains useful as an independent-alpha research lane rather than as a primary replacement.

Price Action is only marginally positive after costs/execution. Wyckoff proxy and L1/tick-path microstructure proxy are rejected in current form. The microstructure result reinforces that L1 proxy features must not be presented as true order flow.

## V35 all-expert AI router — REJECT

V35 exact-MT5 comparison, continuous USD40 book, 2026-02 through 2026-07:

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | 62.36 | +7.68% | 10.82% | 222 | +0.240R | 1.558 |
| **v35_ai_all_expert_meta_router** | **24.49** | **-7.85%** | **39.71%** | **571** | **-0.105R** | **0.788** |

The V35 router lost money in every test month. Decision: **REJECT as a trading candidate**. Do not tune its threshold/model complexity on the same six months.

The current implementation used ExtraTrees + HistGradientBoosting + MLP with inverse opportunity multiplicity and previous-month median calibration. Calibration MAE remained approximately 0.93R-1.13R by month, which is too large relative to the edge being routed. The exact-MT5 failure demonstrates that generic cross-expert expected-R ranking is not currently reliable.

## Decisions

1. Keep `adaptive_ewma_hl8_thr0 + DeepMLP keep60` as the frozen risk-efficiency challenger from V32; do not retune February-July 2026.
2. Reject V35 generic all-expert router.
3. Keep SMC/ICT as a separate specialist research lane. Future work should focus on causal quality/regime filtering and aggregate-risk-aware blending, not simply adding its full 1% risk on top of the baseline.
4. Reject current Wyckoff and microstructure proxies; redesign features before any retest.
5. Use V34 intra-trade telemetry for V36 true sequence exit research. V36 remains diagnostic; only a stable sequence signal may be converted into an exact-MT5 exit-policy test.
6. The aspirational 15% geometric/month objective remains unmet. Do not increase per-trade stop risk above 1.00% to force the target.

## Next technical focus

- V36: GRU / true causal TCN / Transformer on intra-trade sequences with causal market-state joins.
- Primary exit target should include **future incremental R from the current mark**, not only final R, because the action question is hold/protect/exit.
- Add candidate identity and valid-sequence mask to avoid mixing policy families blindly.
- Fit scaling only on real train timesteps; padding must not contaminate train statistics.
- Any useful V36 signal returns to a tester-only MT5 EA for exact economics.
- In parallel, build a dedicated SMC quality filter rather than reviving the failed generic V35 router.

LIVE trading remains forbidden.
