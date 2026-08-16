# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, doubling after loss, or risk escalation as a substitute for expectancy.

## Canonical local history

Latest local Git commit: `83965beff208221f896e4554e22472f0722e8e29` — `research: rescreen quality exits on monthly horizon`.

Complete Git bundle SHA-256: `5543b83297d918969436e8333b2a84443578b5534e1f8c4f36d5374c22788d75`.
Source snapshot SHA-256: `ca964ae35c41227a032a6b01e2bd9472265fbe4cb0d618d89ab12796c6052276`.
Next research kit SHA-256: `e9ecd3039d133644d16687cff344992b7d0a815ff8adba70f743b716901647bb`.
Monthly H1 uploaded bundle SHA-256: `562d4c0c37810ebe37edeb0b325b31c52c83f1a921d27ccb75083ce8f2a8e45d`.

## Monthly H1 Native V1 — COMPLETE

Integrity: all 261 bundle hashes PASS. Windows MetaEditor compile: both finalists `0 errors, 0 warnings`. Batch: 18 independent full calendar months (2025-02 through 2026-07) x two native H1 finalists = 36 MT5 Strategy Tester runs. Native order failures were zero.

Normalized native monthly profile:
- Trend H1: positive 12/18; median +2.20%; best +11.16%; worst -4.19%; max native MTM DD 7.11%.
- EMA H1: positive 15/18; median +1.51%; best +7.95%; worst -3.53%; max native MTM DD 5.38%.

USD 40 strict-target @1.00% stop-risk:
- Trend H1: median +2.43% (~+$0.97); >=15% 3/18; >=20% 1/18; worst -8.46%; best +20.63%; max closed-balance DD 13.29%.
- EMA H1: median +3.69% (~+$1.48); >=15% 1/18; >=20% 0/18; worst -7.08%; best +15.77%; max closed-balance DD 10.46%.

The H1 finalists do NOT robustly satisfy the 15–20% monthly aspiration.

## Risk escalation finding

Diagnostic replay at 1.25%, 1.50%, and 2.00% stop-risk is not an approved deployment policy. Even at 2.00%, median monthly return remained only about +9.07% Trend / +8.11% EMA while worst months reached roughly -16.28% / -15.15% and closed-balance DD roughly 25.03% / 21.11%.

Decision: do not raise the approved research ceiling above 1.00% merely to chase the monthly return target. Higher leverage lowers margin but does not create expectancy.

## Next gate — Monthly Quality / Exit Re-screen V1

Because the practical objective changed from 1–3 months to one calendar month, re-rank the already pre-registered 16 QualityExitLabV1 variants using 18 independent monthly resets before inventing new parameters.

Use exact Windows-proven `QualityExitLabV1.mq5` source SHA-256 `bd396c38663499acf304279ea91da2a5af89c934b3e4b7804deec42242f170d9`.

Each month evaluates 16 variants x four virtual books:
- normalized USD 10k @0.50%;
- USD 40 @0.50%;
- USD 40 @0.75%;
- USD 40 @1.00%.

Runner: `scripts/run_monthly_quality_exit_rescreen_v1.cmd`. It uses a persistent LocalAppData checkpoint so completed months are reused after interruption. Virtual winners must return to native MT5 before promotion.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The V17 source snapshot + complete Git bundle remain the complete-history recovery layer until full local history mirroring on remote is explicitly verified. Never claim full remote history sync without verification.