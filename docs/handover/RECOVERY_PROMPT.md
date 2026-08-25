# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V50 fast DEMO execution qualification.

Authoritative branch for new work:
`agent/v50-execution-probe`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-050-decouple-alpha-frequency-from-execution-qualification.md`
3. `docs/research/v50_execution_probe_plan.md`
4. `runtime/v50_execution_probe/START_V50_EXECUTION_PROBE_GIT_BASH.sh`

## Frozen alpha

Do not lower or retune `v46_hl10_thr0p05_breadth4` just to make the execution test trade more often. Historical evidence is inherited.

## Why V50 exists

V49 can remain healthy and flat for long periods because breadth4 opportunities are selective. V50 therefore tests broker plumbing independently with three controlled Exness DEMO probe round trips while continuing to observe the frozen strategy.

V50 probe properties:
- separate magic `500050`;
- broker minimum volume;
- margin precheck;
- protective SL/TP;
- approximately 45-second hold;
- automatic close;
- `OnTradeTransaction` confirmation;
- push notification;
- no overlap with an open/pending breadth4 broker position;
- one final ZIP.

## Transition rule

Before replacing V49, require all four V49 status values to be zero:
`virtual_open`, `owned_positions`, `open_pending`, `close_pending`.

The V50 runner compiles before closing V49. If compilation fails, do not manually delete state or kill an unsettled V49 position.

## Final evidence

V50 final statuses:
- `EXECUTION_PIPELINE_PASS`;
- `HOLD`;
- `EXECUTION_PROBE_INCOMPLETE`.

Supervisor output:
`runtime/v50_execution_probe/OUTPUT_V50/V50_EXECUTION_PROBE_*.zip`

Use the ZIP manifest and broker transaction evidence for the next review.
