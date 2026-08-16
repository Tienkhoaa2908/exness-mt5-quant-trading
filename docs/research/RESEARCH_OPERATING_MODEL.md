# Mô hình vận hành nghiên cứu và nguồn tham khảo

## Nguyên tắc

Research ưu tiên theo thứ tự: correctness → safety → reproducibility → backtest integrity → risk → observability → maintainability → performance → sophistication.

Mọi hypothesis phải được chuyển thành rule cơ học, có thể backtest và có control/ablation. Không promote vì chart đẹp, tên strategy nổi tiếng, một tháng lãi lớn, hoặc vì cộng nhiều indicator.

Mọi broad search phải chịu kỷ luật multiple testing: catalog pre-register trước run; report toàn bộ candidates; không sửa parameter sau khi nhìn cùng output rồi gọi đó là xác nhận; winner phải qua forward/native/cost stress mới.

## Nguồn nghiên cứu chính

### Trend / momentum

- Moskowitz, Ooi, Pedersen (2012), *Time Series Momentum*, Journal of Financial Economics. DOI: 10.1016/j.jfineco.2011.11.003.
  - Dùng để biện minh cho việc giữ trend/momentum như một family độc lập, không phải để copy parameter.
- Hurst, Ooi, Pedersen (2017), *A Century of Evidence on Trend-Following Investing*.
  - Dùng làm evidence rằng trend following cần được đánh giá qua nhiều regime/horizon, không chỉ một đoạn data.

### Trading frictions / churn

- Gârleanu & Pedersen (2013), *Dynamic Trading with Predictable Returns and Transaction Costs*, Journal of Finance. DOI: 10.1111/jofi.12080.
  - Lý do nghiên cứu inaction/hysteresis thay vì phản ứng với mọi signal.
- Novy-Marx & Velikov (2016), *A Taxonomy of Anomalies and Their Trading Costs*, Review of Financial Studies. DOI: 10.1093/rfs/hhv063.
  - Buy/hold spread và turnover control là reference cho yêu cầu entry mới phải khó hơn việc tiếp tục giữ exposure.

### Intraday seasonality

- Cotter & Dowd (2010), *Intra-day seasonality in foreign exchange market transactions*, International Review of Economics & Finance. DOI: 10.1016/j.iref.2009.08.003.
- Ito & Hashimoto (2006), *Intraday seasonality in activities of the foreign exchange markets*, Journal of the Japanese and International Economies. DOI: 10.1016/j.jjie.2006.06.005.

Các paper này chỉ biện minh cho việc **đo** time-of-day/session effect. Không hard-code session winner từ literature; phải kiểm tra riêng trên XAUUSDm/server time của broker.

### Data snooping / multiple testing

- Sullivan, Timmermann & White (1999), *Data-Snooping, Technical Trading Rule Performance, and the Bootstrap*, Journal of Finance. DOI: 10.1111/0022-1082.00163.
- White (2000), *A Reality Check for Data Snooping*, Econometrica. DOI: 10.1111/1468-0262.00152.

Multi-Factor Edge Lab V1 đã chạy 32 candidates trong cùng sample và cho rank stability 2025/2026 thấp; mọi ranking của V21 chỉ là screening. Signal Intelligence Lab V1 tiếp tục dùng catalog pre-register 30 candidates, không mở optimizer. Candidate mạnh vẫn phải qua holdout/forward, native parity và cost/spread/delay stress.

### ICT / SMC reference

- `joshyattridge/smart-money-concepts` trên GitHub, MIT license.
  - Chỉ dùng như reference để chuẩn hóa các khái niệm định lượng như Fair Value Gap, swing high/low, liquidity.
  - Không copy source code.
- Các repo SMC không có license rõ hoặc chỉ phát hành binary `.ex5` không được copy vào core.

ICT/SMC không được coi là edge đã chứng minh. Trong core chỉ tồn tại các abstraction đo được:
- liquidity sweep = quét một extreme xác định rồi đóng trở lại;
- BOS = close vượt một trading range xác định;
- FVG = imbalance ba nến theo inequality OHLC rõ ràng.

### MQL5 implementation

Chỉ dùng API chuẩn MetaQuotes:
- `CopyRates`;
- `iRSI`;
- `iMACD`;
- `iADX`;
- `iBands`;
- `OrderCalcProfit` cho tính risk virtual.

Lab tester-only không gọi `OrderSend`/`CTrade`.

## Safety

- REAL-MONEY LIVE TRADING: FORBIDDEN.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không password/token/secret trong repo.
- Stop-risk research ceiling hiện tại: 1.00%.
- Virtual screening không được deploy trực tiếp.
