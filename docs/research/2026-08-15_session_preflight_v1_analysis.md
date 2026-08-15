# Session Preflight V1 — analysis

Uploaded bundle SHA-256: `44488930085c45bf7dfd16c68622b511d84e2ff765734ef7174e73c78b7305d5`.

Integrity: every path in `bundle_manifest_sha256.txt` was recomputed and matched.

## Preflight contract

- Previously observed `10018 MARKET_CLOSED` timestamps: **15**.
- Exact timestamps now caught by session preflight: **15/15**.
- Total dynamic session skips in the two windows: **17**.
- Additional closed-session signals caught: **2**.
- Native order failures after preflight: **0 in all four runs**.

Additional dynamic skips beyond the old failure list:
- `2026_q1` `ema_pullback_fast10` `2026.01.30 21:45:00`
- `2026_q1` `ema_pullback_fast10` `2026.02.02 21:00:00`

## Native normalized-account results

| Window | Strategy | Initial | Profit | Final | Return | Closed trades | Win rate | PF | MTM DD | Session skip | Volume reject | Order fail |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025_q1 | `trend_breakout_20_regime300` | $10,000 | +697.37 | $10697.37 | +6.97% | 51 | 45.10% | 1.479 | 4.07% | 2 | 0 | 0 |
| 2025_q1 | `ema_pullback_fast10` | $10,000 | +701.01 | $10701.01 | +7.01% | 52 | 44.23% | 1.464 | 2.46% | 6 | 0 | 0 |
| 2026_q1 | `trend_breakout_20_regime300` | $10,000 | +434.61 | $10434.61 | +4.35% | 64 | 39.06% | 1.275 | 2.78% | 3 | 19 | 0 |
| 2026_q1 | `ema_pullback_fast10` | $10,000 | -3.20 | $9996.80 | -0.03% | 67 | 34.33% | 0.998 | 3.35% | 6 | 21 | 0 |

These windows are already close to the intended capital holding horizon: the 2025 window is about 5 weeks and the 2026 window about 7.5 weeks.

## USD 20 / 30 / 40 strict-target replay

Standard-Cent-equivalent capital translation, target risk 0.50%, hard cap 1.00%, floor volume, and skip when minimum volume would exceed the target. This is not a native XAUUSDc backtest.

| Window | Strategy | Initial | Profit | Final | Return | Executed/signals | Win rate | PF | Closed DD | Avg actual risk |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025_q1 | `trend_breakout_20_regime300` | $20 | +1.04 | $21.04 | +5.22% | 48/52 (92.3%) | 45.83% | 1.448 | 3.10% | 0.379% |
| 2025_q1 | `trend_breakout_20_regime300` | $30 | +2.10 | $32.10 | +7.01% | 52/52 (100.0%) | 44.23% | 1.594 | 3.11% | 0.377% |
| 2025_q1 | `trend_breakout_20_regime300` | $40 | +2.57 | $42.57 | +6.42% | 52/52 (100.0%) | 44.23% | 1.477 | 3.33% | 0.410% |
| 2025_q1 | `ema_pullback_fast10` | $20 | +0.82 | $20.82 | +4.11% | 44/53 (83.0%) | 43.18% | 1.441 | 1.88% | 0.355% |
| 2025_q1 | `ema_pullback_fast10` | $30 | +1.66 | $31.66 | +5.53% | 52/53 (98.1%) | 46.15% | 1.455 | 1.77% | 0.388% |
| 2025_q1 | `ema_pullback_fast10` | $40 | +2.20 | $42.20 | +5.49% | 53/53 (100.0%) | 45.28% | 1.437 | 1.91% | 0.393% |
| 2026_q1 | `trend_breakout_20_regime300` | $20 | +0.00 | $20.00 | +0.00% | 0/64 (0.0%) | n/a | 0.000 | 0.00% | n/a |
| 2026_q1 | `trend_breakout_20_regime300` | $30 | +0.61 | $30.61 | +2.02% | 11/64 (17.2%) | 45.45% | 1.820 | 1.12% | 0.423% |
| 2026_q1 | `trend_breakout_20_regime300` | $40 | +0.88 | $40.88 | +2.20% | 27/64 (42.2%) | 40.74% | 1.353 | 2.56% | 0.379% |
| 2026_q1 | `ema_pullback_fast10` | $20 | +0.00 | $20.00 | +0.00% | 0/67 (0.0%) | n/a | 0.000 | 0.00% | n/a |
| 2026_q1 | `ema_pullback_fast10` | $30 | +0.54 | $30.54 | +1.79% | 8/67 (11.9%) | 50.00% | 2.119 | 1.16% | 0.411% |
| 2026_q1 | `ema_pullback_fast10` | $40 | +0.42 | $40.42 | +1.04% | 21/67 (31.3%) | 38.10% | 1.200 | 2.54% | 0.391% |

## Decision

- Session-aware broker preflight is accepted: it converts all 15 known MARKET_CLOSED order failures into safe skips and creates zero native order failures in the validation windows.
- The practical holding horizon is now **1–3 months**, so long multi-year returns remain robustness evidence but are no longer the main decision unit.
- Future capital evaluation must be reported per 1–3 month window, with USD 20 / 30 / 40 translations and signal participation. The recent 2026 window shows why: higher XAU price/volatility can make small-capital lot granularity far more restrictive than in 2025.
- Default risk target remains 0.50%; the 1.00% hard cap is a rejection ceiling, not a target.
- No real-money live trading is authorized.
