# V41 Baseline Upgrade Stack + Direct Action-Value — preregistered Stage A plan

Date: 2026-08-21  
Branch: `agent/v41-baseline-stack-action-value`

## Economic control

Accepted exact-MT5 baseline: `adaptive_ewma_hl8_thr0`, continuous USD40 @ <=1.00% stop-risk:

- start $40;
- end $107.43;
- 8.58% geometric/month;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

15% geometric/month remains aspirational: $40 would become about $214.01 after 12 months. No V41 threshold/risk may be tuned merely to force this target.

## What the baseline actually is

The baseline is not an ML/DL directional model. It is a causal online mixture-of-experts router:

- EMA H1 skip20;
- MACD H1 gap10;
- BOS/FVG H1 gap8;
- Trend20 H1 gap5;
- slow multi-horizon 16h+24h momentum.

Only normalized realized-R from control shadow books updates expert EWMA scores. Half-life = 8; threshold = 0. The chosen expert owns direction.

### Main gaps

- realized-R feedback is delayed;
- market/opportunity quality is not valued directly;
- sequence/churn information is only implicit;
- V36 in-trade state is not part of the baseline controller;
- exit protection is not chosen by expected incremental value versus baseline.

## Layer A — entry expected-R

Model: `HistGradientBoostingRegressor`.

Causal features available before entry:

- selected source family and direction;
- clock encodings;
- last two completed-trade R outcomes;
- same-direction history;
- time since prior completed trade;
- rapid post-profit context;
- third same-direction trade after two wins context.

Fixed keep target: **60%**, inherited as a bounded architecture choice from V32 keep60. Threshold is the 40th percentile of the previous calibration-month scores, then applied unchanged to the next month. No test-month quantile.

This is a new baseline-local model, not a retune of the frozen V32 DeepMLP.

## Layer B — V36 chronology calibration

Accepted V36 Transformer predictions are not retrained. Isotonic calibrators for `p_hold` and `p_protect` are fit only on V36 rows whose corresponding control trades fully exited before the fold calibration boundary. Calibrated state plus `pred_final_r` become features in the action-value model.

## Layer C — direct action value

Decision zone: current unrealized R >= +1R.

Actions:

- `STATIC_PROTECT_0.25R`;
- `SELECTIVE_TRAIL_0.25R`;
- baseline/no-action is the control.

For every causal state and action, calculate the realized counterfactual target:

`delta_R = action_exit_R - baseline_exit_R`.

Two models per action:

- HGB regressor: `E[delta_R]`;
- HGB classifier: `P(delta_R > 0)`.

Action score = predicted delta × positive probability.

Fixed action coverage target: **20%** from the preceding calibration month. A test state must also have predicted delta >0. First selected state per trade is retained; if two actions qualify at the same first time, larger predicted delta wins.

Training weights are inverse number of states per trade so long trades do not dominate labels.

## Layer D — diagnostic baseline holes

Pre-existing hypotheses are measured but not auto-integrated:

- targeted EMA/BOS SHORT exhaustion after two same-direction winners within <=4h;
- EMA server 22-23 weakness;
- generic rapid same-direction re-entry after a profitable trade.

Same-sample success only creates a hypothesis. It cannot become a hidden production veto.

## Frozen positive evidence carried forward

- V32 DeepMLP keep60: near-baseline exact return with DD ~10.82% -> 7.36%, trades 222 ->153, AvgR .240 -> .325, PF 1.558 ->1.833. Frozen; no keep-rate retune.
- V36 Transformer: Hold AUC .6757, Protect AUC .6771, final-R Spearman .5148. Frozen sequence feature.
- V30: expected-R is more useful than win/loss; family-specific context matters. Architecture lead, not fresh confirmation.

Rejected components are explicitly excluded: generic cooldown, hard quality conjunction, broad signal fusion, fixed range-to-family routing, universal fast exits, V39 eventual-giveback target and V40 first-passage-only target.

## Stage-A economics

All shadow lanes use the same risk scale calibrated so the untouched baseline R tape reproduces $107.43. Report separately:

- exact baseline;
- entry-value shadow;
- action-value shadow;
- integrated stack shadow;
- 15% target.

Shadow results are not exact-MT5 because modified decisions alter the state path.

## Promotion logic

Each lane is independent.

**Entry return PASS**: shadow geo/month > baseline, total delta R >0, and positive delta in >=75% of OOS months (minimum 4).

**Entry efficiency KEEP**: shadow geo no more than 0.25 percentage points/month below baseline and shadow DD at least 15% lower. This is an efficiency finding, not a return promotion by itself.

**Action PASS**: shadow geo > baseline, total delta R >0, positive action delta in >=75% OOS months (minimum 4), >=30 selected actions, overall selected-action coverage 3%-30%.

**Integrated stack PASS**: shadow geo > baseline, total delta R >0, positive stack delta in >=75% OOS months (minimum 4), and shadow DD no more than 1 percentage point worse than the calibrated baseline shadow.

Final `STAGE_A_PASS` if entry-return, action-value or integrated stack clears its gate. Promotion lane is frozen before any exact-MT5 Stage B.

## Safety / integrity

- offline/read-only Stage A;
- no MT5/MetaEditor launch;
- zero broker orders;
- zero extra entries;
- initial risk unchanged;
- research stop-risk ceiling <=1.00%;
- one run -> one ZIP with CRC + SHA manifest.
