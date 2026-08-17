# V26 — MT5 training data export + cross-asset ML/DL analysis

Ngày: 2026-08-17

## Runtime export

User bundle SHA-256: `fb7df7b54e64cd7df4d260fca4ea20841a6cf5dd4e3a8daeadd0f98f2cf47259`.

Integrity: 145/145 manifest entries PASS.

Summary:
- total bar rows: 876,136;
- raw XAUUSDm ticks: 17,678,951;
- train ticks Jun–Jul 2026: 14,692,068;
- forward ticks Aug-2026 through 2026-08-17: 2,986,883;
- resolved context: XAGUSDm, EURUSDm, GBPUSDm, USDJPYm, US500m, USTECm, US30m, USOILm, BTCUSDm;
- terminal maxbars = 100,000;
- no order path / no account secrets.

## Coverage defect

Because terminal `maxbars=100000`, deep low-timeframe requests overflowed available chart history:
- XAUUSDm M1/M5/M15: `Invalid params`;
- all context M5: `Invalid params`.

Successfully exported:
- XAUUSDm M30/H1/H4/D1 from 2022-01 through Aug-2026;
- context M15/H1/H4 from 2024-01 through Aug-2026;
- raw broker ticks Jun-2026 through Aug-2026.

A dedicated V1.3 top-up exporter is required after setting MT5 `Max bars in chart` >= 1,000,000. It exports only XAU M1/M5/M15 + context M5, so existing 17.7M ticks are not duplicated.

## Cross-asset M30 feature dataset

A causal M30 dataset was constructed using current XAU M30 bar-close state plus as-of closed XAU H1/H4/D1 and cross-market M15/H1/H4 state. Future labels are created offline only.

Rows: 54,609 total; 54,113 pre-Aug train rows; 496 Aug holdout rows.

Main target used here: future 8 × M30 bars = 4h range normalized by current ATR14.

### LightGBM range model — chronological monthly walk-forward

Fixed feature schema selected before the OOS window. Expanding train, 16h purge, test Aug-2025 → Jul-2026:
- mean Spearman: ~0.542;
- positive Spearman: 12/12 months;
- mean bottom-20% realized normalized range: ~2.11 ATR;
- mean top-20% realized normalized range: ~4.57 ATR.

Partial Aug-2026 evaluation after freezing the pre-Aug model:
- Spearman ~0.626;
- bottom-20% ~1.93 ATR;
- top-20% ~4.28 ATR.

### LightGBM direction model

Same chronological monthly walk-forward:
- mean AUC ~0.534;
- 11/12 months AUC > 0.50;
- partial Aug-2026 AUC ~0.555.

This is better than the sparse V22/V24 trade-event direction models, but still modest; it is not strong enough to let ML directly own order direction.

## DL screening

Fixed sequence length 64 M30 bars with 146 causal bar/cross-asset features. Train pre-May-2026, validation May–Jul-2026, then one partial Aug check.

- TCN: validation range Spearman ~0.560; partial Aug ~0.580; partial Aug direction AUC ~0.573.
- PatchTransformer: validation range Spearman ~0.532; partial Aug ~0.564; partial Aug direction AUC ~0.568.
- GRU exploratory run: validation range peaked ~0.560; partial Aug range ~0.519 and direction AUC ~0.603, but pre-Aug validation direction was only ~0.51. Do not select GRU because one forward slice looks unusually good.

Conclusion: sequence DL preserves the range-regime signal but has not yet shown stable direction discrimination superior to tree models.

## Raw tick microstructure analysis

17.7M raw ticks were aggregated causally into M30 microstructure features: tick count, spread distribution, mid path/range/net, quote-change fractions, imbalance and inter-arrival statistics.

June–Jul train / Aug holdout:
- tick-only range signal exists but is weaker than bar/cross-asset regime features;
- tick-only direction holdout is ~random;
- adding tick features to a compact bar model slightly helps range but does not improve direction.

Therefore raw ticks are kept for execution/fidelity, spread/regime state and later execution modeling, not promoted as direct direction alpha.

## Frozen V26A baseline

Pre-Aug models were frozen for research reproducibility:
- range model SHA-256 `82bd74e6a92c2b20d5e09a42012b86f150cce76454b8c7f5552cd710577a7b7b`;
- direction model SHA-256 `beac2ce7eb41c4a728a368e5a88e4f7fd85743e21e66f1dede77c1f396690fd5`;
- feature schema SHA-256 `9fd98ab3c81b5ba3543c1e4b7ebe4678dccd8f340ab682818e471a10233a9a3c`.

Status: research baseline only, not deployable.

## Validation discipline

Partial Aug-2026 has now been inspected and is no longer pristine for additional same-sample hyperparameter tuning. Any new threshold/model chosen after this analysis must be treated as screening. Fresh forward evidence starts after the freeze time and should not be used to retune first.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. No model artifact is allowed to create native broker orders. Stop-risk research ceiling remains 1.00%/trade.
