# Phân tích Signal Intelligence Lab V1 (V22)

Ngày: 2026-08-16.

## Integrity và runtime

- ZIP SHA-256: `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`.
- Internal manifest: 22/22 SHA-256 PASS.
- MetaEditor: 0 errors, 0 warnings.
- 18 tháng đầy đủ: 2025-02 đến 2026-07.
- `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`.
- 30 candidates x 4 books, reset độc lập theo tháng.

## Kết quả chính USD40 @ 1%

`ema_h1_base` vẫn là control mạnh nhất:
- median tháng +6.3236%;
- mean +4.8389%;
- 13/18 tháng dương;
- worst -4.5875%; best +14.7376%;
- max MTM DD 9.0171%;
- AvgR trade-ledger khoảng 0.17R.

`ema_h1_score3` gần như trùng hoàn toàn control. `ema_h1_score4` chỉ loại rất ít tín hiệu. Điều này xác nhận score 3/4 không tạo discrimination đủ mạnh vì signal construction ban đầu đã làm phần lớn entry có score cao.

`ema_h1_score3_adaptive`:
- median +6.0098%; mean +5.1881%;
- 12/18 tháng dương;
- worst -3.8154%; best +17.9680%;
- max DD 9.0171%.

Adaptive exit cải thiện mean/tail ở vài tháng nhưng không nâng median robust hơn control.

## Exhaustion V2

Guard V2 lần này thực sự được exercise. Tổng `streak_guard_reject` trên USD40@1%:
- EMA 101;
- MACD 84;
- Trend 170;
- BOS+FVG 92;
- RSI2 99.

Nhưng guard toàn cục làm EMA median giảm từ +6.3236% xuống +5.8129%. Do đó failure mode không phải "mọi third-entry đều xấu".

Sequence reconstruction trên base ledger cho third-entry cùng hướng sau hai lệnh thắng và gap <=4h:
- EMA SHORT: n=46, AvgR khoảng -0.0535R, loss-rate ~52.2%;
- BOS+FVG SHORT: n=20, AvgR khoảng -0.0659R;
- MACD và Trend cùng condition vẫn dương.

Kết luận: chỉ đáng test targeted short-exhaustion cho EMA/BOS-like context; không dùng global cooldown/guard.

## Session pathology của EMA

EMA server-hour 20-23:
- n=49;
- tổng khoảng -12.85R;
- AvgR khoảng -0.262R.

Tách theo năm vẫn âm:
- 2025: n=32, AvgR khoảng -0.075R;
- 2026: n=17, AvgR khoảng -0.614R.

Riêng 22-23 có n=34, tổng khoảng -11.82R, AvgR khoảng -0.348R và âm ở cả 2025/2026.

Đây là candidate family-specific session ablation hợp lý. Không áp dụng cho Trend/BOS vì hai family đó có late-session expectancy dương trong sample.

## Regime shift

Trade-level AvgR của 12 tháng đầu -> 6 tháng cuối:
- EMA: ~0.207R -> ~0.073R;
- MACD: ~0.133R -> ~0.025R;
- Trend: ~0.202R -> ~0.018R;
- BOS+FVG: ~0.177R -> ~0.031R;
- RSI2: ~0.048R -> ~-0.069R.

Do đó vấn đề lớn hơn một indicator filter: edge thay đổi theo regime.

## H1 trend-separation diagnostics

`entry_h1_gap_atr` là khoảng cách directional EMA50-H1 với EMA200-H1, chuẩn hóa bằng ATR M15. Conditional diagnostics trên base trade ledger cho thấy:
- MACD gap >=10: n=154, AvgR ~0.317R; 2025 ~0.308R, 2026 ~0.339R;
- Trend gap >=8: n=212, AvgR ~0.234R; 2025 ~0.242R, 2026 ~0.214R;
- BOS+FVG gap >=8: n=191, AvgR ~0.333R; 2025 ~0.263R, 2026 ~0.509R;
- BOS+FVG gap >=10: n=130, AvgR ~0.373R.

**Cảnh báo:** đây là conditional trade-ledger diagnostics, không phải return của một strategy đã re-simulate. Nếu chặn một entry, thời gian flat thay đổi và các signal sau có thể được nhận khác. Vì vậy gate kế tiếp phải chạy lại Strategy Tester với gate thật.

## Meta-labeling check

Dùng 12 tháng đầu làm train và 6 tháng cuối làm test, Logistic Regression trên entry telemetry cho AUC xấp xỉ:
- EMA 0.469;
- MACD 0.441;
- Trend 0.511;
- BOS+FVG 0.470;
- RSI2 0.482.

Shallow gradient boosting cũng chỉ quanh 0.47-0.52. Không có evidence để promote ML meta-labeling từ feature set hiện tại. Không thêm model phức tạp chỉ để tăng độ phức tạp.

## Quyết định

1. Không promote score3/score4.
2. Không promote global exhaustion guard.
3. Giữ EMA base làm control.
4. Gate kế tiếp test family-specific regime grid + EMA late-session ablation + targeted EMA SHORT third-entry guard.
5. Test selective router một-position-at-time để xem gated orthogonal signals có bổ sung edge mà không tái tạo churn của Opportunity Fusion hay không.
6. Risk ceiling vẫn 1.00%/trade; không Martingale/grid/doubling.
