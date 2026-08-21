# V39 Selective Harvest Controller — research plan

Date: 2026-08-21

## Motivation

V38 exact MT5 rejects unconditional fast exits, but establishes a useful boundary: fixed TP1R reaches USD104.42 versus USD107.43 control while cutting median hold time by ~40%. The remaining loss is concentrated in right-tail/trending opportunities. Therefore the next problem is not `how fast can we exit?`; it is `which >=1R winners should be harvested now versus allowed to continue?`.

V39 preserves all accepted prior evidence:

- `adaptive_ewma_hl8_thr0` remains the control and entry/router source of truth;
- V32 DeepMLP keep60 remains frozen as a separate entry-risk-efficiency challenger;
- V36 Transformer sequence classification remains the strongest accepted AI exit clue;
- V38 M1/tick telemetry is an additional short-horizon state source, not a replacement for V36;
- V34 SMC remains a separate research-only specialist and is not merged into V39 risk.

## Research question

After the control position is already approximately +1R unrealized, can a causal AI/regime controller identify giveback-prone states while preserving the rare large trend winners that make fixed TP1R underperform the baseline?

## Stage A — read-only diagnostics

No MT5 intervention in Stage A.

### A1. Preserve V36 benchmark

Retain the accepted V36 targets and causal sequence contract. Do not relabel or retune the existing Feb-Jul evidence merely to improve headline metrics.

### A2. Add V38 M1 short-horizon representation

Use only the untouched V38 control telemetry `intra_trade_m1_fast.csv`.

Candidate causal features:

- current unrealized R, MFE, MAE, giveback;
- age/time-in-trade;
- one-minute delta R and short rolling R velocity/acceleration;
- completed prior-minute tick count and tick-direction imbalance;
- mid-price net move, absolute path and range in R units;
- mean/max spread;
- direction and existing causal market/regime state where available.

Do not call these features true order flow; they are L1/tick-path proxies.

Short-horizon auxiliary labels may examine 5–15 minute continuation and giveback, but economic promotion may not use reconstructed subset PnL.

### A3. Tail-preservation objective

The primary error is **false harvest of large winners**, not ordinary classification error. Report:

- first-trigger avoided giveback;
- percentage of selected triggers that later finish below trigger R;
- foregone R on selected right-tail winners;
- monthly stability;
- trigger coverage;
- results by source family (EMA, slow momentum, trend, BOS/FVG, MACD);
- results by direction/regime.

A model with higher global AUC but repeated catastrophic false exits on large winners is rejected.

## Stage B — bounded exact-MT5 intervention

Only if Stage A produces a stable selective signal.

The first exact policy must be narrow:

- control entry/router unchanged;
- initial stop/risk unchanged;
- action allowed only after current unrealized R >= +1.0R;
- AI may choose `HARVEST_NOW` or `KEEP_BASELINE_EXIT`;
- no new entry, no position stacking, no increased stop-risk;
- if AI does not fire, the accepted baseline protection/TP remains untouched.

Preferred implementation is tester-side ONNX inference. MQL5 supports ONNX session creation, explicit input/output shapes and `OnnxRun`; any model must pass Python-vs-MQL numerical parity before economic testing.

## Causal deployment options

Two legitimate development options are allowed:

1. **Frozen model:** train strictly before the exact test window and keep weights/threshold fixed.
2. **Walk-forward monthly models:** each month model is trained only from fully exited prior data, with model/threshold frozen before that month begins; the EA selects the preregistered model by calendar month.

Do not precompute a trade-key decision tape from the baseline path and replay it after interventions. Early exits alter later entries and state, so such a tape would be path-invalid.

## Required gates before exact MT5

- no train/test overlap by trade;
- train-only normalization;
- sequence masking causal and deterministic;
- model export deterministic enough to reproduce inference;
- ONNXRuntime/PyTorch parity on held samples;
- MQL5 ONNX smoke test and Python-vs-MQL parity;
- tester-only guard present;
- no `OrderSend`, `CTrade` or external broker-order path;
- accepted V34/V38 control source reproduced before modification;
- MetaEditor compile 0/0.

## Economic acceptance rule

A selective-harvest arm is not accepted merely because hold time falls.

It must improve or nearly preserve absolute return while materially improving at least one of:

- max drawdown;
- return/DD;
- AvgR/PF;
- turnover-adjusted return;
- time-in-market efficiency,

without a material increase in turnover or repeated monthly right-tail destruction.

Any development winner is frozen before a genuinely fresh chronological confirmation.

## Safety

Research stop-risk remains <=1.00% per trade. Same-symbol aggregate risk must remain <=1.00% if any future agents are combined. PAPER/DEMO only after gates. REAL-MONEY LIVE TRADING remains forbidden.
