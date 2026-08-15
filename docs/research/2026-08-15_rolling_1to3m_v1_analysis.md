# Rolling 1–3M Validation V1 — analysis

Uploaded bundle SHA-256: `2313416609be0aeeac587e10647864b16d75b5eb818e2923032f181c4298ff1f`.

Integrity: all 93 SHA-256 entries in `bundle_manifest_sha256.txt` matched.

## Native normalized MT5 results

| Window | Strategy | Return | Trades | Win% | PF | MTM DD% |
|---|---|---:|---:|---:|---:|---:|
| 2025_jan_mar | `trend_breakout_20_regime300` | +2.81% | 113 | 36.28% | 1.077 | 6.99% |
| 2025_jan_mar | `ema_pullback_fast10` | +9.46% | 114 | 40.71% | 1.273 | 6.36% |
| 2025_apr_jun | `trend_breakout_20_regime300` | +12.15% | 121 | 41.32% | 1.358 | 4.32% |
| 2025_apr_jun | `ema_pullback_fast10` | +6.84% | 124 | 38.71% | 1.189 | 5.42% |
| 2025_jul_sep | `trend_breakout_20_regime300` | +6.72% | 126 | 37.60% | 1.167 | 7.93% |
| 2025_jul_sep | `ema_pullback_fast10` | +9.69% | 124 | 39.02% | 1.245 | 4.02% |
| 2025_oct_dec | `trend_breakout_20_regime300` | +11.17% | 132 | 39.69% | 1.312 | 6.41% |
| 2025_oct_dec | `ema_pullback_fast10` | +5.35% | 116 | 36.52% | 1.165 | 9.78% |
| 2026_jan_mar | `trend_breakout_20_regime300` | +13.05% | 109 | 41.67% | 1.499 | 3.23% |
| 2026_jan_mar | `ema_pullback_fast10` | +1.98% | 118 | 35.04% | 1.051 | 5.35% |
| 2026_apr_jun | `trend_breakout_20_regime300` | +0.24% | 129 | 33.59% | 0.998 | 6.97% |
| 2026_apr_jun | `ema_pullback_fast10` | -1.25% | 119 | 33.61% | 0.960 | 8.63% |
| 2026_jul_aug | `trend_breakout_20_regime300` | +2.39% | 56 | 37.50% | 1.164 | 4.99% |
| 2026_jul_aug | `ema_pullback_fast10` | +2.60% | 57 | 38.60% | 1.174 | 4.93% |

Trend was positive in 7/7 windows; EMA was positive in 6/7. Median normalized returns were about +6.72% Trend and +5.35% EMA. Neither existing strategy produced a robust 15–20% return in every 1–3 month window.

## USD 40 strict 0.50% Standard-Cent-equivalent replay

| Window | Strategy | $40 profit | Final | Return | Executed/Signals | Closed DD% |
|---|---|---:|---:|---:|---:|---:|
| 2025_jan_mar | `trend_breakout_20_regime300` | +1.20 | $41.20 | +2.99% | 113/113 (100.0%) | 5.63% |
| 2025_jan_mar | `ema_pullback_fast10` | +3.04 | $43.04 | +7.61% | 114/114 (100.0%) | 5.32% |
| 2025_apr_jun | `trend_breakout_20_regime300` | +5.58 | $45.58 | +13.94% | 109/121 (90.1%) | 2.80% |
| 2025_apr_jun | `ema_pullback_fast10` | +2.77 | $42.77 | +6.93% | 112/124 (90.3%) | 2.76% |
| 2025_jul_sep | `trend_breakout_20_regime300` | +2.31 | $42.31 | +5.77% | 126/126 (100.0%) | 5.90% |
| 2025_jul_sep | `ema_pullback_fast10` | +2.98 | $42.98 | +7.44% | 124/124 (100.0%) | 3.06% |
| 2025_oct_dec | `trend_breakout_20_regime300` | +1.33 | $41.33 | +3.33% | 108/132 (81.8%) | 5.93% |
| 2025_oct_dec | `ema_pullback_fast10` | +1.27 | $41.27 | +3.17% | 85/116 (73.3%) | 6.73% |
| 2026_jan_mar | `trend_breakout_20_regime300` | +0.64 | $40.64 | +1.59% | 46/109 (42.2%) | 2.83% |
| 2026_jan_mar | `ema_pullback_fast10` | +0.22 | $40.22 | +0.54% | 33/118 (28.0%) | 2.56% |
| 2026_apr_jun | `trend_breakout_20_regime300` | -0.16 | $39.84 | -0.39% | 67/129 (51.9%) | 5.67% |
| 2026_apr_jun | `ema_pullback_fast10` | -0.00 | $40.00 | -0.00% | 59/119 (49.6%) | 3.09% |
| 2026_jul_aug | `trend_breakout_20_regime300` | +1.33 | $41.33 | +3.33% | 46/56 (82.1%) | 3.53% |
| 2026_jul_aug | `ema_pullback_fast10` | +0.86 | $40.86 | +2.16% | 40/57 (70.2%) | 3.67% |

