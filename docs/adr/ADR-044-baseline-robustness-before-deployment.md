# ADR-044 — Baseline-first robustness validation before deployment escalation

Date: 2026-08-21
Status: Accepted for historical research; project-wide live policy superseded by ADR-049

## Policy note

V44 was a historical robustness milestone. Project-wide policy is now:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Any statement in V44 about not authorizing live capital describes the evidence level of V44 itself, not a permanent prohibition on real-money research or future production deployment.

## Context

The accepted baseline `adaptive_ewma_hl8_thr0` produced `$40 -> $107.432645`, 8.58163% geometric/month, 9.9038% max DD and 563 trades on the accepted 12-month exact-MT5 window. V39-V42 did not establish a material return upgrade.

The highest-value next step was broad exact-MT5 robustness validation of the baseline family plus engineering hardening rather than another overlay or parameter sweep.

## Decision

Freeze three routers: HL8 threshold0, HL8 threshold0.05, HL10 threshold0.05. Do not tune them on V44.

Run 19 exact restart windows: 12 monthly, 4 quarter blocks, 2 half-years and 1 annual. Run the annual window first and require exact accepted-control reproduction before spending time on the remaining windows.

Build V44 from immutable accepted V38 source. Change telemetry/output markers only; strategy logic, entry/exit geometry, sizing and risk remain frozen.

Use artifact-driven compile and MT5 checkpoints, portable Python packaging and package-only recovery.

## Consequences

V44 can establish whether the one-year baseline is broad enough to justify the next deployment-readiness research stage. It cannot establish future returns by itself.

If no candidate passes the fixed robustness gate, return to baseline research rather than relaxing the V44 gate or retuning on the same 19 windows.

Current project-wide live-trading research/readiness semantics are defined by ADR-049, not by the historical V44 phase boundary.
