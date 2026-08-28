# V47 Forward Regime-Shadow Validation Plan

Date: 2026-08-22

## Policy note

V47 was a forward/shadow research milestone. Current project-wide live policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V47's paper/shadow/no-broker-order restrictions describe V47 itself and are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Why V47

V46 breadth4 materially repaired the multi-year risk problem without a parameter sweep. Formal V46 status remains HOLD because of one preregistered sign-count gate, but breadth4 passed every other risk/economic check and converted weak years into near-flat behavior while retaining strong 2025-2026 edge.

The next useful evidence had to be fresh. Re-optimizing breadth, HL10 or the 0.05 thresholds on 2021-2026 would be same-sample tuning.

No single short period can authorize promotion by itself.

## Frozen primary

The V47 primary remains exactly the V46 breadth4 mechanism:
- HL10 realized-R EWMA expert router;
- selected expert threshold 0.05;
- breadth health threshold 0.05;
- require >=4 of 5 shadow experts healthy before opening new risk;
- existing entries, exits and stop/risk geometry unchanged;
- research stop-risk <=1.00%;
- V47 itself has no native/external broker orders.

No breadth3/breadth5 ranking is allowed in V47.

## V47 is not another historical parameter search

Do not run a grid over:
- breadth count;
- EWMA half-life;
- score threshold;
- ADX threshold;
- DI rules.

The accepted 2021-2026 sample is considered consumed for those choices.

## Mandatory observability fixes

Before any new evidence-producing run:
- manifest `candidate_count` must reflect actual compile-time candidate count;
- manifest `source_file` / release identity must identify the current source;
- evidence must log exact source SHA and parent SHA chain.

## Fresh shadow diagnostics

V45 post-hoc diagnostics suggested causal price-state ideas such as ADX upper-bound observation and DI direction alignment. These are not active V47 gates.

For every breadth4 trade opportunity V47 should log timestamp, selected expert/source, HL10 scores, healthy count, ADX, DI, direction, shadow pass flags, primary decision and eventual paper/shadow outcome.

## Decision framework

Breadth4 remains the only primary mechanism during V47.

A later price-state gate may be considered only if fresh shadow evidence shows consistent reduction in losing-R without material destruction of positive edge, across more than one market condition, surviving realistic friction and without look-ahead/event-calendar dependency.

## Crisis-regime objective

Desired behavior:
- unhealthy ensemble -> little/no new exposure;
- healthy broad ensemble -> participate enough to retain edge;
- no event-specific war/news exceptions;
- capital preservation is more important than annual sign count.

## Historical V47 execution scope

V47 itself remains research/paper-shadow only and does not add a native broker-order path merely to collect forward evidence.

That restriction is specific to V47. Later V49 moved to native broker-DEMO execution, and ADR-049 explicitly allows production/live research and targets real-capital deployment after readiness evidence.
