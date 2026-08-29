# ADR-059 — V57 fixed-0.01 trend + SMC research replay

Date: 2026-08-29  
Status: Accepted for tester-only research

## Context

V56 replayed XAUUSDm M15 for 2026-08-24 through 2026-08-28 with broker real ticks and found nine selected-candidate virtual entries but zero broker OPEN requests. The structural blocker was volume granularity: the research book emitted 0.0001–0.0002 standard-lot-equivalent volume while the Standard-account symbol reported `SYMBOL_VOLUME_MIN=0.01` and `SYMBOL_VOLUME_STEP=0.01`.

The operator explicitly requires 0.01 lot for the next research iteration and wants the model to reduce bad trades by improving entry quality rather than by reducing lot size. V57 therefore evaluates 0.01 as a hard research constraint and reports its USD consequences directly.

V56's nine virtual trades, naively scaled to 0.01 while preserving the same entry/exit path, are a baseline diagnostic only: 4 wins, 5 losses, `-1.98597R`, and approximately `-$45.39595` on a $40 starting balance. This scaling is not a claim that a real account would have followed the same path; margin, stop-out, spread, fills and guard behavior can change the realized result.

## Decision

Create V57 on the isolated branch `agent/v57-fixed001-trend-smc-research`. V57 is tester-only and cannot be attached to a live chart.

V57 keeps the selected parent candidate `v52_b4_or_b3_trend_bos` and the V55 execution/reconciliation stack, but changes research entry qualification and order volume as follows:

- broker order volume is fixed at exactly `0.01` lot;
- broker min/max/step compatibility, stop geometry and available-margin checks remain mandatory;
- no risk-based volume down-sizing is used in the V57 open path;
- the actual simulated broker entry uses the pre-registered `trend_smc_balanced` gate;
- other gates are shadow-scored in the same MT5 run so they do not require separate real-tick tester passes.

V57 does **not** authorize REAL deployment. The fixed 0.01 choice can imply very large percentage loss relative to a $40 balance; the tester must expose that in USD and percentage terms rather than hide it.

## Causal trend and SMC feature set

V57 adds confluence features without using future information at the decision timestamp:

1. **H1 trend regime** — EMA50 vs EMA200 plus EMA50 slope. Trade direction must agree with H1 trend for all promoted research gates.
2. **H4 trend regime** — EMA20 vs EMA50 plus closed H4 price alignment.
3. **ADX / DI** — ADX >= 18 and directional DI alignment as trend-strength confirmation.
4. **Confirmed H1 swing structure** — two closed H1 bars on each side are required before a swing pivot can be used. A pivot is therefore usable only after confirmation, never retroactively.
5. **BOS / CHoCH proxy** — a close beyond the latest confirmed swing level in the trade direction.
6. **Displacement FVG** — three-candle H1 imbalance with middle-candle body >= 0.60 ATR and gap >= 0.08 ATR.
7. **Liquidity sweep / reclaim** — recent H1 excursion beyond a confirmed swing followed by a close back through the level.
8. **MACD histogram**, **RSI14 trend band**, and an **RSI2 extreme-entry penalty**.

The SMC definitions were informed by public implementations such as `joshyattridge/smart-money-concepts`, but V57 is independently implemented to preserve this project's causal/no-look-ahead requirements. In particular, public swing algorithms that identify a pivot with future bars must not mark that pivot as tradable before those future bars have closed.

## Pre-registered gates

All gates are evaluated on each selected-candidate virtual entry in one run:

- `baseline_fixed001`: every selected-candidate entry, scaled to 0.01 for shadow comparison;
- `trend_h1`: H1 trend must align;
- `trend_adx`: H1 trend + ADX/DI alignment;
- `trend_structure`: H1 trend + confirmed structure or BOS/CHoCH alignment;
- `trend_smc_balanced`: H1 trend + confluence score >= 5;
- `trend_smc_strict`: H1 trend + confluence score >= 6.

Score weights are fixed before the replay: H1 trend aligned +3 / opposite -3; H4 trend +1; ADX/DI +1; structure +1; BOS/CHoCH +1; FVG +1; liquidity sweep +1; MACD +1; RSI14 trend-band +1; RSI2 extreme penalty -1.

The balanced gate is the only gate that sends simulated broker orders. The remaining gates are diagnostic shadow filters. Same-week comparison is exploratory and cannot by itself authorize promotion.

## Faster backtest protocol

V56 already produced and verified the adaptive state at the start of 2026-08-24. V57 commits that exact state with SHA256:

`7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259`

Its provenance is the accepted V56 evidence ZIP SHA256:

`a9ec9c8cb0f7402c6ffac603fc187d79ca7aa281f84e0c0fdf8310bac3a23c55`

V57 therefore skips V56's 2026-08-02→2026-08-23 warm-forward phase and runs one Strategy Tester pass only:

- symbol: XAUUSDm
- timeframe: M15
- from: 2026-08-24
- to: 2026-08-29
- tester model: 4, every tick based on real ticks
- deposit: USD 40
- leverage: 1:200
- optimization: off
- cloud: off
- visual: off

Existing MT5 tick/history cache may reduce repeat-run time, but no specific runtime is guaranteed.

## Capital-limit handling in research

Daily-loss and maximum-drawdown thresholds are emitted as `V57_WOULD_HALT` telemetry instead of terminating the research pass. This is intentional so all candidate entries can be measured over the week with fixed 0.01. It is tester-only behavior and must never be ported to a REAL runtime without a separate ADR.

Spread, stale-data, broker stop geometry, ownership/reconciliation and margin guards remain active.

## Evidence and reporting

V57 must report both shadow and actual simulated-broker results:

- trades / wins / losses;
- net and gross USD PnL;
- profit factor;
- ending-balance and return proxy for fixed 0.01 shadow paths;
- max balance drawdown proxy and whether the $40 shadow balance crossed zero;
- actual broker deal PnL including profit, commission, swap and fee;
- per-trade `V57_TRADE_REPORT.csv` with gate flags, trend/SMC features and fixed-0.01 shadow PnL;
- fixed-0.01 stop-risk cash, equity-risk percentage and margin telemetry;
- source SHA, MetaEditor compile log, tester config and CRC-verified evidence ZIP.

A gate that looks better on this single week requires broader out-of-sample real-tick validation before any production decision.
