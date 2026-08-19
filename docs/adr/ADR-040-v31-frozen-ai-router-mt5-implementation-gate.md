# ADR-040 — V31 frozen AI router MT5 implementation gate

## Status

Accepted for Strategy Tester research — 2026-08-20.

## Context

V30 showed that expected-R filtering was more useful than direct win/loss classification, while GRU, causal TCN and Patch Transformer did not beat stronger tabular controls. Repeated `(entry_time,direction)` catalog opportunities also require inverse-multiplicity controls.

The next implementation gate evaluates explicit nonlinear neural/kernel/SVR models in the same MT5 virtual-book path used by the accepted V30 evidence. The research objective is a `$40` virtual starting book with an aspirational `15%/month` target, while keeping maximum research risk at 1.00% per trade.

## Decision

Create `V31AiRouterLabV1` with the original 12 V30 baseline candidates plus three frozen synthetic AI candidates:

1. distilled ReLU DNN `73-96-48-24-1`;
2. linear SVR expected-R control;
3. 384-component random-Fourier RBF approximation followed by weighted Ridge.

All models use the same frozen 73-dimensional causal input. Training labels end before `2025-07-01`; July-2025 scores freeze the thresholds. No threshold is re-estimated during the MT5 run.

The implementation interval is `2025-08-01 -> 2026-08-01`, `XAUUSDm M15`, using MT5 `Every tick` generated tester ticks. This interval validates implementation/economic behavior but is not pristine statistical confirmation because it was already inspected during offline model development.

## Economic gate

Primary book: `usd40_r1p0_cent`. Also evaluate 0.5% and 0.75% risk books for robustness.

A result is not accepted merely because arithmetic mean monthly return exceeds 15%. Evaluation also requires median return, months above 15%, positive-month breadth, worst month, MTM drawdown, turnover, sizing rejects and concentration.

The 1.00% per-trade research ceiling is not increased to force the target.

## Evidence contract

Before Strategy Tester begins, Windows MetaEditor must report `0 errors / 0 warnings`. A complete run must produce 12 months × 15 candidates × 4 books = 720 monthly-summary rows, plus trade ledger, bar features, manifest, compile log and adaptive-state checkpoints.

A future untouched chronological holdout remains mandatory before any PAPER/DEMO promotion.
