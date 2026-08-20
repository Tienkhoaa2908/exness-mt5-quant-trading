# V35 AI all-expert meta-router

Date: 2026-08-20

V35 is trained only after V34 exact-MT5 specialist outcomes exist.

## Expert pool

The router combines ten base experts rather than replacing the existing trading system:

Existing accepted families:

- EMA pullback;
- MACD;
- BOS/FVG;
- Trend20;
- slow multi-horizon momentum.

New V34 families:

- causal SMC/ICT;
- causal Price Action;
- Wyckoff proxy;
- tick/microstructure proxy;
- specialist confluence.

## Learning protocol

Labels come from **V34 exact-MT5 norm-book `r_multiple`**, not Python price reconstruction.

For every test month February-July 2026:

1. previous month is calibration;
2. training labels require `exit_time < calibration_month_start`;
3. duplicate `(entry_bar,direction)` opportunities receive inverse multiplicity weight;
4. models: ExtraTrees + HistGradientBoosting + MLP 64-32-16;
5. ensemble predicts expected R for each active expert opportunity;
6. only the highest-scored expert on a bar may become the router action;
7. previous-month median predicted-R is the frozen threshold for the following month;
8. no test-month threshold peeking.

Input state includes causal market/tick features, V34 specialist scores, existing EWMA expert state and one-hot source identity.

The resulting router tape contains only direction/source/score/threshold. Offline predictions are not PnL evidence.

## Exact MT5 return

V35 source is generated from the deterministic V34 source and adds one independent router candidate:

`v35_ai_all_expert_meta_router`

Pinned deterministic source SHA-256:

`663d97b9345341aa98827e5da31ad441792f944d7c597b7a91bd94c6485e6709`

The final February-July 2026 economics are again produced by MT5 with Deposit USD40, continuous 1% book and the accepted state-after-January checkpoint.

V35 does not authorize live trading. A development winner still requires frozen fresh chronological confirmation.
