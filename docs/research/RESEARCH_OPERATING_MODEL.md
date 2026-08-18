# Mô hình vận hành nghiên cứu và nguồn tham khảo

## Nguyên tắc

Research ưu tiên theo thứ tự: correctness → safety → reproducibility → backtest integrity → risk → observability → maintainability → performance → sophistication.

Mọi hypothesis phải được chuyển thành rule cơ học, có thể backtest và có control/ablation. Không promote vì chart đẹp, tên strategy nổi tiếng, một tháng lãi lớn, hoặc vì cộng nhiều indicator.

Mọi broad search phải chịu kỷ luật multiple testing: catalog pre-register trước run; report toàn bộ candidates; không sửa parameter sau khi nhìn cùng output rồi gọi đó là xác nhận; winner phải qua forward/native/cost stress mới.

Khi cùng một data pass có thể đo nhiều bounded hypotheses, runner phải gom chúng thành một one-click batch và một output ZIP để giảm manual rerun.

## Evidence hierarchy

1. Static QA chỉ chứng minh source/safety, không chứng minh runtime.
2. Windows MetaEditor compile chứng minh compile, không chứng minh edge.
3. Strategy Tester output + manifest/log/trade ledger là truth source cho virtual labs.
4. Conditional filtering của trade ledger chỉ là hypothesis discovery nếu filter thay đổi opportunity set; phải re-simulate gate thật.
5. Virtual finalist phải quay lại native MT5 parity trước PAPER/DEMO.
6. LIVE luôn bị cấm.

## Nguồn nghiên cứu chính

### Trend / momentum

- Moskowitz, Ooi, Pedersen (2012), *Time Series Momentum*, Journal of Financial Economics. DOI: 10.1016/j.jfineco.2011.11.003.
- Hurst, Ooi, Pedersen (2017), *A Century of Evidence on Trend-Following Investing*.

Dùng để biện minh cho trend/momentum như family độc lập và yêu cầu đánh giá qua nhiều regime/horizon, không copy parameter.

### Trading frictions / churn

- Gârleanu & Pedersen (2013), *Dynamic Trading with Predictable Returns and Transaction Costs*, Journal of Finance. DOI: 10.1111/jofi.12080.
- Novy-Marx & Velikov (2016), *A Taxonomy of Anomalies and Their Trading Costs*, Review of Financial Studies. DOI: 10.1093/rfs/hhv063.

Reference cho inaction/hysteresis và turnover control; không biến thành hard-coded rule nếu XAUUSDm evidence không hỗ trợ.

### Intraday seasonality

- Cotter & Dowd (2010), *Intra-day seasonality in foreign exchange market transactions*, International Review of Economics & Finance. DOI: 10.1016/j.iref.2009.08.003.
- Ito & Hashimoto (2006), *Intraday seasonality in activities of the foreign exchange markets*, Journal of the Japanese and International Economies. DOI: 10.1016/j.jjie.2006.06.005.

Các paper chỉ biện minh cho việc **đo** time-of-day/session effect. Không hard-code session winner từ literature; phải kiểm tra riêng trên XAUUSDm/server time.

### Data snooping / multiple testing

- Sullivan, Timmermann & White (1999), *Data-Snooping, Technical Trading Rule Performance, and the Bootstrap*, Journal of Finance. DOI: 10.1111/0022-1082.00163.
- White (2000), *A Reality Check for Data Snooping*, Econometrica. DOI: 10.1111/1468-0262.00152.

V21/V22 là screening catalogs, không phải final validation. Candidate mạnh vẫn phải qua holdout/forward, native parity và cost/spread/delay stress.

### ICT / SMC reference

- `joshyattridge/smart-money-concepts` trên GitHub, MIT license.
  - Chỉ dùng làm reference cho Fair Value Gap, swing high/low, liquidity.
  - Không copy source code.
- Repo SMC không có license rõ hoặc chỉ phát hành binary `.ex5` không được copy vào core.

ICT/SMC không được coi là edge đã chứng minh. Trong core chỉ dùng abstraction đo được bằng OHLC.

### Regime handling after V22

V22 cho thấy soft score chung, global exhaustion guard và telemetry meta-labeling không generalize đủ; edge giảm mạnh từ 2025 sang 2026. V23 vì vậy ưu tiên observable family-specific regime/session proxies trước latent-regime/ML phức tạp, để hạn chế degrees of freedom và data snooping.

### MQL5 implementation

Chỉ dùng API chuẩn MetaQuotes cho dữ liệu/indicator/risk virtual. Lab tester-only không gọi `OrderSend`/`CTrade`.

## Safety

- REAL-MONEY LIVE TRADING: FORBIDDEN.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không password/token/secret trong repo.
- Stop-risk research ceiling hiện tại: 1.00%.
- Virtual screening không được deploy trực tiếp.