## Risk allowance overlay on the same frozen native ledger

This is not leverage. It changes allowed stop-risk from 0.50% to 0.75% or 1.00% and therefore can make the minimum cent lot feasible more often.

| Window | Strategy | Return @0.5% | @0.75% | @1.0% | DD @1.0% |
|---|---|---:|---:|---:|---:|
| 2025_jan_mar | `trend_breakout_20_regime300` | +2.99% | +2.61% | +4.12% | 12.77% |
| 2025_jan_mar | `ema_pullback_fast10` | +7.61% | +16.00% | +19.96% | 11.68% |
| 2025_apr_jun | `trend_breakout_20_regime300` | +13.94% | +18.64% | +27.51% | 6.91% |
| 2025_apr_jun | `ema_pullback_fast10` | +6.93% | +13.29% | +18.81% | 9.91% |
| 2025_jul_sep | `trend_breakout_20_regime300` | +5.77% | +10.77% | +12.81% | 13.18% |
| 2025_jul_sep | `ema_pullback_fast10` | +7.44% | +15.47% | +17.00% | 6.76% |
| 2025_oct_dec | `trend_breakout_20_regime300` | +3.33% | +13.95% | +21.21% | 11.26% |
| 2025_oct_dec | `ema_pullback_fast10` | +3.17% | +9.04% | +9.35% | 18.02% |
| 2026_jan_mar | `trend_breakout_20_regime300` | +1.59% | +5.50% | +15.04% | 5.42% |
| 2026_jan_mar | `ema_pullback_fast10` | +0.54% | +2.33% | +3.03% | 7.66% |
| 2026_apr_jun | `trend_breakout_20_regime300` | -0.39% | -0.17% | -1.85% | 13.35% |
| 2026_apr_jun | `ema_pullback_fast10` | -0.00% | +8.64% | +2.30% | 11.74% |
| 2026_jul_aug | `trend_breakout_20_regime300` | +3.33% | +3.76% | +8.42% | 7.75% |
| 2026_jul_aug | `ema_pullback_fast10` | +2.16% | +4.62% | +5.72% | 8.93% |

At 1.0% target risk, each strategy reached at least +15% in only 3 of 7 windows. Trend still lost in 2026 Apr–Jun; EMA stayed far below target in several 2026 windows. Closed-equity DD reached about 13.35% for Trend and 18.02% for EMA; MTM DD would be at least as important and may be worse.

## Decision

- Do not use higher leverage as a substitute for signal quality. The rolling native runs showed no margin rejects, while volume/risk-floor rejects appeared in difficult high-volatility windows.
- Keep 1.0% per-trade risk as an aggressive research ceiling, not a default.
- Next gate is a pre-registered quality/exit matrix: tighter ATR stops, alternative R targets, break-even runner, ADX(14), H1 trend alignment, and price-quality confirmation.
- Evaluate all variants across the same seven non-overlapping 1–3 month windows, with independent USD 40 books at 0.50%, 0.75%, and 1.00% risk plus a continuous normalized book.
- No real-money live trading.
