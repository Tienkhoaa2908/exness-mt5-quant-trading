# ADR-061 — V59 Integrated Bidirectional RR Research

Status: ACCEPTED FOR RESEARCH IMPLEMENTATION

## Context

V57/V58 exposed two separate problems that must be solved together rather than by stacking isolated filters:

1. The selected V52 candidate is direction-capable in code, but the 2026-08-24..2026-08-28 selected-book sample emitted nine LONG trades and no SHORT trades. This is a sample outcome, not proof that the engine is long-only; however promotion must demonstrate symmetric behavior in bearish windows instead of assuming it.
2. The inherited exit geometry is `stop_atr=2.0`, `tp_r=4.0`, with a giveback/protective-stop policy that often realizes much less than the nominal 4R target. In the selected nine-trade sample, winners realized about 0.56R..1.19R while losers commonly realized about -1R.
3. With fixed 0.01 lot on XAUUSDm and a USD40 book, the inherited 2ATR stop can imply a very large cash loss per stopped trade. V59 keeps lot 0.01 for the requested research path, but it must not treat a structurally invalid or unaffordable stop as acceptable merely to force an entry.
4. SMC/ICT concepts such as FVG, BOS/CHoCH, liquidity sweep and order blocks are useful as directional/structure evidence, not standalone guarantees. They must be causal and combined with trend, momentum, location and execution cost.

## Decision

V59 is one integrated two-sided engine, not a selector among separate bots.

### 1. Symmetric direction engine

The same scoring rules are evaluated for LONG and SHORT with mirrored inequalities. No feature may be long-only unless explicitly documented and separately tested.

Directional evidence groups:

- H4 regime: fast/slow trend and slope.
- H1 trend: EMA structure/slope and price location.
- M15 trigger: confirmed BOS/CHoCH, displacement/FVG, liquidity sweep/reclaim, pullback/retest.
- Momentum: ADX/+DI/-DI, MACD histogram/slope.
- Anti-chase/location: RSI2, RSI14, distance from fast EMA in ATR units, premium/discount relative to recent swing range.
- Execution quality: spread cash, stop geometry, margin feasibility.

The actual decision is an integrated directional score. Component scores remain logged for attribution.

### 2. Do not force direction balance

A bullish week may legitimately contain only LONG trades and a bearish week may legitimately contain only SHORT trades. V59 must prove that the same code can trade both directions by testing at least one bullish and one bearish historical window. It must not manufacture opposite-direction trades merely to make counts look balanced.

### 3. Fixed lot remains 0.01 in V59 research

`FIXED_LOT=0.01` remains an invariant for this research branch.

Risk reduction therefore comes from better entry selection and stop geometry, not from reducing lot size.

### 4. Structural stop + cash feasibility

The initial stop is derived from causal invalidation structure first (recent confirmed swing / BOS-FVG invalidation with an ATR buffer). V59 then calculates the exact cash loss of that structural stop at 0.01 using `OrderCalcProfit`.

If the structural stop requires cash loss above the preregistered research cap, V59 rejects the setup rather than:

- widening risk silently;
- moving the stop inside invalidation merely to fit the budget; or
- reducing lot below 0.01.

Research must report how many otherwise-valid trades are rejected by this constraint.

### 5. Reward-to-risk research

The inherited nominal 4R target is not assumed optimal.

V59 compares, in one evidence pass where possible:

- 2.0R hard target;
- 2.5R hard target;
- 3.0R hard target;
- regime-adaptive 2R/3R target.

Breakeven win rates before costs are 33.3%, 28.6% and 25.0% respectively. Selection is based on realized expectancy after spread/commission/slippage, not on nominal RR alone.

### 6. Exit ladder

V59 removes the inherited `lock 50% of peak after 1R` as the default research exit. The research ladder is:

- before +1R: original structural SL;
- at +1R: optional breakeven only when structure/volatility allows;
- at +1.5R: optional lock +0.5R;
- at +2R: optional lock +1R for 2.5R/3R variants;
- hard TP at the selected target;
- structure-failure / opposite CHoCH may close early only if preregistered and measured separately.

Because 0.01 is the broker minimum on the target Standard symbol, V59 does not assume partial close below 0.01.

### 7. Causality requirements

- Closed bars only for trend/structure features.
- Swing points become tradable only after confirmation bars exist.
- FVG/BOS/CHoCH/order-block state cannot use future bars.
- No same-bar future high/low to decide an entry.
- No seed from the end of a test period may be used to replay its beginning.

### 8. Validation plan

The 2026-08-24..2026-08-28 week remains a diagnostic window, not a promotion dataset.

V59 must additionally test broader cached real-tick windows containing both rising and falling XAUUSD regimes. Fast vectorized/bar-level screening may be used to reject weak variants first; final candidates require MT5 `Model=4` real-tick validation.

Report separately:

- LONG trades / SHORT trades;
- wins / losses by direction;
- gross profit / gross loss / net USD;
- average win R / average loss R;
- profit factor;
- max drawdown;
- SL exits / TP exits / early exits;
- nominal RR vs realized RR;
- spread/commission/slippage;
- rejected-by-structural-risk count;
- rejected-by-model count;
- directional score attribution.

## Non-goals

- V59 is not authorization for REAL-money activation.
- V59 does not claim that FVG/ICT/SMC signals are predictive by themselves.
- V59 does not force a trade simply because 0.01 is executable.
- V59 does not optimize only the 24..28 August week and then call that robust.
