# V27.1 — MT5 Economic Calendar startup-race hotfix

Ngày: 2026-08-18.

## Runtime evidence từ diagnostic user

Diagnostic ZIP SHA-256: `d99d5f215ea5057ddc3bc4d917707bec0f0af54518bd4e7815b2b1e96cb8d1a1`.

MetaEditor compile: 0 errors / 0 warnings.

Terminal log cho thấy race condition rõ:
- 08:48:14.742 — `ExportEconomicCalendarV1` loaded successfully;
- 08:48:14.834 — script exits;
- 08:48:15.402 — Exness account authorized;
- 08:48:15.970 — terminal synchronized.

V1 kiểm tra `TERMINAL_CONNECTED` ngay đầu `OnStart()` và return nếu chưa connected, vì vậy script thoát khoảng 0.6 giây trước authorization và không bao giờ tạo `latest.txt`.

## V27.1 fix

- đợi tối đa 90 giây cho terminal connected + account login ready + `TimeTradeServer()>0`;
- ghi `bootstrap_status.txt` theo phase để diagnostic không còn mơ hồ;
- chia `CalendarValueHistory` thành chunk 28 ngày, retry bounded cho error 5401/4001;
- runner watchdog tăng lên 25 phút và diagnostic ZIP thu bootstrap status;
- vẫn DATA ONLY, `AllowLiveTrading=0`, không `OrderSend`, không `CTrade`.

## Release

One-click SHA-256: `872e3470b95bd5a1c850d5efc33ffd05d8024504ee6f599e70c791868eb970a4`.

Internal kit manifest: 5/5 PASS.

Windows MetaEditor/runtime V27.1 chưa được claim PASS cho đến khi user chạy hotfix và upload result/diagnostic ZIP.
