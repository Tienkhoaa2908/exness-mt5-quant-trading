# V38 Fast Harvest Lab — exact-MT5 development plan

Date: 2026-08-21

## Why V38 exists

The accepted system has demonstrated positive exact-MT5 edge, but the next bottleneck is not another broad entry-model sweep. The working hypothesis is that XAUUSD intraday opportunities may benefit from shorter time-in-market and more aggressive profit capture: enter from the existing causal baseline/router, harvest the high-probability impulse, and leave before edge decay/giveback.

V38 is an incremental overlay. It does **not** delete, replace, or retune the accepted baseline, V32 keep60 challenger, V34 specialist research, or V36 sequence-AI evidence.

## Frozen references preserved

- `adaptive_ewma_hl8_thr0` remains the exact control.
- `adaptive_ewma_hl8_thr0 + DeepMLP keep60` remains the frozen risk-efficiency challenger. V38 does not retune its entry threshold.
- V34 specialist candidates remain in the generated source unchanged so control reproducibility is testable.
- V36 GRU/TCN/Transformer findings remain accepted research evidence. V38 adds higher-resolution telemetry for a later short-horizon AI controller rather than discarding V36.

## Safety

- Strategy Tester only.
- No native/external broker orders.
- No Martingale, grid, or loss doubling.
- Existing 2ATR stop geometry and book risk fractions are unchanged.
- Research stop-risk ceiling remains 1.00%/trade.
- The six fast arms are independent **virtual research books**, not permission to stack six real positions. Any later combined policy must keep aggregate same-symbol stop-risk <=1.00%.

## Exact V38 arms

All six V38 candidates clone the same `adaptive_ewma_hl8_thr0` entry/router configuration. Only exit timing differs.

1. `v38_adaptive_fast_tp0p50`
   - immediate virtual close when current R >= +0.50R.
2. `v38_adaptive_fast_tp0p75`
   - immediate virtual close when current R >= +0.75R.
3. `v38_adaptive_fast_tp1p00`
   - immediate virtual close when current R >= +1.00R.
4. `v38_adaptive_fast_gb0p25_after0p75`
   - armed after MFE >= +0.75R;
   - close while still profitable if current R <= MFE - 0.25R.
5. `v38_adaptive_velocity_decay_after0p50`
   - causal 60-second R samples;
   - armed after MFE >= +0.50R and current R >= +0.25R;
   - after at least two completed one-minute deltas, close when current delta <= -0.05R and previous delta <= +0.05R.
6. `v38_adaptive_timebox30m`
   - close at the first tick at/after 30 minutes from entry, regardless of sign.

Hard-stop processing remains before every V38 fast-exit rule. Existing protection/TP logic remains after the V38 overlay if no fast rule fires.

This is a bounded hypothesis set, not a large threshold sweep.

## Period and exact-MT5 contract

Primary development comparison:

- XAUUSDm
- M15 entry engine
- Every-tick tester mechanics
- 2025-08-01 through 2026-08-01
- Deposit USD40
- leverage 1:200
- continuous USD40 decision book
- state starts from accepted state-after-chunk1
- month-end liquidation retained
- one-position-per-candidate behavior retained

The accepted V34 control must reproduce before any V38 arm is interpreted:

- 12 monthly rows;
- 563 continuous-USD40 trades;
- final balance USD107.432645;
- accepted monthly trade counts and monthly ending-capital path.

A control mismatch invalidates the run.

## Metrics

Return remains necessary but no longer sufficient. V38 explicitly measures speed/capture:

- ending capital / total return;
- geometric monthly return;
- max MTM drawdown;
- return/DD;
- AvgR and sumR;
- profit factor;
- trade count;
- turnover;
- average giveback R;
- MFE;
- capture efficiency;
- mean / median / p90 holding minutes;
- sumR per market hour;
- positive months and >=15% months.

Development qualification requires a fast arm to preserve at least 90% of control ending capital, not exceed control max DD, and reduce median holding time by at least 40%. This is not a promotion rule; it is only a bounded development screen.

## M1/tick telemetry for the next AI layer

V38 writes `intra_trade_m1_fast.csv` from the untouched control candidate (`adaptive_ewma_hl8_thr0`) for norm and continuous-USD40 books.

Each row is emitted causally at the first tick of a new minute using the completed prior-minute tick aggregate and the current available mark. Fields include:

- current R, MFE, MAE, giveback;
- one-minute delta R;
- tick count;
- tick-direction imbalance;
- directional mid-price net move in R;
- absolute tick path in R;
- one-minute mid range in R;
- mean/max spread points;
- age since entry.

This data is intended for the next short-horizon AI controller. The target should be continuation/giveback over the next 5–15 minutes, not long-horizon “hold forever” prediction.

No offline reconstructed PnL is promotion evidence. Any AI-derived exit rule must return to exact MT5.

## Interpretation discipline

A lower AvgR can still be acceptable if shorter holding time, lower DD, lower giveback and larger opportunity throughput improve exact account economics. Conversely, a high win rate or fast median exit is not enough if turnover/cost destroys total return.

The current 15%/month objective remains aspirational. V38 must not increase per-trade risk to force it.
