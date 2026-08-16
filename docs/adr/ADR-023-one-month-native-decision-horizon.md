# ADR-023 — One-month native decision horizon before further risk escalation

Date: 2026-08-16

## Context

The practical capital horizon is short. The intended initial USD 40 allocation is expected to be deployed for roughly one month at a time. A three-month aggregate can hide month-to-month dispersion and does not match that deposit/withdrawal horizon.

## Decision

- Supersede the pending 1–3 month H1 finalist native gate with `Monthly H1 Native V1`.
- Keep finalists and parameters frozen: `trend_h1_2atr_2r`, `ema_h1_2atr_2r`, stop=2 ATR, TP=2R, closed-H1 EMA alignment, session preflight unchanged.
- Test 18 full calendar months from 2025-02 through 2026-07. Exclude partial January 2025 and August 2026 from canonical monthly statistics.
- Native MT5 contract: XAUUSDm/M15, Model=0, ExecutionMode=0, USD 10,000 normalized deposit, native 0.50% risk, leverage 1:200, tester-only CTrade, external broker orders=0.
- Translate each monthly native ledger to USD 40 at strict-target 0.50%, 0.75%, and 1.00% stop-risk.
- Treat 15–20% monthly as an aspiration/hit-rate metric, not a guarantee or optimizer target.
- Risk above 1.00% remains outside the current research phase.
- Runner must checkpoint completed month/candidate runs in LocalAppData and reuse them after interruption; diagnostics include the checkpoint.
- REAL-MONEY LIVE TRADING remains forbidden.

## Required report

Positive-month ratio, >=15% and >=20% monthly hit rates, median/mean/worst/best return, USD profit, participation, native win rate/PF/MTM DD/costs/rejections.