# ADR-021 — Improve edge/exit quality before escalating risk

Date: 2026-08-15

## Context

Rolling native validation across seven non-overlapping 1–3 month windows showed that the frozen Tier-A strategies are profitable often, but USD 40 strict 0.50% Standard-Cent-equivalent returns are usually below the user's 15–20% aspiration. Raising the allowed stop-risk to 0.75–1.00% increases participation and return in some windows, but does not make 15–20% robust and materially increases drawdown.

The user asked whether stronger leverage can increase entry ability. Current evidence shows the binding constraint is usually risk/lot granularity rather than margin: rolling native runs produced no margin rejects, while volume/risk-floor rejects appeared in high-volatility 2026 windows. Higher leverage lowers margin but does not reduce loss-at-stop or minimum-lot risk.

## Decision

1. Keep real-money live trading forbidden.
2. Treat 1.00% per-trade stop risk as an aggressive research ceiling, not a default.
3. Do not use leverage as a substitute for edge.
4. Run `QualityExitLabV1` before any risk escalation decision.
5. Pre-register 16 variants: baseline, tighter ATR stop, larger R target, break-even runner, ADX(14) filter, H1 trend alignment, price-quality confirmation, and a combined quality+exit variant for each Tier-A family.
6. Evaluate the same seven 1–3 month windows.
7. Each candidate is evaluated through four independent virtual books in the same tick stream: normalized continuous 0.50%, USD 40 cent-equivalent 0.50%, 0.75%, and 1.00%.
8. USD 40 cent books use 0.0001 standard-lot equivalent minimum/step and conservative 1:200 margin stress.
9. Promotion requires cross-window improvement in expectancy/PF and controlled MTM drawdown; a single 15–20% window is insufficient.

## Consequences

- Research targets the actual bottlenecks: signal quality, exit geometry, lot granularity and risk budget.
- The lab remains fast because all variants share one virtual tester pass per window; native parity is required only for finalists.
- 15–20% is treated as a stretch outcome to test, not a guaranteed or mandatory forecast.
