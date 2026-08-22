# ADR-045 — Multi-year single-run validation before deployment escalation

## Decision

Freeze the V44 baseline family and run one continuous historical MT5 test from
2022-01-01 to 2026-08-01 with monthly logging. Use a cold adaptive state and
exclude six warm-up months. Do not inject the accepted 2025-08 state backwards.

## Why

V44 demonstrated excellent one-year economics and restart robustness, but all
19 windows came from the same 2025-08 to 2026-08 regime. A multi-year test is
more valuable now than another parameter optimization cycle.

One continuous run is preferred to dozens of historical restarts because it is
faster, preserves causal state evolution, and still provides monthly/yearly
analysis through the EA's monthly ledger.

## Consequences

- V45 is validation, not optimization.
- Primary: HL10 threshold0.05; return shadow: HL8 threshold0.05; control: HL8 threshold0.
- Historical state starts cold; first six months are warm-up.
- MT5 is not rerun after a collection/analysis/packaging-only failure.
- A pass supports paper/demo deployment work only.
- Real-money live trading remains forbidden.
