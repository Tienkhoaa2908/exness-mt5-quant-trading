# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Source of truth

Do not reconstruct state from memory when GitHub/evidence disagree.

Current canonical branch:

`agent/v40-upgrade-campaign`

Accepted V39 base:

`a28146448c4cf8020e6fa1147e39d97506fa08e6`

Accepted V40 implementation head that generated evidence:

`f201a432e7839c6190382a0362fd44cb4be26976`

Windows recovery must use explicit refspec and must not use `git clean`; accepted V36/V38 outputs and Python environments may be untracked.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk <=1.00%/trade.
- No Martingale, uncontrolled grid or doubling after loss.
- Do not remove tester/live guards.
- Offline research launches no MT5/MetaEditor unless an explicit exact-MT5 gate is promoted.
- Do not increase risk or tune thresholds merely to force 15% geometric/month.

## Canonical evidence

- V30 source: `4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`.
- V31.1 ZIP: `7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`.
- V32 ZIP: `3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`.
- V34/V35 ZIP: `ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`.
- Accepted V34 source: `8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`.
- V36/V37 ZIP: `7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`.
- V38 exact ZIP: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
- V39 HOLD ZIP: `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`.
- V40 HOLD ZIP: `e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`.

Exact baseline truth remains $40 -> $107.43 over 12 months, 8.58% geometric/month, max DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501. 15%/month would imply about $214.01 from $40 after 12 months and is not achieved.

## Frozen evidence

V32 DeepMLP keep60 remains frozen risk-efficiency evidence: near-same Feb-Jul return with DD 10.82% ->7.36%, trades 222 ->153, AvgR 0.240 ->0.325, PF 1.558 ->1.833. Do not retune that accepted window.

V36 Transformer remains reproducible sequence/ranking evidence: final-R Spearman 0.5148, Hold AUC 0.6757, Protect AUC 0.6771, both >0.5 in 6/6 months. Accepted prediction SHA: `a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`.

V40 calibration diagnostics show literal V36 probabilities are not well calibrated: approximate 10-bin ECE ~0.176 Hold, ~0.230 Protect. Use V36 as rank/state evidence unless probability calibration is added chronologically.

## V39 accepted decision

V39 fusion is HOLD: 17 triggers, 3/6 positive months, 32% false-big-winner. Do not rescue via same-sample quantile, p_hold, source/direction or risk sweeps.

## V40 accepted result

Bundle integrity PASS: outer SHA `e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`, CRC PASS, 13/13 manifest entries PASS.

Inputs: 129,311 filtered M1 rows, 563 trades, M1 coverage 563/563, 29,514 +1R states across 283 trades.

First-passage model/action gate:

- 7 folds PASS;
- 65 triggers PASS;
- 42.21% coverage FAIL (target 5%-35%);
- mean AUC 0.5264 FAIL (>=0.60);
- GIVEBACK_FIRST 63.08% PASS;
- TAIL_FIRST 15.38% PASS;
- positive static-shadow months 1 FAIL (>=4);
- total static delta -14.01R FAIL;
- final `STAGE_A_HOLD`.

Shadow economics are not exact-MT5 PnL:

- Immediate: $95.15 / 7.49% per month / -14.85R;
- Static protect 0.25R: $95.76 / 7.55% / -14.01R;
- Selective trail 0.25R: $94.48 / 7.43% / -15.69R;
- calibrated shadow baseline: $107.43 / 8.5814%.

Root cause: V40 correctly improves event-order semantics but `GIVEBACK_FIRST` is still not equivalent to profitable protection. Among 41 GIVEBACK_FIRST triggers, static protection loses about -0.342R/trade because many trades cross the giveback boundary and later recover before baseline exit.

Full result: `docs/research/v40_upgrade_campaign_stage_a_result.md`.

## Next research contract — direct action value

Do not promote V40 to exact-MT5.

The next research milestone should directly estimate counterfactual action reward from each causal +1R state:

`reward(action) = shadow_action_R - baseline_R`.

Requirements:

- fixed candidate actions preregistered before evaluation;
- first-passage state/features may be retained as inputs, not the sole target;
- chronological train -> trailing calibration -> test month;
- model expected action value and/or probability action value >0;
- selection threshold calibrated on pre-test data only;
- OOS monthly economic gate is primary;
- zero extra entries and unchanged initial risk;
- no barrier/source/risk sweep on V40 development months;
- source/direction diagnostics cannot become production filters on the same sample;
- only a preregistered positive economic Stage-A gate may advance to frozen exact-MT5 Stage B.

V36 probability calibration can be a separate support lane; do not retrain accepted OOS predictions to improve headline numbers.

## Runner hardening that must not regress

- explicit branch refspec;
- no `git clean`;
- pytest optional/static fallback;
- tracked-source secret scan;
- V36 full dependency probe including sklearn/scipy;
- V40 `signal_sources` schema adapter: preserve existing source, M15 fallback only, no `_x/_y` collision;
- one run -> one ZIP;
- internal manifest and CRC verification.

## Decision stack

- Baseline KEEP/control.
- DeepMLP keep60 KEEP frozen benchmark.
- V36 KEEP sequence/rank evidence; calibrate probability before literal threshold use.
- V35 generic router REJECT.
- V37 generic SMC gate REJECT/redesign.
- V38 universal fast exits REJECT.
- V39 selective harvest HOLD/redesign.
- V40 first-passage protection HOLD/redesign to direct action value.
- 15% geometric/month aspirational and unmet.
