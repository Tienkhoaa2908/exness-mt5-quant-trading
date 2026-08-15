# Recovery checkpoint — 2026-08-15

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, or doubling after loss.

## Canonical local history

Latest local Git commit: `eac12cf` — `research: add USD 40 capital replay and session preflight gate`.

Complete Git bundle SHA-256: `5cdb2a72fb87290d4d5adb17c6a5dafed391eb79531f081edef3ea619feb8dda`.
Source snapshot SHA-256: `70d66561b728128e054d82ac6b404c3fe96fa5ac1af3f01a5cd88814a290ad59`.
Next research kit SHA-256: `9edb46559b04a7c820bff779ec5ef25d50ee45cb61e27496d9ae01ac80a22dff`.

## Accepted strategy state

Tier A remains:
- `trend_breakout_20_regime300`
- `ema_pullback_fast10`

Long native validation window: 2025-01-10 through 2026-08-15, XAUUSDm M15, generated Every Tick, native MT5 Strategy Tester orders.

Normalized USD 10,000 results:
- Trend: +$5,889.99 -> $15,889.99, +58.90%, 788 filled trades, win rate 38.20%, PF 1.206, MTM DD 8.53%.
- EMA: +$4,802.02 -> $14,802.02, +48.02%, 772 filled trades, win rate 37.82%, PF 1.174, MTM DD 11.00%.

All 15 native order failures were retcode `10018 MARKET_CLOSED`; no sizing/stops/margin failure was observed in that long run.

## Tiny-capital state

Canonical comparison set is now USD 20 / USD 30 / USD 40. Strict risk target = 0.50% equity; hard cap = 1.00%; volume is floored and never rounded upward.

Native-ledger Standard-Cent-equivalent replay:
- Trend: $20 -> $24.00; $30 -> $40.75; $40 -> $59.43.
- EMA: $20 -> $22.47; $30 -> $38.52; $40 -> $59.19.

These are historical capital-mechanics replays, not live projections and not native XAUUSDc backtests. USD 40 is mechanically least censored by minimum lot among the three balances.

## Next gate

Run `Session Preflight V1`: dynamic broker-session validation using MQL5 `SymbolInfoSessionTrade`, two targeted windows covering every prior 10018 failure, two Tier-A strategies. PASS requires all prior failure timestamps to become preflight session skips and native `order_fail=0`.

After PASS: promote session-aware core, then extended-history/OOS and cent-specific cost/spec validation.

## Recovery rule

GitHub is a required checkpoint after every material milestone. Local source snapshot + complete Git bundle remain the second recovery layer until the full source tree/history is mirrored on remote. Never claim remote sync is complete without verifying the remote commit/files.