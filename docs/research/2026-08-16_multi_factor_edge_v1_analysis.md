# Multi-Factor Edge Lab V1 — phân tích

Ngày: 2026-08-16

Uploaded bundle SHA-256: `c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`.

Integrity: **22/22 SHA-256 PASS**. Windows MetaEditor compile: **0 errors / 0 warnings**. Ba chunk sáu tháng hoàn tất, bao phủ 18 calendar months độc lập từ 2025-02 đến 2026-07. Lab giữ tester-only virtual books với `native_broker_orders=0`, `external_broker_orders=0`.

## Kết quả chính — USD40 @1.00% stop-risk research ceiling

| Candidate | Median tháng | Positive | >=15% | Worst | Best | Max MTM DD | Median PF | Median trades | Median turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ema_h1_base` | **+6.32%** | 13/18 | 0/18 | -4.59% | +14.74% | 9.02% | 1.476 | 34.5 | 149.3x |
| `macd_h1_base` | +4.65% | 13/18 | 3/18 | -13.09% | +17.70% | 15.77% | 1.242 | 43.5 | 195.3x |
| `trend20_h1_base` | +3.78% | 13/18 | 0/18 | -6.32% | +13.51% | 11.30% | 1.397 | 31.0 | 150.0x |
| `ema_h1_quality` | +2.31% | 14/18 | 0/18 | -4.85% | +6.24% | 7.29% | 1.681 | 11.5 | 53.4x |
| `bos_fvg_h1_base` | +1.84% | 13/18 | 1/18 | -8.69% | +15.30% | 10.99% | 1.167 | 30.5 | 146.8x |

Không candidate nào robustly tiến gần aim 15–20%/tháng. `macd_h1_base` có ba tháng >=15% nhưng left tail và drawdown xấu hơn EMA rõ rệt.

## Hard quality gate over-filter

Conjunctive quality filter cải thiện một số selected-trade statistics nhưng phá quá nhiều opportunity:

- EMA: median return 6.32% → 2.31%; median turnover 149.3x → 53.4x; max MTM DD 9.02% → 7.29%; median PF 1.476 → 1.681.
- MACD: 4.65% → 0.14%.
- Trend20: 3.78% → 0.86%.
- BOS+FVG: 1.84% → -0.06%.
- Donchian55: 1.60% → -0.54%.

Đây là evidence chống lại all-or-nothing multi-factor conjunction. Gate kế tiếp phải đo soft confirmation score và giữ feature telemetry thay vì yêu cầu mọi factor cùng đúng.

## Streak guard V21 là no-op trong sample

Với mọi family, `quality_streak` bằng đúng `quality` và `streak_guard_reject=0`.

Code V21 yêu cầu đồng thời:
1. rapid same-direction profitable sequence để build streak;
2. third same-direction signal trong bốn giờ;
3. chưa có 0.50 ATR adverse reset từ profitable exit gần nhất.

Observed sample không gặp đủ ba điều kiện tại entry. Vì vậy V21 **không kiểm nghiệm được** proposed exhaustion guard. Đây là experiment miss/no-op, không phải evidence rằng exhaustion control vô dụng.

Guard mới phải:
- count consecutive same-direction profitable exits độc lập với rapid-entry status;
- dùng state window rộng hơn;
- yêu cầu reset mạnh hơn, pre-register 1.00 ATR;
- log pre-entry streak state vào trade ledger.

## Sequence diagnostics

Với `ema_h1_base` USD40@1%:
- 155 third entries xảy ra sau hai profitable trades liền trước cùng hướng;
- overall third-entry loss rate ~48.4%, average ~+0.062R;
- 50 trường hợp là SHORT third entry: loss rate 52%, average gần flat;
- 40 SHORT third entries xảy ra trong <=4h từ prior exit: loss rate ~52.5%, average khoảng **-0.086R**.

Pathology vì vậy là asymmetric/conditional. Broad EMA third-entry population không đồng loạt xấu, nhưng rapid SHORT exhaustion vẫn âm.

So sánh:
- MACD third-entry sequences vẫn dương trung bình;
- Trend20 third-entry sequences vẫn dương;
- BOS+FVG SHORT third-entry sequences âm;
- Donchian55 SHORT third-entry sequences âm;
- liquidity-sweep base âm overall.

Global rule kiểu “block trade thứ ba” sẽ over-filter.

## Entry-expectancy bottleneck

Trên executed USD40@1% base trades:
- EMA: 607 trades, AvgR ~+0.170;
- MACD: 799, AvgR ~+0.103;
- Trend20: 572, AvgR ~+0.134;
- BOS+FVG: 564, AvgR ~+0.125.

Với stop-risk ceiling 1% và khoảng 30–45 trades/tháng, strategy cần roughly 0.33–0.50R average expectancy/trade để mechanically support khoảng 15%/tháng trước compounding/frictions. Current base AvgR chỉ khoảng một phần ba đến một nửa mức đó.

Do đó chỉ thêm signals hoặc tăng risk không giải quyết target một cách robust.

## Regime stability

Rank stability yếu: Spearman correlation của candidate median-return ranks giữa 2025 và 2026 chỉ khoảng 0.24.

Ví dụ:
- EMA base: median ~+6.61% năm 2025 và +4.91% năm 2026.
- MACD base: ~+7.01% năm 2025, +1.54% năm 2026.
- Trend20 base: ~+6.90% năm 2025, gần flat năm 2026.
- Donchian55 base: +1.78% năm 2025, -1.82% năm 2026.

EMA vẫn là core ổn định nhất; các family khác chỉ là challenger/conditional source, không phải replacement đã được chứng minh.

## Family pruning

- **Giữ:** EMA H1, MACD H1, Trend20 H1, BOS+FVG H1, RSI2 H1 như mean-reversion diagnostic khác bản chất.
- **Bỏ khỏi active V22 search:** Donchian55 vì redundancy với Trend20 và yếu 2026; liquidity sweep vì median âm; BB+RSI V21 vì zero raw signals nên **chưa được kiểm nghiệm**, không phải bị disproven.
- Nhãn ICT/SMC không được coi là evidence. BOS/FVG chỉ được giữ vì mechanical OHLC definition tạo non-zero và partly-positive evidence.

## Quyết định kế tiếp

Xây `SignalIntelligenceLabV1` thay vì mở thêm broad strategy zoo.

Gate kế tiếp phải:
- thay hard quality conjunction bằng soft scores;
- ghi entry-state features ở từng trade;
- implement targeted exhaustion guard mạnh hơn và có telemetry xác minh;
- test adaptive exit chỉ như bounded ablation;
- giữ one run → one ZIP;
- giữ stop-risk <=1.00%;
- giữ toàn bộ execution virtual/tester-only.

REAL-MONEY LIVE TRADING vẫn bị cấm.
