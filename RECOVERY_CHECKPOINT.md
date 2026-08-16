# Recovery checkpoint — V22 Signal Intelligence Lab V1

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING vẫn bị cấm. Chỉ offline research / MT5 Strategy Tester; PAPER/DEMO chỉ sau safety gates. Không Martingale, uncontrolled grid, doubling after loss, không tháo LIVE/tester guard, không tăng stop-risk vượt ceiling 1.00%/trade và không commit password/token/secret.

## Bằng chứng hoàn tất — Signal Intelligence Lab V1 (V22)

Output ZIP SHA-256:
`abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`

- internal SHA-256: PASS 22/22;
- Windows MetaEditor: 0 errors, 0 warnings;
- 3 chunk hoàn tất, 18 tháng độc lập 2025-02 → 2026-07;
- 30 candidates × 4 books;
- `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`.

`ema_h1_base` USD40@1% vẫn là control mạnh nhất: median +6.3236%, 13/18 tháng dương, worst -4.5875%, max MTM DD 9.0171%. Chưa có evidence robust cho aim 15–20%/tháng.

V22 decision:
- không promote score3/score4;
- không promote global exhaustion guard;
- không promote telemetry meta-labeling LR/GBDT vì test AUC gần 0.5;
- regime shift và family-specific session/trend-separation là gate kế tiếp.

## Gate kế tiếp — V23 Regime Router Lab V1

- 26 candidates × 4 books = 104 virtual books;
- EMA late-session + targeted SHORT exhaustion ablations;
- MACD/Trend/BOS family-specific H1 trend-separation grid;
- selective one-position-at-time routers;
- 18 monthly resets trong 3 chunk;
- một runner → một ZIP.

Conditional trade-ledger thresholds chỉ là hypothesis discovery và phải được re-simulate trong Strategy Tester.

## Recovery rule

Đọc `README.md`, `docs/handover/CURRENT_STATE.md`, `docs/handover/RECOVERY_PROMPT.md`, `docs/research/RESEARCH_OPERATING_MODEL.md`, ADR và workflow trước khi thay đổi code. Sau run quan trọng, user chỉ upload ZIP do runner tạo; verify manifest/hash trước khi phân tích.
