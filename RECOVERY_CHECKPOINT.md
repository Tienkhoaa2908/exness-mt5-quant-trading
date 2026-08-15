# Recovery checkpoint — 2026-08-15

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, or doubling after loss.

## Canonical local history

Latest local Git commit: `a43d4bdee5c8805f2054bb37975aa7405b33d3e1` — `research: accept session preflight and add rolling 1-3m gate`.

Complete Git bundle SHA-256: `59776f8040384c08be8d3deea933653ac7e67cde708bf76c1ab3642dacddd59c`.
Source snapshot SHA-256: `643cfadd8b204d88e4e7de18898ac652b528b9adc16dffa2213b700f5033f177`.
Next research kit SHA-256: `e03b9025735a2ae4106bed9598dc690262534b5a29ea60c200586f8702052fcc`.
Session-preflight uploaded bundle SHA-256: `44488930085c45bf7dfd16c68622b511d84e2ff765734ef7174e73c78b7305d5`.

## Accepted strategy state

Tier A remains:
- `trend_breakout_20_regime300`
- `ema_pullback_fast10`

Parameters remain FROZEN.

Long native validation (2025-01-10 through 2026-08-15, XAUUSDm/M15, generated Every Tick):
- Trend: $10,000 -> $15,889.99, +$5,889.99 (+58.90%), 788 filled trades, win 38.20%, PF 1.206, MTM DD 8.53%.
- EMA: $10,000 -> $14,802.02, +$4,802.02 (+48.02%), 772 filled trades, win 37.82%, PF 1.174, MTM DD 11.00%.

## Session Preflight V1 — PASS

Canonical evidence: `evidence/mt5_runs/2026-08-15_session_preflight_v1/` in local history.

- Every internal SHA-256 in the uploaded bundle passed.
- All 15 previously observed `10018 MARKET_CLOSED` timestamps became dynamic broker-session skips using `SymbolInfoSessionTrade`.
- 17 total session skips were observed: the 15 known timestamps plus 2 additional closed-session signals.
- All four targeted native runs had `order_fail=0`.
- No alpha parameters were changed.

Targeted normalized-account results:
- 2025 window (~5 weeks): Trend +6.97%, PF 1.479, win 45.10%, MTM DD 4.07%; EMA +7.01%, PF 1.464, win 44.23%, MTM DD 2.46%.
- 2026 window (~7.5 weeks): Trend +4.35%, PF 1.275, win 39.06%, MTM DD 2.78%; EMA -0.03%, PF 0.998, win 34.33%, MTM DD 3.35%.

## Capital policy and practical horizon

Canonical small-capital comparison set: USD 20 / USD 30 / USD 40. Maximum intended first deposit is USD 40.

Risk contract:
- target risk = 0.50% equity per trade;
- hard cap = 1.00% only as a rejection ceiling, not a target;
- never round volume upward;
- skip if minimum lot violates the target under strict-target analysis.

Practical decision horizon is now **1–3 months**. Long-history results remain robustness context, but promotion decisions must also show repeated non-overlapping 1–3 month windows.

Important period dependence from Session Preflight evidence under Standard-Cent-equivalent strict 0.50% replay:
- 2025 window: USD 40 executed essentially all accepted native signals and ended around $42.57 Trend / $42.20 EMA.
- 2026 window: USD 40 could execute only about 42% of Trend and 31% of EMA accepted native signals, ending around $40.88 Trend / $40.42 EMA.
- USD 20 executed zero accepted native signals in that early-2026 window at strict 0.50%, illustrating strong lot-granularity dependence on XAU price/volatility.

These are historical capital-mechanics replays, not live projections and not native XAUUSDc backtests.

## Next gate — Rolling 1–3M Validation V1

Run `scripts/run_rolling_1to3m_v1.cmd` from the V13 one-click kit.

Two frozen Tier-A strategies × seven non-overlapping windows = 14 native generated-tick tests:
- 2025-01-10 -> 2025-04-01
- 2025-04-01 -> 2025-07-01
- 2025-07-01 -> 2025-10-01
- 2025-10-01 -> 2026-01-01
- 2026-01-01 -> 2026-04-01
- 2026-04-01 -> 2026-07-01
- 2026-07-01 -> 2026-08-15

The MQL source is byte-identical to the Session Preflight V1 source that just passed. New native order rejections are evidence and do not abort the batch unless artifact integrity fails.

After upload, report each window separately for normalized native performance and USD 20/30/40 capital translation.

## Recovery rule

GitHub is a required checkpoint after every material milestone. Local source snapshot + complete Git bundle remain the second recovery layer until the full source tree/history is mirrored on remote. Never claim remote sync is complete without verifying the remote commit/files.