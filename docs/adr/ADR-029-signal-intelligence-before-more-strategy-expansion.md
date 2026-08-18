# ADR-029 — Ưu tiên signal intelligence trước khi mở rộng thêm strategy family

## Trạng thái

Accepted for research implementation — 2026-08-16.

## Bối cảnh

Multi-Factor Edge Lab V1 chạy 32 candidates trên 18 independent monthly resets và bốn risk books. Broad strategy expansion không tạo được profile robust 15–20%/tháng. EMA H1 base vẫn là control mạnh nhất theo median USD40@1%, khoảng +6.32%/tháng.

Hai phát hiện quan trọng hơn việc thêm indicator family:

1. Hard conjunctive quality filter làm PF của selected trades tốt hơn nhưng loại quá nhiều opportunity, khiến return giảm mạnh.
2. Targeted streak guard V21 tạo zero rejects; do đó observed sample chưa thực sự kiểm nghiệm hypothesis exhaustion đó.

Rank stability giữa 2025 và 2026 cũng thấp, nên một parameter/family sweep lớn hơn sẽ làm tăng data-snooping/backtest-overfitting risk.

## Quyết định

1. Giữ REAL-MONEY LIVE TRADING bị cấm.
2. Giữ 1.00% stop-risk là research ceiling.
3. Freeze năm family cho gate kế tiếp:
   - EMA H1 pullback/reclaim;
   - MACD(8,21,5) H1;
   - Trend20 H1 breakout;
   - BOS+FVG H1 continuation;
   - RSI2 H1 trend-reversion diagnostic.
4. Thay hard quality conjunction bằng **soft confirmation score** với threshold pre-register trước run.
5. Ghi entry-state telemetry cho từng executed trade: ADX, DI, ATR/ATR50, candle body ratio, close location, EMA200 distance theo ATR, RSI2, RSI14, MACD histogram, H1 EMA gap, server hour, prior-profit streak và bars since last exit.
6. Redesign exhaustion state:
   - count consecutive profitable exits cùng hướng dù trade trước có rapid hay không;
   - khi count >=2, block next same-direction entry tối đa 8 giờ nếu chưa có 1.00 ATR adverse reset từ profitable exit gần nhất;
   - report reject count riêng.
7. Chỉ test một bounded adaptive-exit hypothesis: strong non-RSI2 entry có thể dùng 0.75R peak-distance trail sau +1R với TP4R; còn lại dùng proven 50%-of-peak lock sau +1R / TP4R.
8. Dùng sáu pre-registered variants mỗi family:
   - base peak-lock;
   - score>=3 peak-lock;
   - score>=4 peak-lock;
   - score>=3 + exhaustion V2;
   - score>=3 + adaptive exit;
   - score>=3 + exhaustion V2 + adaptive exit.
9. Total catalog: 5 families × 6 variants = 30 candidates; 4 books/candidate = 120 virtual books trên cùng tick stream.
10. Tiếp tục 18 independent calendar-month resets trong ba generated-tick chunks sáu tháng và package một output ZIP.
11. Apparent finalist vẫn chỉ là virtual screening; phải qua native MT5 parity, spread/cost/delay stress và forward validation.

## Lý do

V21 cho thấy binary all-factor confirmation dễ over-filter. Soft score + telemetry cho phép kiểm tra cụ thể trạng thái nào phân biệt winner với false entry thay vì chỉ biết một hard gate đã reject trade.

Catalog/threshold được freeze trước run để giảm nguy cơ chọn cấu hình sau khi đã nhìn cùng sample.

## Hệ quả

Gate này không được thiết kế để “chứng minh” 15–20%/tháng. Nó kiểm tra liệu conditional entry quality, exhaustion state và adaptive profit capture có nâng AvgR/return đáng kể mà không tăng risk hoặc turnover mù quáng hay không.

Nếu AvgR vẫn không tiến đáng kể về vùng cần thiết cho practical trade count, aim 15–20%/tháng phải được xem là chưa được evidence hỗ trợ cho instrument/risk contract hiện tại, thay vì ép bằng leverage.
