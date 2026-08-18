# Signal Intelligence Lab V1 — quy trình một lần chạy

## Mục tiêu

Giảm susceptibility với false entry bằng cách ghi telemetry trạng thái trước entry, dùng soft confirmation score thay cho hard conjunction, sửa exhaustion guard để thực sự có cơ hội tác động, và kiểm tra một adaptive-exit ablation có giới hạn. Toàn bộ gate được gom vào một lần chạy của user.

## Năm signal family giữ lại

1. `ema_h1`
2. `macd_h1`
3. `trend20_h1`
4. `bos_fvg_h1`
5. `rsi2_h1`

Donchian55 bị loại khỏi active search vì redundancy cao với Trend20 và yếu rõ ở 2026. Liquidity sweep bị loại khỏi active search vì median V21 âm. BB+RSI V21 tạo zero raw signals nên được phân loại là **chưa được kiểm nghiệm**, không phải alpha family đã bị chứng minh thất bại.

## Sáu variant mỗi family

1. `base`
   - không threshold score;
   - dùng peak-lock exit control.

2. `score3`
   - soft confirmation score >=3;
   - peak-lock exit.

3. `score4`
   - soft confirmation score >=4;
   - peak-lock exit.

4. `score3_exhaust`
   - score >=3;
   - exhaustion V2;
   - peak-lock exit.

5. `score3_adaptive`
   - score >=3;
   - bounded adaptive exit.

6. `score3_exhaust_adaptive`
   - score >=3;
   - exhaustion V2;
   - bounded adaptive exit.

Tổng: 30 candidates × 4 books = 120 virtual books.

## Soft confirmation score

Score là tổng có giới hạn của các state checks được pre-register, không phải optimizer. Không thay threshold sau khi nhìn output rồi gọi đó là validation.

Telemetry entry gồm:
- ATR14 / ATR50 volatility ratio;
- ADX14;
- +DI / -DI directional agreement;
- candle body / range;
- direction-adjusted close location;
- distance đến EMA200 tính theo ATR;
- RSI2;
- RSI14;
- MACD histogram;
- H1 EMA50 - EMA200 separation tính theo ATR;
- server hour;
- profit streak trước entry;
- số M15 bars từ exit gần nhất.

Score component được family-specific để mean-reversion không bị ép qua cùng trend-strength rule như breakout/trend.

## Exhaustion V2

Sau hai profitable exits liên tiếp cùng hướng:
- streak vẫn được giữ bất kể trade thứ hai có phải rapid re-entry hay không;
- next same-direction signal trong 32 M15 bars (8 giờ) bị reject nếu giá chưa có adverse reset ít nhất 1.00 ATR từ profitable exit gần nhất;
- mọi reject được đếm bằng `streak_guard_reject`;
- trade ledger ghi `entry_profit_streak_before` và `entry_bars_since_exit` để xác minh guard thật sự được exercised.

Thiết kế này cố ý mạnh hơn V21 vì guard V21 0.50 ATR / 4h tạo zero rejects trong sample.

## Adaptive exit ablation

Default exit không đổi:
- initial stop = 2 ATR;
- TP = 4R;
- sau MFE >= +1R, bảo vệ 50% peak R.

Adaptive mode chỉ bật khi:
- family không phải RSI2;
- `quality_score >= 4`;
- `ADX >= 25` tại entry.

Khi bật:
- sau +1R, trailing protection nằm 0.75R sau peak;
- TP vẫn 4R.

Mục tiêu là kiểm tra xem strong-state entries có nên được cho thêm room để giữ winner hay không, không mở grid exit parameter.

## Books / risk

Bốn book độc lập mỗi candidate:
- normalized USD10k @0.50%;
- USD40 @0.50%;
- USD40 @0.75%;
- USD40 @1.00%.

Không upward volume rounding. Margin stress 1:200. Stop-risk >1.00% nằm ngoài gate.

## Lịch chạy

Ba generated-tick chunk sáu tháng:
- 2025-02 → 2025-08;
- 2025-08 → 2026-02;
- 2026-02 → 2026-08.

EA reset books tại calendar-month boundary để giữ 18 monthly observations độc lập. Runner có heartbeat, bounded watchdog, broker-unavailable detection, một retry, checkpoint reuse, Common Files recovery và một final ZIP.

## Metrics bắt buộc

Không chọn winner theo best month.

Phải report:
- median/mean monthly return;
- positive-month ratio và >=10/15/20% hit rates;
- AvgR / PF / win rate;
- max MTM DD;
- trades/month;
- turnover proxy;
- score-reject và streak-reject counts;
- rapid post-profit loss rate;
- third-entry sequence theo direction;
- telemetry distribution của winners vs losers;
- 2025 vs 2026 stability;
- base → score3 → score4 → exhaustion → adaptive ablation.

Virtual candidate chỉ được promote thành finalist để native/forward validation, không được deploy trực tiếp.

REAL-MONEY LIVE TRADING vẫn bị cấm.
