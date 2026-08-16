# ADR-024 — Monthly horizon requires monthly variant re-screen

Status: Accepted — 2026-08-16

## Context

The practical decision horizon is now one full calendar month on a USD 40 tiny-capital book. Native H1 finalist evidence over 18 independent months showed that prior 1–3 month virtual rankings do not imply 15–20% monthly returns.

At USD 40 / 1.00% strict-target stop-risk, Trend H1 reached >=15% in 3/18 months and EMA H1 in 1/18. Median monthly returns were only about +2.43% and +3.69% respectively.

Exploratory replay above the approved ceiling showed that even 2.00% stop-risk did not lift median monthly return to 15%; it materially increased worst-month loss and drawdown instead.

## Decision

1. Keep the approved research stop-risk ceiling at 1.00%.
2. Do not use leverage or risk escalation as a substitute for expectancy.
3. Re-screen the existing 16 pre-registered Quality/Exit variants using independent one-month resets before adding new strategy parameters or families.
4. Reuse the exact `QualityExitLabV1.mq5` source that already compiled and ran successfully on Windows MT5; only the schedule/runner changes.
5. Use 18 full months (2025-02 through 2026-07), four books per candidate: normalized 10k@0.5%, USD40@0.5%, USD40@0.75%, USD40@1.0%.
6. Virtual monthly winners must return to native MT5 before promotion.

## Consequences

The next gate is cheaper and less error-prone than immediately writing new alpha code, and it answers whether the already-tested TP/SL/ADX/H1/quality variants were mis-ranked by the previous longer holding horizon.

If no existing variant materially improves median monthly return and >=15% hit rate without unacceptable drawdown, the project will expand to new complementary alpha families rather than increase per-trade risk above 1%.

REAL-MONEY LIVE TRADING remains forbidden.
