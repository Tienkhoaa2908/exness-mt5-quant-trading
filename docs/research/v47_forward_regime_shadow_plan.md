# V47 Forward Regime-Shadow Validation Plan

Date: 2026-08-22

## Why V47

V46 breadth4 materially repaired the multi-year risk problem without a parameter sweep. Formal V46 status remains HOLD because of one preregistered sign-count gate, but breadth4 passed every other risk/economic check and converted 2022/2023 into near-flat years while making 2024 positive and retaining strong 2025-2026 edge.

The next useful evidence must be fresh. Re-optimizing breadth, HL10 or the 0.05 thresholds on 2021-2026 would be same-sample tuning.

## Frozen primary

The V47 primary remains exactly the V46 breadth4 mechanism:
- HL10 realized-R EWMA expert router;
- selected expert threshold 0.05;
- breadth health threshold 0.05;
- require >=4 of 5 shadow experts healthy before opening new risk;
- existing entries, exits and stop/risk geometry unchanged;
- research stop-risk <=1.00%;
- no native/external broker orders;
- no live authorization.

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
- manifest `candidate_count` must reflect the actual compile-time candidate count, not stale literal 23;
- manifest `source_file` / release identity must identify the current V47/V46-derived source;
- evidence must log exact source SHA and parent SHA chain.

## Fresh shadow diagnostics

V45 post-hoc diagnostics suggested two causal price-state ideas:
- ADX upper-bound observation around 30;
- direction/DI alignment: LONG requires +DI > -DI, SHORT requires -DI > +DI.

These are not active V47 gates.

For every breadth4 trade opportunity, V47 should log at minimum:
- timestamp;
- selected expert/source;
- selected HL10 score;
- healthy expert count;
- all five HL10 scores if feasible;
- ADX;
- +DI / -DI;
- direction;
- whether ADX<=30 would pass;
- whether DI alignment would pass;
- primary breadth4 decision;
- eventual paper/shadow R outcome.

The purpose is to estimate incremental value on fresh observations without changing the primary decision.

## Decision framework

Breadth4 remains the only primary mechanism during V47.

A later price-state gate may be considered only if fresh shadow evidence shows:
- consistent reduction in losing-R, not merely fewer trades;
- no material destruction of positive breadth4 edge;
- improvement is visible across more than one market condition/month;
- effect survives realistic friction;
- no look-ahead or event-calendar dependency.

No single short period can authorize promotion by itself.

## Crisis-regime objective

The system is not required to make money in every crisis or transition period.

Desired behavior:
- unhealthy ensemble -> little/no new exposure;
- healthy broad ensemble -> participate aggressively enough to retain edge;
- no event-specific war/news exceptions;
- capital preservation is more important than annual sign count.

## Safety / deployment meaning

V47 remains research/paper-shadow only. It does not authorize real-money trading.

No native/external broker order path may be added merely to collect forward evidence. If forward observation is needed, use a paper/shadow accounting path or another tester-safe mechanism.
