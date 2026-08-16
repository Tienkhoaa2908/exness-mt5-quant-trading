# ADR-025 — Profit protection is measured explicitly; MT5 research runs are bounded

## Status

Accepted — 2026-08-16.

## Context

Monthly H1 native validation showed that the existing static 2 ATR / 2R exits do not robustly achieve the USD 40 monthly return aspiration. User review of trade charts also highlighted open-profit giveback: positions can move favorably and then return much of that unrealized profit before the fixed exit fires.

The subsequent monthly QualityExit rescreen runner also exposed a reliability problem. It opened MT5 once per month and used unbounded `Start-Process -Wait`. During the `2025_10` run the Exness trial service reported `Service is not available` and the tester was not synchronized; the process appeared to hang.

## Decision

1. Exit quality is evaluated with path-dependent metrics, not only final PnL:
   - MFE/MAE in R;
   - giveback from MFE to realized R;
   - capture efficiency;
   - reached +1R then ended non-positive.
2. Keep H1 entry logic and the 2 ATR initial stop fixed for this experiment so the variable under study is profit protection.
3. Pre-register a small bounded set of profit-lock, trailing, stepped and partial-take policies; do not run an unconstrained optimizer.
4. Run monthly-reset virtual books in three six-month MT5 chunks rather than 18 separate terminal startups.
5. Replace unbounded MT5 waiting with heartbeat + watchdog + one retry + broker-unavailable detection.
6. Preserve/recover completed chunks from checkpoint or validated Common Files artifacts.
7. Any virtual exit finalist must pass native MT5 dynamic-stop/partial-close parity before promotion.

## Consequences

The experiment directly tests the observed failure mode and should reduce Windows runtime/startup fragility. It does not guarantee that earlier profit capture improves expectancy; overly aggressive trailing can cut trend winners, so selection remains evidence-driven.

Real-money live trading remains forbidden.