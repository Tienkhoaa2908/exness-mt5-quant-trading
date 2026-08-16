# Exness / MetaTrader 5 Quant Trading

Kho nghiên cứu cho hệ thống giao dịch định lượng MT5/Exness.

**REAL-MONEY LIVE TRADING = FORBIDDEN.** Giai đoạn hiện tại chỉ cho phép offline analysis, MetaTrader 5 Strategy Tester và các bước PAPER/DEMO sau khi qua safety gates. Không Martingale, uncontrolled grid, doubling after loss, không bỏ LIVE guards và không commit password/token/secret.

## Trạng thái hiện tại

- Churn Control Lab V1 đã hoàn tất và không promote generic cooldown/re-arm.
- Failure mode mới được xác nhận: re-entry cùng hướng sau một chuỗi profitable exits có thể suy giảm expectancy, đặc biệt nhóm SHORT thứ ba vào nhanh sau hai SHORT thắng.
- Next gate: **Multi-Factor Edge Lab V1**.
- Một lần double-click `RUN_MULTI_FACTOR_EDGE_LAB_V1.cmd` chạy 32 candidates × 4 books trên cùng tick stream, 18 tháng độc lập, và đóng gói **một ZIP**.
- Remote recovery mirror lưu implementation V21 tại `recovery/v21_impl_payload.zip`; root CMD tự materialize `mql5/`, `scripts/` và experiment config nếu clean clone chưa có các file đó.

Canonical recovery state nằm tại `docs/handover/CURRENT_STATE.md` và `docs/handover/RECOVERY_PROMPT.md`.
