# Exness / MetaTrader 5 Quant Trading

Kho nghiên cứu cho hệ thống giao dịch định lượng MT5/Exness.

**REAL-MONEY LIVE TRADING = FORBIDDEN.** Chỉ offline analysis, MetaTrader 5 Strategy Tester và PAPER/DEMO sau safety gates. Không Martingale, uncontrolled grid, doubling after loss, không bỏ LIVE guards và không commit password/token/secret.

## Trạng thái hiện tại

- Multi-Factor Edge Lab V1 đã hoàn tất: bundle SHA-256 `c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`, integrity 22/22 PASS, MetaEditor 0 errors / 0 warnings.
- `ema_h1_base` vẫn là control mạnh nhất: median USD40@1% khoảng +6.32%/tháng; chưa có evidence robust cho aim 15–20%/tháng.
- Hard quality conjunction bị reject vì over-filter; V21 streak guard là no-op trong sample (`streak_guard_reject=0`) nên chưa được xem là đã kiểm nghiệm thành công/thất bại.
- Next gate: **Signal Intelligence Lab V1**.
- Một lần double-click `RUN_SIGNAL_INTELLIGENCE_LAB_V1.cmd` chạy 30 candidates × 4 books, 18 monthly resets trong 3 chunk và đóng gói **một ZIP**.

Canonical recovery state: `docs/handover/CURRENT_STATE.md` và `docs/handover/RECOVERY_PROMPT.md`.
