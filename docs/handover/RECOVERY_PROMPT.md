# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Current source of truth

Branch: `agent/v41-baseline-stack-action-value`.

Base accepted V40 evidence commit: `cb034e23ef9bf231fc1e1369295098854dcd77d0`.

Use explicit Windows refspec:

`git fetch --no-tags origin "+refs/heads/agent/v41-baseline-stack-action-value:refs/remotes/origin/agent/v41-baseline-stack-action-value"`

then `git checkout -B agent/v41-baseline-stack-action-value refs/remotes/origin/agent/v41-baseline-stack-action-value` and hard-reset to that remote ref.

Never `git clean`; accepted V36/V38 evidence and `.venv` may be untracked.

## Safety

REAL-MONEY LIVE TRADING forbidden. Research stop-risk <=1.00%/trade. No Martingale/grid/doubling. V41 Stage A launches no MT5/MetaEditor and sends no orders. No risk escalation to force 15%/month.

## Baseline

Exact control `adaptive_ewma_hl8_thr0`: $40 -> $107.43 over 12 months, 8.58% geometric/month, max DD9.90%, 563 trades, AvgR.215R, PF1.501. Target15%/month implies about $214.01 after 12 months and remains unmet.

Baseline is a causal EWMA performance router, not a neural net. Experts: EMA skip20, MACD gap10, BOS/FVG gap8, Trend20 gap5, Slow Momentum16h+24h. Realized-R EWMA half-life8, threshold0; chosen expert owns direction.

## Frozen evidence / do not retune

- V32 DeepMLP keep60: frozen risk-efficiency benchmark; no keep-rate retune on Feb-Jul2026.
- V36 Transformer: frozen sequence-state model; use accepted predictions, chronology-calibrate them, do not retrain them to improve V41 headline metrics.
- V30 expected-R: architecture lead; family-specific context matters; do not claim fresh confirmation from reused 2025-08..2026-07 data.

Rejected: generic cooldown, hard quality conjunction, broad signal fusion, fixed range->family mapping, universal fast exit, V39 eventual-giveback target, V40 first-passage-only action trigger.

## V41

Entry layer: HGB expected-R; fixed 60% prior-calibration keep target. Features are source/direction/clock and prior completed-trade sequence context only.

Action layer: direct `delta_R = action_R - baseline_R` for static-protect0.25R and selective-trail0.25R; HGB regression + P(delta>0); fixed 20% calibration coverage target and predicted delta must be positive.

V36 layer: isotonic calibration fit only on accepted V36 rows whose control trades fully exited before the fold calibration boundary.

Hard sequence/session rules are diagnostic-only. Layers are gated separately so a weak entry layer cannot hide a good action layer and vice versa.

All equity output is calibrated decision-tape shadow, not exact-MT5. A Stage-A PASS only freezes one promotion lane for exact-MT5 Stage B.

## Runner hardening

Preserve: pytest optional with direct static fallback; tracked-source secret scan; explicit refspec; no `git clean`; V36 dependency recovery; V40 `signal_sources` schema adapter; compile all V41/V40 dependency files; offline safety-token scan; one ZIP + internal SHA manifest + CRC + analyzer verification.

## Output

Upload only `runtime/v41_baseline_stack/OUTPUT_V41_STAGE_A/v41_baseline_stack_action_value_stage_a.zip`.

After upload verify integrity, then report DONE / EVIDENCE / DECISIONS / ISSUES / NEXT including exact baseline vs entry/action/stack shadows vs15% target.
