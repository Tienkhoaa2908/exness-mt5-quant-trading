# Profit Protection Lab V1 — analysis

Date: 2026-08-16

Uploaded bundle SHA-256: `13b61b630046fde11ed05b252781cc08f8cc90e56041cdccd284722300345731`.

Internal bundle hashes: **PASS (22/22)**. Windows MetaEditor compile log: **0 errors, 0 warnings**. Three six-month chunks completed, covering 18 independent calendar months from 2025-02 through 2026-07. The experiment remained tester-only with virtual books and `external_broker_orders=0`.

## Main finding

The user's visual diagnosis was materially correct: the fixed 2R control often allowed a trade that had reached meaningful open profit to finish non-positive. Profit protection can eliminate that particular failure mode, but exit logic alone does **not** produce a robust 15–20% monthly profile on USD 40.

### USD 40 at the 1.00% research ceiling

| Candidate | Median monthly return | Positive months | >=15% | Worst | Best | Max MTM DD | Median PF | Reached >=1R then <=0R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EMA H1 + lock 50% of peak after +1R, TP4R | **+6.32%** | 13/18 | 0/18 | -4.59% | +14.74% | 9.02% | 1.476 | **0/324** |
| EMA H1 + trail 0.75R after +1R, TP3R | +5.93% | 12/18 | 0/18 | -3.36% | +13.60% | 9.18% | 1.482 | **0/337** |
| EMA H1 + lock +0.5R at +1R | +4.71% | 14/18 | 1/18 | -4.78% | +15.44% | 9.07% | 1.429 | **0/336** |
| EMA H1 fixed 2R control | +3.54% | 14/18 | 1/18 | -6.80% | +15.20% | 10.96% | 1.274 | **71/271 (26.2%)** |
| Trend H1 + lock 50% of peak after +1R, TP4R | +3.78% | 13/18 | 0/18 | -6.32% | +13.51% | 11.30% | 1.397 | **0/309** |
| Trend H1 fixed 2R control | +2.32% | 12/18 | 2/18 | -8.27% | +20.93% | 14.01% | 1.168 | **83/298 (27.9%)** |

The strongest practical exit improvement is `ema_h1_lock_50pct_peak_after_1r_tp4r`. Relative to the EMA fixed-2R USD40/1% control, median monthly return increased from 3.54% to 6.32% while observed max MTM DD fell from 10.96% to 9.02%. The count of trades that reached at least +1R and later finished non-positive fell from 71 to zero.

However, 6.32% median monthly return is only about **+$2.53 on a $40 account**, still far below the practical aspiration of +$6 to +$8 per month. No profit-protection candidate reached >=15% in a majority of months; the top peak-lock candidate reached it in 0/18 months.

## Important nuance

On the normalized continuous USD10k/0.5% book, fixed EMA 2R retained higher average R per trade than several protected variants. Peak-lock nevertheless improved median monthly return because it shortened holding periods, recycled capital sooner, prevented large giveback after +1R, and created more subsequent entry opportunities.

Therefore the remaining bottleneck is **opportunity-adjusted alpha**: the system needs more independent positive-expectancy opportunities per month without increasing stop-risk above the current ceiling.

## Regime stability

The EMA peak-lock candidate remained materially healthier than fixed EMA in 2026:

- EMA peak-lock median USD40/1% return: about +6.61% in 2025 and +4.91% in 2026.
- EMA fixed-2R median: about +5.11% in 2025 but only +0.75% in 2026.

Trend remained more regime-sensitive. Trend peak-lock median USD40/1% return was about +6.90% in 2025 but approximately flat in 2026. Trend is therefore retained as a challenger/source of distinct signals, not the primary return engine.

## Partial-profit result

The partial-50% candidate was not promoted. Tiny-capital lot granularity caused partial-reject events (69 EMA, 47 Trend in the USD40/1% books), and the current account mode observed in MT5 is Netting. Any future native partial exit must be account-mode-aware and cannot assume hedging-style partial-close helpers.

## Decision

1. Keep risk ceiling at 1.00% per trade. Do not use leverage/risk escalation as a substitute for missing expectancy.
2. Promote `ema_h1_lock_50pct_peak_after_1r_tp4r` as the **virtual exit champion** only; it is not yet native-deployable.
3. Do not spend another cycle micro-optimizing stop/TP numbers. Exit protection has addressed the specific giveback failure mode but did not reach the monthly return objective.
4. The next research gate expands **independent signal opportunity** using strategy families that already had positive prior V4 evidence: RSI2 trend reversion and fast MACD trend, alongside EMA H1 and Trend H1.
5. Fusion candidates are one-position-at-a-time on the same symbol, making the research design compatible with a future Netting implementation and ensuring open stop-risk never stacks above the selected per-trade risk budget.
6. All fusion candidates use the same peak-lock exit (2 ATR initial stop, TP4R, after +1R lock 50% of peak R) so the experiment isolates entry/opportunity effects.

## Next gate

`OpportunityFusionLabV1`: 18 independent monthly resets, three six-month MT5 chunks, 10 candidates x four books, tester-only virtual orders, no CTrade and no external broker orders. Any winner must pass native MT5 validation before promotion.