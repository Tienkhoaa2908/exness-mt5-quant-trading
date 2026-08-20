# V36 / V37 results

Date: 2026-08-20

## Evidence package

Uploaded ZIP SHA-256:

`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Contents:

- `v36_sequence_summary.json`
- `v36_sequence_predictions.csv`
- `v37_smc_quality_summary.json`
- `v37_smc_quality_predictions.csv`

The run used the canonical V30 stitch contract and required exactly 35,344 unique M15 rows after half-open chunk trimming.

## V36 true intra-trade sequence DL

Models:

- GRU48
- true causal TCN48
- Transformer48x2 with positional encoding and causal attention mask

Sequence length: 32 M15 states. Numeric state = current path state plus causal market/regime/tick features. Candidate identity and an explicit valid-step mask are included. Scaling is train-only and excludes padded timesteps.

Chronological OOS months: 2026-02 through 2026-07.

Mean metrics:

| Model | Future-delta Spearman | Final-R Spearman | Hold AUC | Protect AUC |
|---|---:|---:|---:|---:|
| GRU48 | +0.0187 | +0.5246 | 0.6426 | 0.6150 |
| causal TCN48 | -0.0116 | +0.4767 | 0.6152 | 0.5524 |
| **Transformer48x2** | **+0.0403** | **+0.5148** | **0.6757** | **0.6771** |

Interpretation:

- Direct regression of `future_incremental_realized_R_from_current_mark` remains weak. Do not use the regression head as a continuous expected-R controller.
- Final-R rank correlation is not evidence of a strong model edge by itself because current unrealized R already contains substantial information about final R.
- The binary sequence heads are materially stronger and much more stable than V33 entry-snapshot heads. Transformer hold AUC is >0.5 in all 6 months and protect AUC is >0.5 in all 6 months.
- Transformer is the only model in this tournament with both heads consistently useful enough to justify an exact-MT5 policy experiment.

Development-only policy diagnostic from the OOS prediction file:

For the first telemetry state per trade satisfying `current_unrealized_R >= +1.0R` and `Transformer p_hold < 0.10`, 603 trades trigger. At the first trigger, exiting at the observed mark instead of waiting for the original final exit would have avoided an average 0.205R of subsequent giveback; 79.3% of triggered trades finish below that trigger mark. Mean avoided giveback is positive in all six inspected months. This is a post-hoc development clue, not PnL evidence, because intervention changes subsequent paths and execution must be replayed in MT5.

Decision: **PROMISING FOR BOUNDED EXACT-MT5 EXIT-POLICY TEST**. Do not promote the Transformer or reconstruct PnL offline.

## V37 dedicated SMC quality filter

Candidate: `v34_smc_ict_causal` exact-MT5 norm-book trades.

Models:

- HistGradientBoostingRegressor
- ExtraTreesRegressor
- MLPRegressor 48-24

Frozen diagnostic rule: score >= prior-month 40th percentile, approximately keep60.

Aggregate OOS 2026-02 through 2026-07:

| Model | Mean coverage | Baseline AvgR | Selected AvgR | Mean uplift | Months uplift >0 | Selected sumR |
|---|---:|---:|---:|---:|---:|---:|
| HistGB | 61.6% | 0.0181R | -0.0497R | -0.0679R | 1/6 | -15.75R |
| ExtraTrees | 67.0% | 0.0181R | -0.0587R | -0.0768R | 0/6 | -19.98R |
| MLP 48-24 | 51.5% | 0.0181R | +0.0254R | +0.0073R | 4/6 | +3.44R |

The MLP has a small mean AvgR uplift, but it discards most of the baseline SMC sumR and is unstable by month. HistGB and ExtraTrees are directionally wrong on average.

Decision: **REJECT current generic SMC keep60 quality gate**. Do not send V37 to MT5. If SMC research continues, redesign around regime/direction-specific labels or independent structure features rather than tuning the same generic score threshold.

## Next gate

V38 should test a conservative Transformer-derived exit/protection policy inside Strategy Tester, with no risk increase and no native/external broker orders. The principal development hypothesis is to act only after the position has reached at least +1R and the sequence model assigns very low probability to additional >=0.5R upside. Exact MT5, not subset arithmetic, decides whether this reduces giveback without destroying the large winners that drive baseline expectancy.
