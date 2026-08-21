# V39 Selective Harvest Controller — research plan

Date: 2026-08-21

## Motivation

V38 exact MT5 rejects unconditional fast exits but identifies a useful boundary: fixed TP1R reaches USD104.42 versus USD107.43 control while cutting median hold time by about 40%. The remaining loss is concentrated in right-tail/trending opportunities. Therefore the next problem is not `how fast can we exit?`; it is `which >=1R winners should be harvested now versus allowed to continue?`.

V39 preserves prior evidence:

- `adaptive_ewma_hl8_thr0` remains the control and entry/router source of truth;
- V32 DeepMLP keep60 remains frozen risk-efficiency evidence;
- V36 Transformer remains the strongest accepted sequence exit-state clue;
- V38 M1/tick telemetry adds short-horizon state, not true L2/L3 order flow;
- V34 SMC remains a separate research-only specialist.

## Stage A — offline/read-only

Stage A does not launch MT5/MetaEditor and does not intervene in the baseline path. Its outputs are diagnostic path labels only, not economic PnL.

### Decision zone

Only rows with current unrealized R >= +1.0R are eligible.

### M1 feature block

The Stage-A model uses causal V38 control telemetry:

- current R, MFE, MAE and giveback;
- one-minute delta R;
- 3/5/15-minute rolling R velocity;
- short R acceleration and giveback change;
- completed-minute tick count and direction imbalance;
- mid-price net move, absolute path and range in R units;
- spread mean/max;
- age/time-in-trade and direction.

These are L1/tick-path proxies, not order-book/order-flow data.

### Labels

Two separate binary targets are used:

- giveback: original final R <= current R - 0.25R;
- right tail: future max R >= max(current R + 0.75R, 2.0R).

The M1 harvest score is `P(giveback) * (1 - P(tail))`.

### Chronological thresholding

For each test month:

- training data must be fully exited before the trailing calibration window;
- calibration window = prior 2 months;
- threshold = calibration 85th percentile of harvest score;
- no threshold sweep/tuning on the test month;
- first trigger per trade only.

### V36 fusion

Accepted V36 Transformer predictions are not retrained or used as a target for a second model. They are an external tail-preservation veto.

Fusion trigger requires:

- M1 harvest score >= frozen calibration threshold;
- V36 `p_hold <= 0.15`;
- latest causal V36 state age <=75 minutes.

This avoids the invalid design where limited Feb-Jul V36 OOS probabilities become training features and collapse chronological coverage.

## Tail-preservation gate

Primary error is false harvest of big winners. Report at minimum:

- first-trigger avoided giveback;
- finish-below-trigger rate;
- foregone right-tail extension;
- false-big-winner rate;
- monthly stability;
- trigger coverage;
- giveback/tail AUC;
- source-family and direction/source breakdowns.

Stage A only passes its diagnostic gate if:

- >=4 chronological folds;
- >=30 first triggers;
- aggregate trigger coverage between 3% and 35%;
- avoided giveback is positive in at least 75% of folds;
- mean avoided giveback is positive;
- mean false-big-winner rate <=20%.

A model with attractive global AUC but repeated catastrophic false exits is rejected.

## Stage B — exact-MT5 intervention, only after Stage A pass

Stage B is not implemented by this milestone. If Stage A passes, the first Stage-B policy must remain narrow:

- control entry/router unchanged;
- initial stop/risk unchanged;
- action allowed only after current R >= +1.0R;
- action is `HARVEST_NOW` or `KEEP_BASELINE_EXIT`;
- no new entry, no position stacking, no increased stop-risk;
- if AI does not fire, accepted baseline protection/TP remains untouched.

A development winner must be frozen before exact MT5. Do not replay a baseline trade-key decision tape after interventions because early exits change future entry/state/path.

Tester-side ONNX is preferred only after Python/ONNXRuntime/MQL5 numerical parity gates are available.

## Required Stage-B gates

- no train/test trade overlap;
- train-only normalization;
- deterministic causal feature masking;
- frozen model/threshold before the test period;
- ONNX export parity if ONNX is used;
- MQL5 ONNX smoke/parity test;
- tester-only guard;
- no native/external broker-order path;
- accepted V34/V38 control reproduction;
- MetaEditor 0 errors / 0 warnings;
- exact MT5 remains the economic judge.

## Packaging

Workflow is one run -> one ZIP. V39 runner exports evidence, summary, fold metrics, first triggers, source/direction breakdowns, code snapshots and `bundle_manifest_sha256.txt` into one `v39_selective_harvest_stage_a.zip`.

Standard helpers:

- `scripts/package_mt5_research.cmd`
- `scripts/package_mt5_research.py`
- `scripts/analyze_mt5_research_bundle.py`

## Safety and target discipline

Research stop-risk remains <=1.00% per trade. Same-symbol aggregate risk must remain <=1.00% if future agents are combined. PAPER/DEMO only after gates. REAL-MONEY LIVE TRADING remains forbidden.

15% geometric/month remains an aspirational target, not an optimization constraint. Do not raise risk or sweep thresholds merely to force it.
