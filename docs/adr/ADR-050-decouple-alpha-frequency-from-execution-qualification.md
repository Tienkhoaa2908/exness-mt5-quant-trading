# ADR-050 — Decouple alpha frequency from execution qualification

Date: 2026-08-25
Status: Accepted for implementation

## Context

V49 correctly preserved the frozen `v46_hl10_thr0p05_breadth4` strategy, but its execution qualification depended on naturally occurring breadth4 trades. In forward DEMO operation the market feed and heartbeat were healthy while breadth remained 3/5 for long periods, so the order/open/close/reconciliation/notification pipeline could remain untested for days even though the plumbing itself might be correct.

Changing breadth4 to breadth3 only to make the rehearsal trade more often would mix two different questions: alpha quality and execution correctness. It would also discard the historical evidence attached to the frozen candidate.

## Decision

Create V50 as a separate DEMO-only execution qualification layer.

V50 keeps the frozen breadth4 strategy unchanged and adds a second, clearly separated execution-probe magic number. The probe:

- runs only on an Exness DEMO account;
- uses `SYMBOL_VOLUME_MIN` rather than a strategy-sized position;
- checks required margin with `OrderCalcMargin` before every probe open;
- refuses the probe if required margin exceeds 80% of free margin;
- alternates BUY/SELL probe direction;
- uses protective SL/TP;
- holds a probe approximately 45 seconds, then closes it automatically;
- requires three confirmed broker-DEMO round trips;
- records request/result prices, retcodes, order/deal IDs and broker transactions;
- uses a dedicated magic `500050` and never overlaps a breadth4 broker/pending position;
- retains the V49/breadth4 magic `490049` and strategy semantics unchanged;
- stops new strategy entries after V50 FINAL so the packaged evidence is stable.

A clean probe result is `EXECUTION_PIPELINE_PASS`. This is an execution/plumbing result, not a claim that breadth4 trade frequency is optimal and not a substitute for historical alpha evidence.

## Why this is preferred to lowering breadth

Historical strategy evidence remains comparable and reproducible. Execution qualification no longer depends on rare alpha opportunities. If later research concludes that breadth4 is too selective, that is a separate strategy research decision and must be evaluated against the historical evidence rather than silently changed inside an execution test.

## Transition rule

V50 may replace an active V49 session only when V49 is completely settled:

- `virtual_open=0`;
- `owned_positions=0`;
- `open_pending=0`;
- `close_pending=0`.

V50 builds and compiles before closing V49. Compile/start failure must not destroy an unsettled V49 position.
