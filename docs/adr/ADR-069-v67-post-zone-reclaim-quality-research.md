# ADR-069 — V67 Post-Zone Reclaim Quality Research

Status: research / Strategy Tester only.

REAL-money authorization is false.

## Context

Accepted V66 evidence proved that post-BOS retracement into a cash-feasible zone restores execution frequency, but first-touch execution is too aggressive. In the fixed August LONG benchmark V66 produced positive aggregate PnL, while the bearish SHORT lane was materially negative. A large share of losing trades exited within the first minute, which is consistent with buying or selling the first zone touch before the local sweep/rejection has completed.

The research objective is therefore not a fixed weekly trade count or fixed weekly dollar quota. The objective is stable positive expectancy, repeatable weekly behavior, controlled realized losses, and technically defensible entries. Trade frequency is diagnostic rather than a promotion target.

## Decision

V67 preserves the V66 M1 structural-stop ownership and 30-minute second-stage TTL, but `cash-zone touch != order`.

Execution sequence:

`M15 setup -> regime/quality -> M5 context -> closed-M1 BOS -> freeze M1 structural stop -> cash-zone touch -> deeper penetration without structural breach -> closed-M1 rejection/reclaim -> cash feasibility re-check -> context revalidation -> OrderCheck -> order`.

The first cash-zone touch must return without any order attempt.

### Penetration / reclaim

After first zone touch, price must move closer to the unchanged structural stop until prospective fixed-0.01 risk reaches at most `$0.92`. This is a calibration threshold, not a synthetic stop and not a loss target.

A subsequent closed M1 bar must show a directional rejection/reclaim:

- body at least `0.18 × M1 ATR14`;
- body at least 45% of candle range;
- close in at least the directional 65% of the candle range;
- close must progress beyond the prior M1 close by `0.02 × ATR`;
- close must recover at least `0.12 × ATR` from the adverse zone extreme.

If price prints a new adverse extreme after a confirmation, that confirmation is invalidated and a fresh closed-M1 reclaim is required. A reclaim confirmation expires after five minutes if no valid entry occurs.

### Risk / target

- fixed volume: `0.01`;
- prospective planned stop-risk band: `$0.85-$1.10`;
- emergency cash-loss guard: about `$1.20` as a best-effort market-close layer, not a guaranteed realized cap;
- actual target: `+$3.50`;
- minimum risk/spread ratio: `4.0`;
- the M1 structural stop remains fixed and is never clamped into the risk budget.

The lower planned maximum provides execution/slippage headroom relative to V66. A setup is skipped or waits if the unchanged structural stop cannot fit the cash/spread geometry naturally.

## Direction lanes

LONG and SHORT use mirrored execution mechanics but are evaluated independently. Positive LONG evidence cannot promote a negative SHORT lane.

## Validation

Use exactly the same fixed Model=4 samples used by V66 so the experimental change is entry confirmation, not sample selection:

- four fixed August benchmark weeks, each LONG-only and SHORT-only;
- four previously frozen bearish SHORT weeks;
- total: 12 Model=4 passes.

No new screen or PnL-based window reselection is allowed.

## Required diagnostics

V67 must report:

- stage conversion from micro arm -> zone touch -> penetration -> reversal confirmation -> entry-ready -> sent order;
- invalidation, confirmation reset and expiry reasons;
- LONG and SHORT PnL/PF separately;
- weekly consistency statistics rather than fixed external quotas;
- realized max/average losses;
- losing-trade duration counts within 15/30/60 seconds;
- inherited independent noise-shadow outcomes.

## Safety

- Strategy Tester research only.
- REAL-money authorization is false.
- Do not widen or fabricate the structural stop to force feasibility.
- Do not use fixed weekly trade/profit quotas as promotion gates.
- Do not combine direction-isolated pass sums as if they were concurrent portfolio equity.
