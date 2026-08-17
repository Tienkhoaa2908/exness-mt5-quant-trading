# ML/DL Feature Lake + Regime Router Lab V1 — workflow

## Mục tiêu

Một lần chạy MT5 phải trả về đủ dữ liệu để:

1. đánh giá V23 regime routing;
2. tạo sequence dataset cho nhiều vòng ML/DL offline;
3. không yêu cầu user chạy lại Strategy Tester cho từng model/hyperparameter.

## Runtime

- XAUUSDm / M15 / generated Every Tick;
- 18 independent monthly resets;
- 3 chunk sáu tháng;
- 26 V23 candidates × 4 virtual books = 104 books;
- một ZIP output;
- tester-only, không broker order.

## Feature lake

`bar_features.csv` được ghi ở mỗi new M15 bar sau khi đủ warmup data. Mọi feature tại timestamp t chỉ dùng bar đóng và indicator state khả dụng tại t.

Không có target/future label trong MQL.

Sau upload, analyzer tạo future-return labels 4/8/16/32 bars. Model tournament dùng horizon 16 làm target chính và 32 bars làm purge buffer.

## Validation ML/DL

Không random split. Mỗi tháng OOS chỉ được dự đoán từ data trước tháng đó. Sáu tháng đầu dùng làm warm-up, còn tối đa 12 tháng OOS. Last 32 bars của training bị purge để tránh overlap target horizon.

Trade-level gate diagnostics chỉ là discovery. Finalist phải quay lại MT5 generated-Every-Tick, rồi real-tick fidelity window và native parity trước PAPER/DEMO.
