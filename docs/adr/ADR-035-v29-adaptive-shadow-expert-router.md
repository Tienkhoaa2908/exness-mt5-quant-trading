# ADR-035 — V29 adaptive shadow-expert router

## Decision
Reject fixed one-dimensional `range percentile -> strategy family` routing after V28 later-confirmation reversal.

V29 instead runs independent shadow experts (EMA, MACD, BOS/FVG, Trend, slow 16h+24h momentum) and updates causal realized-R EWMAs from the normalized control books. Adaptive candidates select only among experts currently emitting valid signals. A fast5-vs-slow20 divergence probe is included as a bounded change-severity experiment; it changes adaptation speed, not trade direction.

## Frozen catalog
12 candidates × 4 virtual books × 18 independent monthly accounting resets. Adaptive EWMA half-lives: 8/10/12; minimum scores 0 or +0.05R. Slow momentum decisions only at server 00:00/08:00, 16h+24h agreement, 8h timebox, stop 2ATR, TP4R; both no-peak-lock and peak-lock controls are included.

## Validation
Exact stateful MT5 tick replay is required because shadow-expert exits alter causal adaptive weights. Offline ledger screening is discovery only. Adaptive state is carried sequentially across the three tester chunks and runner retries restore the exact pre-chunk state.

## Safety
Tester-only virtual books. REAL-MONEY LIVE TRADING = FORBIDDEN. No native broker orders. Stop-risk research ceiling 1.00%/trade.
