# 2026-08-16 — Phân tích Churn Control Lab V1

## Toàn vẹn bằng chứng

- SHA-256 ZIP đã tải lên: `2579e7806855bdb608cdc9f3987699ad625bf94dd9494467cea6e388ccd5a9ba`.
- `bundle_manifest_sha256.txt`: **PASS 22/22**.
- Windows MetaEditor: **0 lỗi, 0 cảnh báo**.
- Bao phủ: 18 tháng độc lập từ 2025-02 đến 2026-07, chia thành ba chunk sáu tháng.
- Chỉ Strategy Tester với virtual books; native broker orders = 0; external broker orders = 0.
- Source: `ChurnControlLabV1.mq5`.

## Kết quả chính

Không promote giả thuyết cooldown/re-arm tổng quát.

Ở book USD40 / stop-risk 1.00%, `ema_h1_control` không đổi vẫn mạnh nhất theo median return tháng:

- median +6.3236%;
- mean +4.8389%;
- dương 13/18 tháng;
- >=10%: 3/18; >=15%: 0/18;
- worst -4.5875%; best +14.7376%;
- max MTM DD 9.0171%;
- median PF 1.4765;
- median 34.5 trades/tháng;
- turnover proxy median ~149.29x vốn đầu tháng.

Các rule churn tốt nhất có giảm hoạt động nhưng cũng làm giảm return:

- `ema_h1_cd_profit_8`: median +5.3962%;
- `ema_h1_cd_profit_16`: median +5.2387%, max MTM DD 8.1630%, rapid post-profit losses giảm còn 15 so với 104 của control;
- `ema_h1_rearm_profit_0p50atr`: median +4.3474%, turnover ~110.97x.

Kết luận: giảm turnover tự nó chưa đủ. Cooldown áp dụng đại trà chặn cả nhiều re-entry có edge.

## Chẩn đoán sequence — đúng failure mode cần nhắm

Quan sát “sau một chuỗi trade thắng lại có trade cùng hướng vào non rồi thua” tồn tại thật trong ledger.

Với `ema_h1_control` / USD40@1%:

- tổng 607 trades;
- trade vào lại trong <=4 giờ sau một profitable exit có loss-rate cao hơn nhóm còn lại;
- sau **hai trade trước đều lời và cùng hướng**, trade cùng hướng kế tiếp có expectancy yếu đi rõ;
- riêng SHORT có 50 trường hợp trade thứ ba sau hai SHORT thắng liên tiếp:
  - loss-rate khoảng 52%;
  - average R xấp xỉ 0;
- trong đó 41 trường hợp re-entry trong <=4 giờ:
  - loss-rate khoảng 53.7%;
  - average R khoảng -0.109;
  - tổng PnL âm.

Target đúng vì vậy không phải “mọi re-entry đều xấu”, mà là **exhaustion của local move sau nhiều profitable exits cùng hướng**.

## Chẩn đoán theo giờ giao dịch

EMA control ở bucket broker/server 20:00–23:59 có:

- 49 trades;
- loss-rate ~63.3%;
- average R khoảng -0.282;
- tổng PnL âm.

Nhưng hiện tượng này **không đồng nhất giữa strategy families**: Trend H1 không yếu cùng cách ở bucket này. Vì vậy không hard-code global time ban. Lab kế tiếp chỉ test late-session exclusion như một ablation riêng từng family.

## Quyết định

1. Giữ 1.00% stop-risk là research ceiling.
2. Đóng băng peak-lock exit: initial stop 2 ATR, TP4R, sau +1R bảo vệ 50% peak R.
3. Không promote generic cooldown/re-arm.
4. Thay churn-only lab bằng **Multi-Factor Edge Lab V1** chạy một lượt lớn.
5. Lab mới xử lý đồng thời:
   - thêm nhiều signal family độc lập;
   - entry discrimination bằng các factor khác loại;
   - exhaustion guard có state chỉ sau hai profitable exits nhanh cùng hướng;
   - late-session ablation riêng từng family.
6. Virtual finalist vẫn phải qua native MT5 parity trước PAPER/DEMO.
7. REAL-MONEY LIVE TRADING vẫn bị cấm.
