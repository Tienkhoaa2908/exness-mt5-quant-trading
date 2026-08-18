# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật an toàn
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Luật giao tiếp với user — MUST READ / MUST PRESERVE
- User không muốn thấy code Python nội bộ, scratch code, code đóng gói artifact, tool payload hoặc implementation plumbing xuất hiện trước/sau câu trả lời.
- Không trình bày code nội bộ chỉ vì tool đã chạy. Chỉ hiện code khi user chủ động yêu cầu xem code.
- Phần trả lời user phải ưu tiên: DONE / EVIDENCE / DECISIONS / ISSUES / NEXT khi phù hợp; file tải/chạy; SHA-256; hướng dẫn thao tác; chẩn đoán cụ thể.
- Tooling nội bộ phải chạy âm thầm. Không biến private/internal implementation details thành output user-facing.
- Đây là yêu cầu trực tiếp của user ngày 2026-08-18 và phải được giữ sau mọi recovery.

## Current project gate
V27 — MT5 Economic Calendar / event-aware ML-DL data gate.

Trạng thái hiện tại:
- V26 historical MT5 export đã cung cấp cross-asset bars + 17.7M XAU broker ticks.
- V26A cross-asset M30 range model có signal ổn định; direction chỉ modest.
- V1.3 low-TF top-up lấy được M5/M15 nhưng không tạo stable direction alpha; không tiếp tục M1 nếu chưa có evidence mới.
- V27 chuyển sang Economic Calendar: actual/forecast/previous/revision/importance/time-to-event để tạo data orthogonal cho XAU.

## V27.2 runtime issue / recovery
Calendar exporter compile 0 errors / 0 warnings và chạy progress thật. Run bị hard watchdog trước khi hoàn tất, không phải Calendar API failure; diagnostic cho thấy đã tới CNY, khoảng 24k rows, 80 chunks, `last_error=0`.

Partial-recovery utility đã được tạo để copy trực tiếp partial `calendar_values.csv` từ MT5 Common Files, không chạy lại exporter 90 phút.

User screenshot ngày 2026-08-18 cho thấy utility báo:
- recovered run `20260818_093825`;
- calendar CSV khoảng 5,722,996 bytes;
- output ZIP path: `C:\Users\welcome\OneDrive\Desktop\mt5_quant_calendar_PARTIAL_RECOVERY_20260818_141210.zip`.

Nếu user nói không thấy ZIP, kiểm tra OneDrive Desktop path trên trước; đừng mặc định `C:\Users\welcome\Desktop`.

## ML validation discipline
- chronological walk-forward;
- không random CV;
- partial Aug-2026 đã bị inspect nên không còn pristine để tune;
- ML/DL không được sở hữu direct Buy/Sell nếu chưa có stable OOS evidence;
- model/routing finalist phải quay lại MT5 tick-level replay trước promotion;
- LIVE vẫn forbidden.
