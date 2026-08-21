# V40 Upgrade Campaign — Stage A result

Ngày chốt evidence: 2026-08-21.

## Bundle integrity

Accepted uploaded ZIP SHA-256:

`e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`

CRC PASS. `bundle_manifest_sha256.txt` có 13 entries và toàn bộ hash nội bộ PASS.

Evidence head:

`f201a432e7839c6190382a0362fd44cb4be26976`

Branch:

`agent/v40-upgrade-campaign`

Accepted input evidence:

- V38 ZIP SHA: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`;
- V39 ZIP SHA: `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`;
- V36 predictions SHA: `a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`;
- V38 M1 coverage: 563/563 trades;
- filtered M1 rows: 129,311;
- +1R-zone rows: 29,514 across 283 trades.

## Profit report

Exact accepted baseline remains the only verified PnL:

- start $40;
- end $107.43;
- 8.58% geometric/month;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

Aspirational 15%/month target implies about $214.01 after 12 months from $40. The exact baseline is still 6.42 percentage points/month below that target.

V40 calibrated shadow economics are diagnostic only, not exact-MT5 PnL:

| Action | Shadow end | Geo/month | Shadow DD | Delta vs shadow baseline | Total delta R |
|---|---:|---:|---:|---:|---:|
| Immediate | $95.15 | 7.49% | 9.13% | -$12.28 | -14.85R |
| Static protect 0.25R | $95.76 | 7.55% | 9.13% | -$11.67 | -14.01R |
| Selective trail 0.25R | $94.48 | 7.43% | 9.13% | -$12.95 | -15.69R |

The shadow baseline is calibrated to $107.43 / 8.5814% per month. Therefore all three V40 actions are economically worse than baseline in this diagnostic.

## Preregistered gate

Final status: **STAGE_A_HOLD**.

| Gate | Observed | Requirement | Result |
|---|---:|---:|---|
| folds | 7 | >=5 | PASS |
| triggers | 65 | >=30 | PASS |
| coverage | 42.21% | 5%-35% | FAIL |
| mean AUC GIVEBACK_FIRST vs TAIL_FIRST | 0.5264 | >=0.60 | FAIL |
| GIVEBACK_FIRST trigger rate | 63.08% | >=60% | PASS |
| TAIL_FIRST trigger rate | 15.38% | <=25% | PASS |
| positive static-shadow months | 1 | >=4 | FAIL |
| total static delta R | -14.01R | >0 | FAIL |

No threshold/barrier/source/risk rescue sweep is allowed on this sample.

## Monthly diagnostics

Static protect delta R by month:

- Jan: -4.263R / 16 triggers;
- Feb: +1.591R / 5 triggers;
- Mar: -1.796R / 2 triggers;
- Apr: 0.000R / 1 trigger;
- May: -4.118R / 13 triggers;
- Jun: -3.066R / 17 triggers;
- Jul: -2.358R / 11 triggers.

Only February is positive. Coverage is particularly high in May (68.4%), June (53.1%) and January (47.1%). Fold AUC is unstable: Jan 0.429, Feb 0.708, Mar 0.514, Apr 0.494, May 0.349, Jun 0.598, Jul 0.592.

## Root-cause interpretation

V40 fixed one V39 mismatch by predicting event order instead of eventual giveback. Trigger composition confirms partial success: 41/65 triggers are `GIVEBACK_FIRST`, 10/65 `TAIL_FIRST`, 14/65 censored.

However event order is still not the same as economic action value.

For the 41 `GIVEBACK_FIRST` triggers:

- mean trigger R: about 2.240R;
- mean baseline final R: about 2.235R;
- mean static floor: about 1.990R;
- mean realized static-protect shadow R: about 1.893R;
- mean static-protect delta vs baseline: **-0.342R/trade**.

Therefore many trades cross the 0.25R giveback boundary but subsequently recover before the baseline exit. A first-passage classifier can be directionally correct and still recommend an economically bad stop action.

The next model target should therefore estimate **counterfactual action value directly**, not merely event order. For each causal state, derive the shadow outcome of each fixed protective action and predict expected `action_R - baseline_R`, with chronological train/calibration/test and no same-sample threshold rescue.

## Source/direction diagnostics

Baseline source-family AvgR remains strongest in SLOW_MOM (0.280R) and EMA (0.245R). LONG baseline AvgR is 0.227R vs SHORT 0.193R. Some small source-direction cells are weak (e.g. MACD SHORT and TREND SHORT), but these are diagnostic only and must not become filters on this same sample.

Static-protect losses are broad rather than isolated: SLOW_MOM -7.53R, EMA -4.06R, MACD -1.43R, TREND -0.98R across triggered trades. LONG and SHORT both lose under static protection. This argues against source/direction gating as the primary repair.

## V36 calibration warning

V36 remains useful as rank/sequence evidence but its probabilities are not well calibrated as literal probabilities. Approximate 10-bin ECE from the V40 bundle is about 0.176 for Hold and 0.230 for Protect. Protect probabilities are materially overconfident at high bins. Future fusion should calibrate probability heads before using fixed probability thresholds.

## Decision

- V40 Stage A: HOLD; do not promote to exact-MT5 Stage B.
- Exact baseline: KEEP.
- V32 DeepMLP keep60: KEEP frozen risk-efficiency benchmark.
- V36 Transformer: KEEP sequence/ranking evidence; probability calibration needs improvement before threshold use.
- V39/V40 exit controllers: HOLD / structural redesign.
- Next research: direct action-value / counterfactual reward modeling, with first-passage features retained as inputs rather than the sole target.
- No risk increase and no attempt to force 15%/month.

REAL-MONEY LIVE TRADING remains FORBIDDEN.
