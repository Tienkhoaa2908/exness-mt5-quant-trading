# Windows MT5 / Exness — setup nghiên cứu hiện tại

## Trạng thái đã xác nhận

- MetaTrader 5 và MetaEditor trên Windows hoạt động.
- Broker: Exness Technologies Ltd.
- Symbol gold của account nghiên cứu: `XAUUSDm`.
- Timeframe chính: M15.
- Strategy Tester dùng generated `Every tick` cho long screening; real-tick gate được dùng riêng để kiểm tra fidelity khi coverage cho phép.
- REAL-MONEY LIVE TRADING bị cấm.

## Chạy Multi-Factor Edge Lab V1

1. Đóng hoàn toàn MT5 trước khi chạy.
2. Lấy V21 one-click kit hoặc clean clone GitHub.
3. Nếu là clean clone, root CMD sẽ tự giải nén `recovery/v21_impl_payload.zip` nếu source/scripts chưa có.
4. Double-click `RUN_MULTI_FACTOR_EDGE_LAB_V1.cmd`.
5. Runner tự tìm MT5 data folder tương ứng với `C:\Program Files\MetaTrader 5\terminal64.exe`.
6. MetaEditor phải compile `MultiFactorEdgeLabV1.mq5` với 0 errors / 0 warnings; nếu không runner dừng.
7. Runner chạy ba chunk sáu tháng, có heartbeat/watchdog/retry/checkpoint.
8. Khi hoàn tất, Desktop có một file ZIP dạng `mt5_quant_multi_factor_edge_lab_v1_YYYYMMDD_HHMMSS.zip`.
9. Chỉ upload ZIP đó vào chat. Không cần gửi từng screenshot.

Runner không chứa password/token. Nếu không truyền `-Login`, terminal dùng account/session MT5 hiện tại. `AllowLiveTrading=0`, `AllowDllImport=0`, EA có tester guard và không có native/external broker order path.

## Khi runner lỗi

Không force-kill rồi xóa evidence ngay. Runner đã có diagnostic/checkpoint logic. Nếu chunk fail sau retry, giữ màn hình lỗi và checkpoint; không chuyển sang live/manual order.

## Native parity

Multi-Factor Edge Lab V1 chỉ là virtual screening. Nếu có finalist:
- viết native finalist riêng;
- kiểm tra dynamic trade session;
- xác minh account mode Netting/Hedging;
- kiểm tra retcode;
- stress spread/delay/cost;
- chỉ PAPER/DEMO sau safety gates.

LIVE vẫn cấm.
