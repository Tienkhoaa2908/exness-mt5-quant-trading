# V34 Parallel Alpha Lab — causal specialist expansion

Date: 2026-08-20
Safety: Strategy Tester / virtual books only. REAL-MONEY LIVE TRADING IS FORBIDDEN. Stop-risk research ceiling remains 1.00% per trade.

## Objective

The current system's strongest bottleneck is opportunity-adjusted alpha, not merely risk control. V34 adds independent candidate families before adding leverage or larger networks.

V34 keeps the accepted V30 execution/accounting engine and adds five candidates driven by a causal Common-Files tape:

1. `v34_smc_ict_causal` — confirmed market structure, BOS, liquidity sweep, recent FVG, displacement and premium/discount state;
2. `v34_price_action_causal` — engulfing/pin structure, breakout, inside-break and compression context;
3. `v34_wyckoff_proxy_causal` — causal range position, spring/upthrust, effort/result and absorption proxies;
4. `v34_tick_microstructure_proxy` — tick-direction imbalance, mid-price path efficiency, M1 direction/efficiency and spread stability;
5. `v34_specialist_confluence` — bounded agreement of at least two specialist families.

The microstructure family is explicitly an **L1/tick-path proxy**, not true L2/L3 order flow. V30 `real_volume=0` means the system must not describe bar-volume features as institutional order flow.

## Causal contract

`bar_features.time` is the OPEN timestamp of the just-closed M15 bar. It is available only at `time + 15 minutes`.

All specialist state is built on closed bars. Decision-bar tape uses an as-of join with:

`feature_available_time <= decision_bar_time`

SMC swing pivots use left/right confirmation, but a pivot becomes usable only on the bar where the right-side confirmation bars have already closed. No future mitigation, future FVG fill, future swing classification or test-period quantile is used.

Pinned 2025-08-01 -> 2026-08-01 causal tape:

- rows: 23,617 plus header;
- SHA-256: `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.

Signal counts in the reference tape:

- SMC/ICT: 1,647 long / 1,600 short;
- Price Action: 3,264 / 2,742;
- Wyckoff proxy: 412 / 749;
- microstructure proxy: 625 / 410;
- confluence: 949 / 813.

## Exact MT5 contract

V34 deterministic tester-only source SHA-256:

`8d3700911e2fe680a2a4b02994680e812825ab6cf517bf509aaa4ac230526a77`

The source is generated from accepted V30 SHA `4222120...` and preserves:

- no native/external broker orders;
- `MQL_TESTER` guard;
- XAUUSDm M15;
- 2 ATR initial stop;
- same 4R / peak-lock exit geometry to isolate entry-family alpha;
- Deposit USD40;
- book 3 continuous USD40 at 1.00% current-balance stop-risk;
- adaptive state after July 2025 restored before the run;
- 2025-08-01 -> 2026-08-01 exact tick replay.

One MT5 pass evaluates all existing 12 candidates plus all five new specialists in parallel. This is substantially more informative than running five independent Python PnL simulations because every candidate sees the same tester ticks/spread/accounting engine.

## Intra-trade telemetry

V34 also writes `intra_trade_m15.csv` for norm10k and continuous-USD40 books while positions are open. It records path state before the first-tick exit processing of each new M15 bar:

- candidate/family/book/entry time/direction;
- age seconds;
- current unrealized R;
- peak R and MAE;
- current giveback from peak;
- stop R and TP R;
- balance/risk cash/signal source.

Market features are not duplicated in this file; V36 joins them causally by telemetry bar time.

## Acceptance

V34 is a development screen. A specialist is interesting only if exact MT5 shows positive expectancy/PF with reasonable monthly breadth and its entry-time/direction overlap is not almost identical to the accepted EMA/momentum families.

The purpose is not to declare SMC/ICT/Wyckoff labels profitable by definition. Each family must earn its place empirically.
