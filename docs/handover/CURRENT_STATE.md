# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-25

## Project objective

The project targets production/live deployment after sufficient evidence. Current implementation work remains on broker DEMO execution qualification.

Frozen alpha remains `v46_hl10_thr0p05_breadth4`; historical V46/V45 evidence is inherited and is not re-optimized merely to accelerate an execution test.

## Current operational state

The accepted V49 runtime has been running on Exness DEMO with live XAUUSDm M15 ticks. Forward screenshots/evidence show heartbeat and market feed healthy but breadth can remain 3/5 for long periods, producing no natural broker order. This is not by itself proof that the execution pipeline is broken.

V49 startup identity remains:
- accepted local runtime HEAD `2a12498d8b054127dcff766cd91e4a6b37aeef5a`;
- generated V49 source SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- frozen V48 parent SHA256 `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`;
- V49 magic `490049`.

## V50 decision

ADR-050 introduces `agent/v50-execution-probe` to decouple alpha frequency from execution qualification.

V50 does **not** lower breadth4 and does **not** retune alpha. It adds a separate DEMO-only execution probe with magic `500050` that:
- uses broker minimum volume;
- checks margin with `OrderCalcMargin` and caps required margin at 80% of free margin;
- alternates BUY/SELL;
- sets protective SL/TP;
- auto-closes after approximately 45 seconds;
- requires three broker-confirmed round trips;
- logs request/result prices, retcodes, order/deal IDs and trade transactions;
- sends push notifications through the existing MetaTrader notification path;
- never overlaps an open/pending breadth4 broker position.

Expected V50 result is `EXECUTION_PIPELINE_PASS`, `HOLD`, or `EXECUTION_PROBE_INCOMPLETE`.

## Transition safety

Do not stop/replace V49 while any of these are non-zero:
`virtual_open`, `owned_positions`, `open_pending`, `close_pending`.

The V50 runner builds and MetaEditor-compiles before it closes a settled V49 session. A build/compile failure must leave V49 untouched.

## Evidence workflow

After V50 FINAL the detached supervisor creates one ZIP under:
`runtime/v50_execution_probe/OUTPUT_V50/`

The ZIP includes `bundle_manifest_sha256.txt` plus V50 status/final/events/transactions and the relevant V49/run evidence.

## Current readiness

`EXECUTION_QUALIFICATION=V50_IMPLEMENTED_PENDING_WINDOWS_COMPILE_AND_RUN`

Do not infer strategy failure solely from two quiet breadth4 days. Do not infer strategy superiority from the execution probes; the probes exist only to qualify the broker plumbing quickly.
