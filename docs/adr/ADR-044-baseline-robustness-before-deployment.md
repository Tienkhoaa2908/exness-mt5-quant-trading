# ADR-044 — Baseline-first robustness validation before deployment escalation

Date: 2026-08-21
Status: Accepted for research execution

## Context

The accepted baseline `adaptive_ewma_hl8_thr0` produced `$40 -> $107.432645`,
8.58163% geometric/month, 9.9038% max DD and 563 trades on the accepted
12-month exact-MT5 window. V39-V42 did not establish a material return upgrade.
V42 showed that broad direction-switch hysteresis improves quality metrics but
reduces participation and compounding.

The user wants to move quickly toward deployment. The highest-value next step
is therefore not another overlay or parameter sweep; it is broad exact-MT5
robustness validation of the baseline family plus engineering hardening.

## Decision

Freeze three routers: HL8 threshold0, HL8 threshold0.05, HL10 threshold0.05.
Do not tune them on V44.

Run 19 exact restart windows: 12 monthly, 4 quarter blocks, 2 half-years and
1 annual. Run the annual window first and require exact accepted-control
reproduction before spending time on the remaining windows.

Build V44 from immutable accepted V38 source. Change telemetry/output markers
only; strategy logic, entry/exit geometry, sizing and risk remain frozen.

Use artifact-driven compile and MT5 checkpoints, portable Python packaging and
package-only recovery.

## Consequences

This campaign can establish whether the >100% annual result is broad enough to
justify paper/demo deployment work. It cannot establish future returns and it
does not authorize live capital.

If no candidate passes the fixed robustness gate, return to baseline research
rather than relaxing the V44 gate or retuning on the same 19 windows.
