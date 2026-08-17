# Windows MT5 / Exness — setup nghiên cứu hiện tại

## Trạng thái đã xác nhận

- MetaTrader 5 và MetaEditor trên Windows hoạt động.
- Broker nghiên cứu: Exness Technologies Ltd.
- Symbol gold của account nghiên cứu: `XAUUSDm`.
- Timeframe chính: M15.
- Long screening dùng generated `Every tick`; real-tick fidelity gate được chạy riêng khi coverage cho phép.
- REAL-MONEY LIVE TRADING bị cấm.

## Chạy Signal Intelligence Lab V1 (V22)

1. Đóng hoàn toàn MT5 trước khi chạy.
2. Giải nén V22 one-click kit vào một thư mục bình thường trên Windows.
3. Double-click `RUN_SIGNAL_INTELLIGENCE_LAB_V1.cmd`.
4. Runner tự tìm MT5 data folder tương ứng với `C:\Program Files\MetaTrader 5\terminal64.exe`.
5. MetaEditor phải compile `SignalIntelligenceLabV1.mq5` với 0 errors / 0 warnings; nếu compile fail thì runner dừng và giữ evidence.
6. Runner chạy ba chunk sáu tháng, có heartbeat, bounded watchdog, broker-unavailable detection, một retry, checkpoint reuse và Common Files recovery.
7. Khi hoàn tất, Desktop có đúng một output ZIP dạng `mt5_quant_signal_intelligence_lab_v1_YYYYMMDD_HHMMSS.zip`.
8. Chỉ upload ZIP đó vào chat. Không cần gửi từng screenshot hay từng CSV riêng.

## Safety contract của runner

- Template có `AllowLiveTrading=0` và `AllowDllImport=0`.
- EA có `MQL_TESTER` guard.
- Lab dùng virtual books; không có `OrderSend`, không `CTrade`, không native/external broker order path.
- Runner không chứa password/token/secret và không hard-code login account.
- Stop-risk research ceiling vẫn là 1.00%/trade.

## Khi runner lỗi

Không chuyển sang manual/live order để “test nhanh”. Giữ checkpoint/log/diagnostic evidence. Runner đã có bounded watchdog và retry; nếu vẫn fail thì package diagnostic hoặc upload output/error artifact hiện có để phân tích.

## Sau V22

Signal Intelligence Lab V1 chỉ là virtual screening. Candidate chỉ được xem là finalist nếu cải thiện joint return / AvgR / DD / turnover / regime stability và không phải do một vài tháng outlier.

Finalist sau đó phải qua:
- native MT5 parity;
- dynamic broker-session handling;
- Netting/Hedging account-mode correctness;
- spread/delay/cost stress;
- forward/holdout validation;
- PAPER/DEMO sau safety gates.

LIVE vẫn cấm.

## V24 ML/DL Feature Lake

Đóng MT5 hoàn toàn, giải nén V24 kit và double-click `RUN_ML_DL_FEATURE_LAKE_LAB_V1.cmd`. Runner compile EA mới, chạy ba chunk sáu tháng, kiểm tra đủ summary/trades/bar_features và đóng gói một ZIP duy nhất trên Desktop. Upload ZIP đó; không cần tự chạy Python ML/DL trên máy Windows.
