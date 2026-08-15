# ADR-020 — Rolling 1–3 month decision windows

Status: Accepted — 2026-08-15.

## Context

The intended small-capital deployment horizon is usually about 1–3 months rather than leaving USD 20–40 continuously deployed for years. Long-history tests are still necessary for robustness, but a single 19-month aggregate can hide period-specific capital feasibility and regime dependence. Session Preflight V1 also showed that the same strategy behaves differently in early 2025 versus early 2026, while XAU price/ATR changes can heavily censor Standard-Cent-equivalent sizing for USD 20–40.

## Decision

1. The primary decision unit for the next research stage is a **non-overlapping 1–3 month window**.
2. Run the two frozen Tier-A strategies with the accepted dynamic trade-session preflight.
3. Cover the available 2025–2026 history with seven non-overlapping windows, approximately 1.5–3 months each.
4. Keep normalized native MT5 deposit at USD 10,000 for strategy/execution comparability.
5. After evidence ingestion, translate each accepted native ledger separately to USD 20 / 30 / 40 using Standard-Cent-equivalent lot quantization, target 0.50% risk, hard cap 1.00%, no upward rounding.
6. Report per-window: initial cash, USD PnL, final cash, return, executed/signals, win rate, PF, MTM DD on normalized native run, small-capital closed DD, session rejects, volume rejects, order failures/retcodes, costs.
7. New native order failures are **evidence**, not an automation failure; the batch must continue and package them unless artifact integrity fails.
8. Parameters remain frozen. This experiment measures temporal robustness, not optimization.
9. Real-money live trading remains forbidden.

## Window set

- 2025-01-10 → 2025-04-01
- 2025-04-01 → 2025-07-01
- 2025-07-01 → 2025-10-01
- 2025-10-01 → 2026-01-01
- 2026-01-01 → 2026-04-01
- 2026-04-01 → 2026-07-01
- 2026-07-01 → 2026-08-15

## Rationale

This matches the likely capital holding duration, exposes regime and lot-granularity dependence, and avoids selecting a strategy from one favorable aggregate period.
