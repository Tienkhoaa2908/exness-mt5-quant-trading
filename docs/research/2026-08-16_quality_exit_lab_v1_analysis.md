# Quality / Exit Lab V1 — analysis

Uploaded bundle SHA-256: `81832a5917c96f323837e20d9f498c84e401d8e5ab72c6ea690f4910a1757b7d`.

Integrity: PASS (34 internal hashes). Windows MetaEditor compile: 0 errors, 0 warnings.

## Main finding

The strongest robust improvement came from H1 trend alignment, not from simply widening TP or tightening SL.

At USD 40 / 1.00% research ceiling:

| Candidate | Median return | Positive | >=15% | Worst | Best | Max MTM DD | Median PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ema_h1_2atr_2r` | 17.27% | 6/7 | 4/7 | -3.33% | 31.79% | 12.33% | 1.345 |
| `trend_h1_2atr_2r` | 14.84% | 7/7 | 3/7 | +2.27% | 23.87% | 15.64% | 1.359 |
| `trend_tight_1p5atr_2r` | 15.64% | 6/7 | 4/7 | -6.38% | 41.77% | 20.28% | 1.160 |
| `trend_quality_2atr_2r` | 10.58% | 7/7 | 2/7 | +4.80% | 34.96% | 13.87% | 1.321 |

`ema_h1_2atr_2r` is the return finalist. `trend_h1_2atr_2r` is the stability finalist. The tight-stop Trend variant is not promoted because of the negative window and >20% MTM drawdown.

The H1 Trend and H1 EMA USD 40 / 1.00% virtual books have exact entry-time+direction Jaccard about 0.009 and daily realized-PnL correlation about 0.52. This is enough to justify a future shared-risk portfolio test, but not enough to claim diversification.

Important limitation: the virtual lab baseline does not reproduce every native rolling cash result exactly. Therefore finalists must return to native MT5 CTrade validation before any risk/capital promotion.

## Decision

Promote only:
1. `trend_h1_2atr_2r`
2. `ema_h1_2atr_2r`

Keep 2 ATR stop / 2R target frozen for the native gate. Risk research remains 0.50% baseline, 0.75% moderate overlay, and 1.00% aggressive ceiling. No >1.00% stop-risk research in the current phase. REAL-MONEY LIVE TRADING remains forbidden.