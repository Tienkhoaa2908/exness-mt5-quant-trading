# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Research stop-risk ceiling <=1.00%/trade.
- PAPER/DEMO chỉ sau explicit safety/economic gates; LIVE vẫn cấm.
- Current offline research không launch MT5/MetaEditor và không có broker-order path.

## Repository recovery

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

Current canonical branch:

`agent/v40-upgrade-campaign`

Accepted V39 base:

`a28146448c4cf8020e6fa1147e39d97506fa08e6`

Accepted V40 implementation head that generated evidence:

`f201a432e7839c6190382a0362fd44cb4be26976`

Windows recovery must use explicit refspec and must not use `git clean` because accepted runtime evidence and `.venv` may be untracked.

Runner lessons that must not regress:

- pytest optional with dependency-free static fallback;
- secret scan only tracked working-tree source/config via `git ls-files -z`;
- V36 dependency probe includes numpy/pandas/torch/sklearn/scipy and explicit `scikit-learn==1.8.0`;
- V40 schema adapter preserves existing `signal_sources`, uses M15 only as fallback, and never creates `_x/_y` suffix collisions.

## Accepted evidence stack

- V30 source SHA: `4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`.
- V31.1 ZIP: `7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`.
- V32 ZIP: `3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`.
- V34/V35 ZIP: `ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`.
- Accepted V34 source: `8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`.
- V36/V37 ZIP: `7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`.
- V38 exact-MT5 ZIP: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
- V39 accepted HOLD ZIP: `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`.
- V40 accepted HOLD ZIP: `e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`.

## Exact baseline / profit truth

12-month exact-MT5 control `adaptive_ewma_hl8_thr0`, continuous USD40:

- start $40;
- end $107.43;
- total return +168.6%;
- geometric/month 8.58%;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

15% geometric/month remains aspirational and unmet. From $40 it would imply about $214.01 after 12 months. Exact baseline remains 6.42 percentage points/month below target.

Universal fast exits remain rejected. +1R is only a decision zone.

## Frozen model/risk evidence

V32 DeepMLP keep60 remains frozen risk-efficiency evidence: near-same Feb-Jul return while DD fell from 10.82% to 7.36%, trades 222 ->153, AvgR 0.240 ->0.325, PF 1.558 ->1.833. Do not retune the accepted window.

V36 Transformer remains reproducible sequence/ranking evidence: final-R Spearman 0.5148, Hold AUC 0.6757, Protect AUC 0.6771, both AUCs >0.5 in 6/6 months. Accepted predictions SHA: `a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`.

V40 calibration analysis shows V36 literal probabilities are not well calibrated: approximate 10-bin ECE ~0.176 Hold and ~0.230 Protect. Preserve V36 rank signal, but calibrate heads before using probability thresholds.

## V39 accepted decision

V39 fusion: `STAGE_A_HOLD` — 6 folds, 17 triggers, 14.655% coverage, 3/6 positive avoided-giveback months, mean monthly avoided giveback +0.120864R, false-big-winner 32.0%. Do not rescue via same-sample threshold/source/risk sweeps.

## V40 accepted Stage-A result — HOLD

Accepted uploaded ZIP SHA:

`e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`

Integrity: CRC PASS and 13/13 internal manifest entries PASS. Inputs: 129,311 filtered M1 rows, 563 control trades, M1 coverage 563/563, 29,514 +1R-zone rows across 283 trades.

Preregistered gate:

- folds 7 — PASS;
- triggers 65 — PASS;
- coverage 42.21% — FAIL gate 5%-35%;
- mean first-passage AUC 0.5264 — FAIL >=0.60;
- GIVEBACK_FIRST trigger rate 63.08% — PASS >=60%;
- TAIL_FIRST trigger rate 15.38% — PASS <=25%;
- positive static-shadow months 1 — FAIL >=4;
- static total delta -14.01R — FAIL >0;
- final status: **STAGE_A_HOLD**.

Shadow economics, diagnostic only and NOT exact-MT5 PnL:

- Immediate: $95.15, 7.49%/month, -14.85R vs baseline shadow;
- Static protect 0.25R: $95.76, 7.55%/month, -14.01R;
- Selective trail 0.25R: $94.48, 7.43%/month, -15.69R;
- shadow baseline is calibrated to $107.43 / 8.5814% per month.

Only February has positive static-protect monthly delta. May/June/January coverage is too high and fold AUC is unstable.

## V40 root cause

V40 improved target alignment versus V39 by modeling first-passage event order. It correctly concentrates triggers toward GIVEBACK_FIRST: 41/65 GIVEBACK_FIRST, 10/65 TAIL_FIRST, 14/65 censored.

But event order is still not economic action value. Among 41 GIVEBACK_FIRST triggers, static protection loses about -0.342R/trade versus baseline. Many trades cross the 0.25R giveback boundary and later recover before baseline exit. Therefore a classifier can correctly predict a temporary giveback and still recommend an economically harmful stop.

Source/direction filtering is not the main repair: static-protect losses are broad across SLOW_MOM, EMA, MACD, TREND and both LONG/SHORT. Same-sample source gates are forbidden.

Full result:

`docs/research/v40_upgrade_campaign_stage_a_result.md`

## Next research contract

Do NOT promote V40 to exact-MT5 Stage B.

Next milestone should redesign the target to direct counterfactual action value:

- retain causal +1R state and first-passage features as inputs;
- for each fixed protective action, derive offline shadow reward `action_R - baseline_R` from the observed control path;
- train chronological models to estimate expected action value / probability of positive action value;
- calibrate scores on trailing pre-test data only;
- evaluate fixed action-selection policy OOS by month;
- preserve zero extra entries and initial risk;
- do not sweep barrier/source/risk on V40 development months to force PASS;
- only a preregistered positive OOS economic gate may advance to exact-MT5.

## Decision stack

- Baseline: KEEP/control.
- DeepMLP keep60: KEEP frozen risk-efficiency benchmark.
- V36 Transformer: KEEP rank/sequence evidence; calibrate probabilities before threshold use.
- V35 generic router: REJECT.
- V37 generic SMC gate: REJECT/redesign.
- V38 universal fast exits: REJECT.
- V39 selective harvest: HOLD/redesign.
- V40 first-passage protect/trail: HOLD/redesign to direct action value.
- 15% geometric/month: aspirational, unmet, never an override for risk or research gates.

## One run -> one ZIP

Every important run must output one ZIP with `bundle_manifest_sha256.txt`; verify outer SHA, CRC, all manifest hashes, evidence head/branch and summary before acceptance. Do not request screenshots if bundle evidence is sufficient.
