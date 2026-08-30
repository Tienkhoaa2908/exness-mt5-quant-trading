# ADR-068 — V66 Post-BOS Cash-Zone Research

Status: research / Strategy Tester only.

## Decision

V65 proved that M1 microstructure can own a structural stop, but 202 of 205 confirmed micro candidates were rejected because the market price at closed-M1 BOS was already too far from that stop. V66 therefore separates **confirmation** from **execution**.

A closed-M1 `PULLBACK_SWEEP_BOS` or `BREAKOUT_RETEST_BOS` confirmation arms a second-stage setup with a fixed structural stop. The EA does not widen or clamp that stop. On subsequent real ticks it waits until current price naturally produces planned fixed-0.01 risk within `$0.85-$1.25` and risk/spread `>=4`. Only then does it revalidate H4/H1, entry-quality, trend-quality and M5 context, run OrderCheck, and send the trade.

## Second-stage lifecycle

`M15 setup -> M5 context -> closed-M1 BOS -> fixed M1 micro stop -> MICRO_ENTRY_ARM -> tick retracement/rebound -> cash-feasible zone -> revalidation -> order`.

Second-stage TTL is 30 minutes from first micro arm and is not reset. Structural-stop breach invalidates the setup. If price remains above the cash-risk cap, the setup waits. If it moves very close to the stop, it may wait for a rebound back into the feasible risk/spread zone; the stop itself is never moved to manufacture feasibility.

Telemetry includes `MICRO_ENTRY_ARM`, `MICRO_ENTRY_REFRESH`, `MICRO_ENTRY_WAIT`, `MICRO_ENTRY_ZONE_TOUCH`, `MICRO_ENTRY_INVALIDATE`, `MICRO_ENTRY_EXPIRE`, `MICRO_ENTRY_BLOCK`, and `MICRO_ENTRY_END`.

## Frozen contract

- XAUUSDm M15;
- fixed lot `0.01`;
- planned structural risk `$0.85-$1.25`;
- emergency cash guard about `$1.20`;
- actual target `+$3.50`;
- minimum risk/spread ratio `4.0`;
- M5 context only; M1 micro stop owns invalidation;
- 30-minute micro-entry TTL;
- Strategy Tester only; REAL-money authorization false.

## Validation

Use exactly the same 12 Model=4 windows as accepted V65: four August weeks run LONG-only and SHORT-only, plus the four frozen bearish SHORT windows selected by V64 without PnL. No new screen and no PnL reselection are permitted.

The research objective remains higher expectancy with roughly three quality trades per week and week-level profit in the vicinity of `$6` when conditions support it. This is a KPI, not a guaranteed result and not a selection criterion.

## Rejected alternatives

- Widening the `$1.25` structural-risk cap: rejected because it violates the small-loss objective and V65 shows the timing problem directly.
- Clamping the structural stop toward entry: rejected because it creates a non-structural stop.
- Adding more indicators: rejected because V65 produced 205 confirmed micro candidates; signal scarcity is not the current bottleneck.
- Selecting new profitable windows: rejected as post-outcome sample selection.
