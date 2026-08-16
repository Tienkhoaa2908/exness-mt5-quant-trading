# Monthly H1 Native V1 — analysis

Uploaded bundle SHA-256: `562d4c0c37810ebe37edeb0b325b31c52c83f1a921d27ccb75083ce8f2a8e45d`.

Integrity: PASS. All 261 paths in `bundle_manifest_sha256.txt` were recomputed and matched. Windows MetaEditor compile logs: both H1 finalists report `Result: 0 errors, 0 warnings`.

## Native normalized MT5 results

- Trend H1: positive 12/18; median monthly +2.20%; mean +2.57%; worst -4.19%; best +11.16%; median PF ~1.306; median win rate 40.00%; max native MTM DD 7.11%.
- EMA H1: positive 15/18; median monthly +1.51%; mean +2.25%; worst -3.53%; best +7.95%; median PF ~1.239; median win rate 39.21%; max native MTM DD 5.38%.

## USD 40 strict-target translation

Volume is floored to 0.0001 standard-lot-equivalent steps and never rounded upward. If the minimum step would exceed target stop-risk, the signal is skipped. Margin is stress-tested at 1:200. This remains an XAUUSDm-ledger translation, not a native XAUUSDc backtest.

At 1.00% stop-risk:
- Trend H1: positive 12/18; >=15% 3/18; >=20% 1/18; median +2.43% (~+$0.97); mean +4.14%; worst -8.46%; best +20.63%; max closed DD 13.29%.
- EMA H1: positive 13/18; >=15% 1/18; >=20% 0/18; median +3.69% (~+$1.48); mean +4.10%; worst -7.08%; best +15.77%; max closed DD 10.46%.

The H1 finalists therefore do not robustly meet a 15–20% monthly objective.

## Risk escalation diagnostic

Exploratory replay at 1.25%, 1.50%, and 2.00% was used only to test whether the return shortfall could be solved by increasing risk. It is not an approved deployment policy.

At 2.00% stop-risk:
- Trend H1 median monthly return ~+9.07%; >=15% 6/18; worst ~-16.28%; best ~+52.02%; max closed DD ~25.03%.
- EMA H1 median monthly return ~+8.11%; >=15% 6/18; worst ~-15.15%; best ~+35.20%; max closed DD ~21.11%.

Conclusion: risk/leverage escalation alone does not create the required monthly expectancy and materially worsens downside.

## Decision

Keep the approved research ceiling at 1.00% stop-risk. Re-screen the existing 16 pre-registered QualityExitLabV1 variants on 18 independent monthly resets because the decision horizon changed. Reuse the exact Windows-proven QualityExitLabV1 source; only schedule and checkpointed runner logic change. Any virtual monthly finalist must return to native MT5 before promotion.
