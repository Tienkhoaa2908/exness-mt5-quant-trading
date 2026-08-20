# V33 — Neural Policy Controller plan

Date: 2026-08-20.

V32 establishes that the DeepMLP score is economically useful but a single global binary entry threshold is the wrong final interface. Primary keep60 almost preserves baseline return while materially improving DD, AvgR, PF and turnover. The next architecture therefore separates **confirmation** from **development**.

## Lane A — frozen confirmation

Freeze `adaptive_ewma_hl8_thr0 + DeepMLP keep60` exactly as selected by V32. Do not tune its threshold again on 2026-02 through 2026-07. When a complete unseen month is available, compare only the frozen keep60 rule against its frozen baseline using chronological MT5 evidence.

The exploratory `adaptive_ewma_hl12_thr0p05 + keep80` result remains a challenger hypothesis, not primary confirmation evidence.

## Lane B — V33 development

V33 asks whether the neural signal works better as a **policy controller** than as an all-or-nothing entry rejector.

The development sample may reuse previously inspected history, so V33 cannot create promotion evidence. Its purpose is architecture selection only.

### Model

Start with a shared tabular neural network because direct expected-R GRU/TCN/Transformer experiments did not beat the stronger tabular controls. Do not enlarge network capacity merely for complexity.

Use the same causal entry features plus shared hidden layers and multi-task targets already present in the MT5 ledger:

- realized `r_multiple`;
- `mfe_r`;
- adverse-excursion magnitude from `mae_r`;
- `giveback_r`;
- optional hit indicators derived from MFE such as >=1R and >=2R.

All labels are outcomes and therefore training-only. Current decisions still use only features available by decision time.

### Bounded policy arms

The exact MT5 lab should isolate changes rather than run an open optimizer:

1. baseline: existing fixed policy, maximum 1.00% stop-risk;
2. frozen keep60 binary gate reference;
3. **soft-risk only**: preserve broader opportunities but map frozen neural score bands to bounded risk fractions not exceeding 1.00%;
4. **exit-routing only**: keep entry risk fixed but route score bands between the existing fixed-4R behavior and the previously validated peak-lock family;
5. **combined soft-risk + exit-routing** only if arms 3 and 4 independently show value.

No arm may exceed the 1.00% research stop-risk ceiling. No Martingale, loss doubling, uncontrolled grid or stacked same-symbol risk.

### Why policy control

V32 primary keep60 versus baseline:

- ending capital differs by only ~0.34%;
- max DD is ~31.9% lower;
- AvgR is ~35.4% higher;
- PF is ~17.6% higher;
- turnover is ~26.9% lower.

The missing value is upside breadth in the strong May-July regime. A soft controller can retain more opportunities while using the neural score to alter risk/capture behavior instead of deleting the trade outright.

Primary adaptive-router source diagnostics also show context dependence: EMA and slow momentum are healthy under keep60, while Trend20 remains negative. This supports source/regime-conditioned policy rather than another global score threshold.

## Exact-MT5 requirement

Final economics for every V33 arm must again come from Strategy Tester `monthly_summary.csv` and `trades.csv`, not reconstructed Python PnL. Gating/policy changes alter later adaptive state and trade opportunities, so offline subset arithmetic is insufficient.

Required metrics remain ending USD, geometric monthly return, 15%-month hit count, worst month, full-period max MTM DD, trades, AvgR, ledger PF, rejects, turnover and return/DD.

V33 remains tester-only virtual research. REAL-MONEY LIVE TRADING IS FORBIDDEN.