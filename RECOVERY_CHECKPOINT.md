# Recovery checkpoint — 2026-08-15

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, or doubling after loss.

## Canonical local history

Latest local Git commit: `fc2f5a56b9e2d4ce3d91014323655ee653eb427c` — `research: add quality exit lab after rolling validation`.

Complete Git bundle SHA-256: `8ebeb8b4dd27081da1dcdb60c2c0aafe6daec2cbd89791613b396ceab47ba68d`.
Source snapshot SHA-256: `0046dea695adfe2fabf7f489241d7baf5d45a07985925c14ec489e9d7b0fe8f6`.
Next research kit SHA-256: `ee35cf2bf5430d7021326b18c70bccbeb8ff4744fd55aa7ec6c8620f1dbf695a`.
Rolling uploaded bundle SHA-256: `498dffbfa1600714584747a73342b93a53d2fcc6c029ab2eafba2c454352c9f4`.

## Accepted strategy state

Tier A remains frozen:
- `trend_breakout_20_regime300`
- `ema_pullback_fast10`

Session preflight remains accepted: all previously observed MARKET_CLOSED failures became broker-session skips and native order_fail=0 in the targeted gate.

## Rolling 1–3M Validation V1 — PASS integrity, mixed return quality

Seven non-overlapping windows were tested from 2025-01-10 through 2026-08-15.

Normalized native MT5 results:
- Trend: positive 7/7; median return +6.72%; range +0.24% to +13.05%; median PF about 1.167; maximum observed MTM DD 7.93%.
- EMA: positive 6/7; median return +5.35%; range -1.25% to +9.69%; median PF about 1.174; maximum observed MTM DD 9.78%.

USD 40 strict 0.50% Standard-Cent-equivalent replay returns by window:
- Trend: +2.99%, +13.94%, +5.77%, +3.33%, +1.59%, -0.39%, +3.33%.
- EMA: +7.61%, +6.93%, +7.44%, +3.17%, +0.54%, approximately 0.00%, +2.16%.

The current strategies therefore do not robustly achieve the user's 15–20% aspiration over each 1–3 month holding period.

## Risk / leverage decision

A USD 40 replay at 0.75% and 1.00% target stop-risk increases signal participation and return in some windows. At 1.00%, each family reached at least +15% in only 3/7 windows; difficult windows remained weak or negative. Closed-equity DD reached about 13.35% for Trend and 18.02% for EMA; MTM DD must remain the primary promotion metric.

Do not use leverage as a substitute for edge. In the rolling native evidence, margin rejects were zero while risk/volume-floor rejects appeared in difficult high-volatility windows. Higher leverage can lower required margin but does not reduce minimum-lot loss-at-stop.

Risk policy for research:
- 0.50% = baseline;
- 0.75% = moderate research overlay;
- 1.00% = aggressive research ceiling only;
- no risk target above 1.00% in the current project phase.

## Next gate — QualityExitLabV1

Run `scripts/run_quality_exit_lab_v1.cmd` from the V14 one-click kit.

The lab is tester-only and virtual: no CTrade and no broker orders. It runs seven 1–3 month windows. Each run evaluates 16 pre-registered variants x four independent books:
- normalized continuous 0.50% risk;
- USD 40 cent-equivalent 0.50%;
- USD 40 cent-equivalent 0.75%;
- USD 40 cent-equivalent 1.00%.

Variants test:
- baseline 2 ATR / 2R;
- tighter 1.5 ATR stop;
- 2.5R / 3R targets;
- break-even runner;
- ADX(14) >= 20;
- H1 EMA trend alignment;
- price-quality confirmation;
- combined quality + tighter-exit variants.

USD 40 books use 0.0001 standard-lot-equivalent minimum/step and a conservative theoretical 1:200 margin stress. Finalists must return to native MT5 parity before promotion.

## Recovery rule

GitHub is a required checkpoint after every material milestone. Local source snapshot + complete Git bundle remain the complete-history recovery layer until the full source tree/history is mirrored on remote. Never claim remote sync is complete without verifying it.