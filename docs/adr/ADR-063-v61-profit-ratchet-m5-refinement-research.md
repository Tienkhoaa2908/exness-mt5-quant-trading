# ADR-063 — V61 Profit Ratchet + M5 Refinement Research

Status: research-only, tester-only.

## Context

V60 evidence materially improved the loss distribution: actual MT5 real-tick validation produced 5 completed round trips, 3 wins and 2 losses, +$4.22 net, PF 3.24, average winner about +$2.03, average loser about -$0.94, and maximum realized single loss -$1.00. V60 evidence also showed one nominally feasible setup with only $0.05 structural risk was rejected by the broker with retcode 10016, demonstrating that an arbitrarily tiny stop is not a valid way to reduce losses.

The same six real-tick shadow setups produced +$4.13 for the $2 target, +$7.13 for the $3 target, and approximately flat performance for $4. This is a hypothesis-generation sample, not sufficient evidence to optimize a final target.

## Decision

V61 keeps fixed lot 0.01 and strict H4/H1 directional alignment. It introduces an explicit structural-risk band of $0.75 to $1.25. Stops below the band are rejected as too tight; stops above the band remain rejected as too expensive.

The actual tester target becomes $3. When unrealized PnL reaches +$2, V61 attempts a profit ratchet that moves the protective stop to a price corresponding to at least +$1, subject to broker stop/freeze geometry. It does not use partial close.

V61 adds causal M5 refinement using closed M5 bars only. When M5 trend and confirmed micro-structure agree with the H4/H1 direction, the engine may replace the farther M15 structural stop with a closer confirmed M5 swing invalidation. This is intended to increase the number of structurally valid setups without increasing the maximum cash loss.

Before an actual tester order is sent, V61 runs OrderCheck and records any preflight block. This directly addresses the V60 invalid-stop rejection path.

The shadow evaluator continues to record $2, $3 and $4 targets so the profit-ratchet hypothesis can be compared without multiple strategy definitions.

## Constraints

- Fixed lot remains 0.01.
- H4 and H1 must align with trade direction.
- No Martingale, grid, averaging down or position doubling.
- No partial close assumption below broker volume granularity.
- M5 data is causal: CopyRates starts at closed bar shift 1.
- Window selection remains independent of PnL.
- V61 is STRATEGY TESTER ONLY and is not authorization for REAL-money activation.

## Next gate

Windows MetaEditor must compile both V61 experts with 0 errors and 0 warnings. Model=4 real-tick evidence must show whether M5 refinement increases executable setup count, whether OrderCheck eliminates invalid-stop submissions, and whether the +$2 to +$1 profit ratchet improves realized expectancy versus V60.
