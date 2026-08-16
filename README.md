# Exness / MetaTrader 5 Quant Trading

Kho nghiên cứu cho hệ thống giao dịch định lượng MT5/Exness.

**REAL-MONEY LIVE TRADING = FORBIDDEN.** Chỉ offline analysis, MetaTrader 5 Strategy Tester và PAPER/DEMO sau safety gates. Không Martingale, uncontrolled grid, doubling after loss, không bỏ LIVE guards và không commit password/token/secret.

## Trạng thái hiện tại

- Signal Intelligence Lab V1 / V22 đã hoàn tất runtime: bundle SHA-256 `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`, integrity 22/22 PASS, MetaEditor 0 errors / 0 warnings, 18 tháng đầy đủ, external broker orders = 0.
- `ema_h1_base` vẫn là control mạnh nhất: median USD40@1% khoảng +6.32%/tháng; chưa có evidence robust cho aim 15–20%/tháng.
- Soft score chung, global exhaustion guard và telemetry meta-labeling không được promote.
- Regime shift 2025→2026 là vấn đề chính; gate kế tiếp là **V23 Regime Router Lab V1** với family-specific regime/session routing và targeted EMA SHORT exhaustion.
- V23 dự kiến 26 candidates × 4 books = 104 virtual books, 18 monthly resets, 3 chunks và một output ZIP.

Canonical recovery state: `docs/handover/CURRENT_STATE.md` và `docs/handover/RECOVERY_PROMPT.md`.
