# NEXT EXPERIMENT — Rolling 1–3M Validation V1

Parameter search remains **FROZEN**.

Session Preflight V1 is accepted: all 15 previously observed `10018 MARKET_CLOSED` timestamps are now dynamic session skips and all four targeted native runs have `order_fail=0`. Two additional closed-session signals were also skipped by broker session metadata.

## Purpose

Evaluate the two frozen Tier-A strategies over repeated, non-overlapping periods that match the practical capital holding horizon. The main question is not “what is the 19-month return?” but “how often does a USD 20/30/40 account have a usable and positive 1–3 month experience under the frozen risk contract?”

## Batch

Two strategies:
- `trend_breakout_20_regime300`
- `ema_pullback_fast10`

Seven windows:
- `2025.01.10 → 2025.04.01`
- `2025.04.01 → 2025.07.01`
- `2025.07.01 → 2025.10.01`
- `2025.10.01 → 2026.01.01`
- `2026.01.01 → 2026.04.01`
- `2026.04.01 → 2026.07.01`
- `2026.07.01 → 2026.08.15`

Total: 14 native MT5 Strategy Tester runs, generated Every Tick, XAUUSDm/M15, execution delay 0, normalized USD 10,000 deposit, dynamic `SymbolInfoSessionTrade` preflight.

## Acceptance / evidence contract

- Artifact integrity and safety fields must pass.
- Do **not** abort merely because `order_fail > 0`; preserve retcodes as evidence.
- After upload, compute per-window native metrics and separate Standard-Cent-equivalent translations for USD 20 / 30 / 40.
- Target risk 0.50%; 1.00% is a hard ceiling, not a target; no upward volume rounding.
- No parameter changes based on these windows.
- REAL-MONEY LIVE TRADING remains forbidden.
