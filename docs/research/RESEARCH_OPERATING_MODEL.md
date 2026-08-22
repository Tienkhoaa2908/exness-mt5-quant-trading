# Mô hình vận hành nghiên cứu và nguồn tham khảo

## Nguyên tắc

Research ưu tiên theo thứ tự: correctness → safety → reproducibility → backtest integrity → risk → observability → maintainability → performance → sophistication.

Mọi hypothesis phải được chuyển thành rule cơ học, có thể backtest và có control/ablation. Không promote vì chart đẹp, tên strategy nổi tiếng, một tháng lãi lớn, hoặc vì cộng nhiều indicator.

Mọi broad search phải chịu kỷ luật multiple testing: catalog pre-register trước run; report toàn bộ candidates; không sửa parameter sau khi nhìn cùng output rồi gọi đó là xác nhận.

## Mục tiêu production/live — authoritative

Paper/DEMO không phải đích cuối của project.

Project-wide policy:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- mục tiêu là production/live trading bằng vốn thật trên Exness sau khi readiness evidence hoàn tất;
- nghiên cứu có thể bao gồm live-account architecture, capital sizing, risk controls, deployment workflow, VPS/always-on, monitoring, reconciliation và recovery;
- các guard DEMO-only của một runtime cụ thể không phải lệnh cấm nghiên cứu live cho toàn project.

ADR authoritative: `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`.

Current evidence label:
`LIVE_READINESS=PENDING_V49_FINAL`.

Không được ghi `LIVE_READY=1` khi chưa có final execution evidence. Đây là yêu cầu evidence integrity, không phải cấm nghiên cứu tiền thật.

## Active V49 execution rehearsal

V49 đã startup thành công trên Windows với static 9/9 PASS, secret scan PASS, deterministic parent chain PASS, MetaEditor `0 errors, 0 warnings`, V49 DEMO READY và detached supervisor.

V49 là one-shot engineering rehearsal:

`frozen breadth4 intent -> native Exness DEMO order -> auto close -> OnTradeTransaction reconciliation -> push notification -> execution logging -> FINAL -> one ZIP`

Minimum useful sample:
- >=3 market-active XAUUSD dates;
- >=3 completed broker-DEMO round trips;
- hard stop 14 calendar days.

Clean final may produce `LIVE_CANDIDATE_READY`. This is the trigger for the dedicated production/live engineering milestone; historical alpha campaigns are inherited rather than automatically rerun.

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

Các paper này chỉ biện minh cho việc đo time-of-day/session effect. Không hard-code session winner từ literature; phải kiểm tra riêng trên XAUUSDm/server time của broker.

### Data snooping / multiple testing

- Sullivan, Timmermann & White (1999), *Data-Snooping, Technical Trading Rule Performance, and the Bootstrap*, Journal of Finance. DOI: 10.1111/0022-1082.00163.
- White (2000), *A Reality Check for Data Snooping*, Econometrica. DOI: 10.1111/1468-0262.00152.

Các lab nhiều candidate chỉ là screening nếu chưa có holdout/forward/native evidence. Candidate mạnh vẫn phải giữ strategy identity khi chuyển sang execution rehearsal hoặc production engineering.

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

Research/tester phases có thể dùng các API chuẩn MetaQuotes như `CopyRates`, `iRSI`, `iMACD`, `iADX`, `iBands`, `OrderCalcProfit`.

Runtime execution phases dùng native MT5 trade APIs khi đúng contract của milestone. V49 hiện dùng native broker-DEMO execution và `OnTradeTransaction` để đo/reconcile broker behavior.

Các restriction của V48/V49 phải được đọc theo version semantics. Không suy rộng chúng thành permanent live-research prohibition.

## Safety / engineering discipline

- `LIVE_RESEARCH_ALLOWED=1` và `LIVE_DEPLOYMENT_TARGET=1`.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không password/token/secret trong repo.
- Strategy identity phải được giữ cố định trong campaign validation tương ứng.
- Broker ownership, duplicate prevention, reconciliation và evidence capture là bắt buộc ở execution layer.
- Risk controls phải độc lập với alpha signal.
- Promotion/readiness labels phải dựa trên evidence thật; không fabricate PASS.

## V24 — nguyên tắc ML/DL

Không dùng deep learning để bù cho feature/data yếu. Trade-level benchmark V22 cho AUC quanh 0.5 trên 2026, nên V24 tăng information density trước khi tăng model capacity.

Feature lake được xuất ở mức M15 bar, không chứa future target. Offline labels được tạo sau bundle. Model validation dùng chronological monthly walk-forward + purge 32 bars; không random K-fold.

Sequence references:
- Bai, Kolter, Koltun (2018), arXiv:1803.01271 — TCN;
- Lim, Zohren, Roberts (2019), arXiv:1904.04912 — deep momentum / turnover-aware objective;
- Nie et al. (ICLR 2023), arXiv:2211.14730 — patch Transformer / representation learning.

Các paper chỉ là architecture/hypothesis reference, không phải bằng chứng XAUUSDm có edge.
