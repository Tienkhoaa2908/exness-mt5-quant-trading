# ADR-041 — Upgrade the adaptive baseline with layered value models, not replacement strategy churn

Status: Accepted for V41 Stage A research  
Date: 2026-08-21

## Context

The accepted exact-MT5 control is `adaptive_ewma_hl8_thr0`: $40 -> $107.43 over 12 months, 8.58% geometric/month, max DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501. It remains materially below the aspirational 15%/month target.

The baseline is already adaptive. It is a causal performance-weighted mixture of rule-based experts: EMA skip20, MACD gap10, BOS/FVG gap8, Trend20 gap5 and slow 16h/24h momentum. Normalized realized-R updates an EWMA expert score with half-life 8; the router threshold is zero. The meta-router does not directly predict Buy/Sell.

Prior research establishes several distinct lessons:

- V32 DeepMLP keep60 improves risk efficiency materially but does not raise exact return;
- V36 Transformer predicts in-trade hold/protect state reproducibly but has not produced PnL by itself;
- V30 expected-R targets are more useful than win/loss classification and require family context;
- generic cooldowns, hard quality conjunctions, broad signal fusion, fixed range-to-family maps and universal fast exits were rejected;
- V39 eventual-giveback and V40 first-passage targets both fail to answer the final economic question: whether a specific action improves realized R versus the baseline exit.

## Decision

V41 keeps the adaptive router as the core control and adds value layers around it:

1. **Entry expected-R layer** — fixed 60% calibration keep target, informed by V32/V30, using only causal source/time/prior-completed-trade context. Sequence/exhaustion is a feature, not a hard rule.
2. **V36 state layer** — accepted Transformer probabilities are chronology-calibrated and used as in-trade features; V36 is not retrained.
3. **Direct action-value layer** — regress `delta_R = action_R - baseline_R` and classify `P(delta_R > 0)` for static protect and selective trail. The action gate is frozen to a 20% calibration coverage target and requires predicted delta >0.
4. **Layer audit** — targeted exhaustion/session hypotheses are reported separately and cannot be silently activated from the same sample.
5. **Risk governor** — no new entries, no initial-risk increase, no stacking above the 1.00% research ceiling.

Stage-A shadow equity is calibrated to the accepted exact baseline for economic comparison but is not exact-MT5 PnL. Dropping an entry or changing an exit can alter future adaptive-router state, opportunity availability and sizing, so any promoted lane must return to frozen exact-MT5 replay.

## Consequences

- A harmful entry layer cannot poison a useful action layer: lanes are gated independently before the integrated stack is considered.
- V32 remains a frozen benchmark instead of being retuned on Feb-Jul 2026.
- V30 family-specific expected-R evidence guides architecture but is not claimed as fresh confirmation.
- V41 cannot be rescued by sweeping keep rates/action coverage after results are seen.
- A Stage-A PASS permits only a frozen exact-MT5 Stage B; LIVE remains forbidden.
