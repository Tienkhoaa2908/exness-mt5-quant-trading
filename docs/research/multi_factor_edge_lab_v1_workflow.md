# Multi-Factor Edge Lab V1 — quy trình nghiên cứu một lần chạy

## Mục tiêu

Chạy một ma trận nghiên cứu lớn đã pre-register trong một lần vận hành Windows MT5, để không phải chạy nhiều thí nghiệm nhỏ lẻ.

Mức 15–20%/tháng trên book USD40 vẫn chỉ là mục tiêu/hit-rate cần đo, không phải lợi nhuận hứa hẹn và không phải lý do tăng risk vượt ceiling.

## Ma trận thí nghiệm

Tám signal families độc lập:

1. EMA10 pullback/reclaim + H1 alignment.
2. Trend breakout 20 bar + H1 alignment.
3. RSI(2) trend-reversion + H1 alignment.
4. MACD(8,21,5) cross + H1 alignment.
5. Donchian breakout 55 bar + H1 alignment.
6. Bollinger(20,2) + RSI14 range-reversion khi ADX thấp.
7. Liquidity sweep kiểu ICT/SMC: quét extreme của 20 bar trước rồi đóng trở lại bên trong, có H1 alignment.
8. BOS+FVG continuation kiểu ICT/SMC: break cấu trúc 20 bar cộng imbalance 3 nến đo được, có H1 alignment.

Không dùng nhãn chart chủ quan. Các khái niệm ICT/SMC được biến thành rule OHLC định lượng và chỉ được xem là hypothesis.

Bốn variants cho mỗi family:

- `base`;
- `quality`;
- `quality_streak`;
- `quality_streak_late20`.

Tổng: **32 candidates**.

Bốn books trên mỗi candidate:

- normalized USD10k @0.50%;
- USD40 @0.50%;
- USD40 @0.75%;
- USD40 @1.00%.

Tổng cộng **128 virtual books** trên cùng tick stream.

## Quality filter

Variant `quality` phối hợp các factor khác loại, tránh chất nhiều indicator cùng bản chất:

- volatility regime ATR14 / ATR50;
- ADX14 để đo strength/regime;
- +DI/-DI agreement cho nhóm trend;
- candle body/range và close-location theo hướng;
- khoảng cách đến EMA200 để tránh chase quá xa;
- rule riêng cho mean-reversion và liquidity-sweep.

Mục tiêu là loại setup chỉ thỏa một trigger đơn nhưng thiếu price action/regime confirmation.

## Exhaustion guard có state

Generic cooldown đã bị V20 reject vì giảm churn nhưng cũng giảm return.

`quality_streak` chỉ can thiệp vào sequence cụ thể:

- đã có hai profitable exits nhanh cùng hướng;
- xuất hiện signal thứ ba cùng hướng trong 16 bar M15 (4 giờ);
- re-entry bị chặn cho đến khi giá reset ngược ít nhất 0.50 ATR từ profitable exit gần nhất, hoặc qua 4 giờ.

Rule này nhắm trực tiếp pattern “hai trade ăn rồi trade thứ ba cùng hướng vào non và bị trap”.

## Late-session ablation

`quality_streak_late20` chặn entry mới khi broker/server hour >=20.

Đây chỉ là ablation candidate, không phải global rule. V20 cho thấy EMA yếu ở late bucket nhưng Trend thì không. Chỉ promote nếu evidence theo từng family và qua nhiều tháng hỗ trợ.

## Exit và risk được đóng băng

Mọi candidate dùng:

- initial stop = 2 ATR;
- TP = 4R;
- khi MFE >= +1R thì bảo vệ 50% peak R;
- không Martingale;
- không grid;
- không doubling after loss;
- không native position stacking;
- stop-risk research ceiling = 1.00%.

Lab chỉ dùng virtual books trong Strategy Tester; không `CTrade`, không `OrderSend`, không external broker orders.

## Cách chạy

Chỉ cần double-click:

`RUN_MULTI_FACTOR_EDGE_LAB_V1.cmd`

Runner sẽ:

- nếu clean clone chưa materialize source/scripts thì tự giải nén `recovery/v21_impl_payload.zip`;
- compile `MultiFactorEdgeLabV1.mq5`;
- chạy ba chunk generated-Every-Tick, mỗi chunk sáu tháng;
- reset độc lập 18 tháng bên trong EA;
- heartbeat mỗi 30 giây;
- watchdog giới hạn 30 phút/chunk;
- phát hiện lỗi broker synchronization;
- retry một lần;
- reuse checkpoint LocalAppData đã validate;
- recover artifact hợp lệ từ Common Files;
- tạo đúng **một ZIP output** trên Desktop.

Expected summary rows: 18 tháng × 32 candidates × 4 books = **2,304**.

## Kỷ luật promote

So sánh chính:

- median/mean return theo tháng;
- tỷ lệ tháng dương;
- hit-rate >=10/15/20%;
- worst/best month;
- PF / AvgR / MTM DD;
- trades/tháng và turnover;
- rapid re-entry / post-profit loss;
- quality/streak/session reject counts;
- ổn định 2025 so với 2026;
- ablation `base -> quality -> quality+streak -> late-session` trong từng family.

Không chọn candidate chỉ vì một tháng đột biến. Finalist phải quay lại native MT5 và sau đó qua spread/delay stress trước PAPER/DEMO.

REAL-MONEY LIVE TRADING vẫn bị cấm.
