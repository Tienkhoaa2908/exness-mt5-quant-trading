# Native-ledger capital translation — USD 20 / 30 / 40

Date: 2026-08-15

Source: accepted ~19-month native MT5 Tier-A ledger, XAUUSDm M15, 2025-01-10 -> 2026-08-15, generated Every Tick, native Strategy Tester orders. Standard-Cent-equivalent sizing only; not a native XAUUSDc backtest and not a live forecast.

Risk policy: target 0.50% equity, hard cap 1.00%, floor-only volume quantization, no upward rounding.

| Strategy | Initial | Profit | Final | Return | Executed/Signals | Win% | PF | Closed DD% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Trend Regime300 | $20.00 | +$4.00 | $24.00 | +20.00% | 312/788 (39.6%) | 39.42 | 1.240 | 5.55 |
| Trend Regime300 | $30.00 | +$10.75 | $40.75 | +35.83% | 590/788 (74.9%) | 38.31 | 1.210 | 8.40 |
| Trend Regime300 | $40.00 | +$19.43 | $59.43 | +48.59% | 724/788 (91.9%) | 38.12 | 1.217 | 6.67 |
| EMA Pullback10 | $20.00 | +$2.47 | $22.47 | +12.33% | 280/772 (36.3%) | 38.21 | 1.167 | 3.98 |
| EMA Pullback10 | $30.00 | +$8.52 | $38.52 | +28.42% | 525/772 (68.0%) | 38.48 | 1.189 | 6.98 |
| EMA Pullback10 | $40.00 | +$19.19 | $59.19 | +47.96% | 678/772 (87.8%) | 38.64 | 1.231 | 8.18 |

USD 40 is mechanically superior to USD 30 for the frozen XAU risk contract because minimum-lot censoring is much smaller: roughly 88–92% of native signals can be represented under the 0.50% target versus roughly 68–75% at USD 30. USD 20 remains heavily censored.

These historical paths must not be presented as expected future balances. XAUUSDc-specific spread, swap, session, margin and OOS validation are still required. REAL-MONEY LIVE TRADING remains forbidden.