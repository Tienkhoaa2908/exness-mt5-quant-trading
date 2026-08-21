# ADR-043 — Confidence-aware credit routing before new alpha layers

Date: 2026-08-21
Status: Accepted for development research

## Context

The accepted control `adaptive_ewma_hl8_thr0` remains the strongest verified production-style research baseline. V39-V41 overlays failed to monetize predictive state information robustly. V42 exact MT5 tested global direction-switch time hysteresis and was HOLD: quality metrics improved, but participation and compounded return fell.

V42 also confirmed that the historical `adaptive_ewma_hl8_thr0p05` and `adaptive_ewma_hl10_thr0p05` routers are more promising than broad switch delays. Their exact ending balances modestly exceed control while turnover is lower, but neither meets the material promotion gate.

## Decision

V43 will test confidence-aware cross-direction credit allocation on exactly two frozen parents: HL8 threshold0.05 and HL10 threshold0.05.

Four candidates are fixed before results: each parent with directional top-score margin 0.05R or 0.10R. When only one direction has an eligible active expert, V43 selects it immediately. When both directions are active, V43 compares the strongest LONG and SHORT EWMA scores. A clear leader is selected immediately. Only when the score gap is below the fixed candidate margin may the candidate retain its currently active incumbent direction, and only if that direction remains active.

There is no global time hysteresis and no delay attached merely to a direction change.

## Parent and control gates

Every V43 candidate must pass both:

1. the existing material-uplift gate versus accepted `adaptive_ewma_hl8_thr0` control; and
2. an incremental gate versus its own frozen HL8/HL10 threshold0.05 parent.

This prevents a renamed parent or a marginally altered router from being declared a V43 win without incremental economic value.

No same-window margin retuning is allowed.

## Provenance and runtime decision

The immutable research parent remains accepted V38 ZIP SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`. Historical V34/V38 source-builder reconstruction is not an acceptance path.

V43 uses a direct tracked Git Bash runner. Runtime shell patch generation is forbidden. Windows UTF-8, ERR-trap-safe process launching, compile artifact reuse, new-LATEST MT5 completion, portable Python packaging and package-only recovery are mandatory controls inherited from the V42 incident history.

If Strategy Tester and analyzer have completed but packaging fails, do not rerun MT5. Resume only the failed packaging stage.

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Strategy Tester only. `AllowLiveTrading=0`, `AllowDllImport=0`, no native/external broker-order path, and research risk <=1.00% per trade.
