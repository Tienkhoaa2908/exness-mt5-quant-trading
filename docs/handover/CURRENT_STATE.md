# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-17.

## Safety invariant

REAL-MONEY LIVE TRADING = FORBIDDEN.

Không Martingale, uncontrolled grid, doubling after loss. Stop-risk research ceiling 1.00%/trade. Virtual lab/ML prediction không được deploy trực tiếp.

## Evidence gần nhất

ZIP user vừa upload SHA-256 `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03` là **V22 Signal Intelligence output**, không phải V23:
- internal SHA-256 22/22 PASS;
- MetaEditor 0 errors / 0 warnings;
- 18 months;
- tester-only, external broker orders = 0.

V22 control `ema_h1_base` USD40@1% vẫn khoảng median +6.32%/tháng; chưa có robust evidence cho aim 15–20%/tháng.

## ML/DL benchmark trên trade-level telemetry

Pooled base-family entries, train 2025 → test 2026:
- Logistic AUC ~0.495;
- XGBoost ~0.497;
- LightGBM ~0.493;
- CatBoost ~0.504;
- MLP ~0.492;
- GRU ~0.474;
- TCN ~0.478;
- tiny Transformer ~0.500.

Kết luận: không tăng model capacity trên sparse trade-event data. Cần temporal feature lake ở mức bar.

## Gate hiện tại — V24 ML/DL Feature Lake + Regime Router Lab V1

Một lần run:
- giữ toàn bộ V23 26 candidates × 4 books = 104 virtual books;
- 18 monthly resets / 3 six-month chunks;
- xuất `bar_features.csv` ở từng M15 bar;
- raw signal coverage gồm EMA/Trend/RSI2/MACD/Donchian/BB-RSI/liquidity sweep/BOS-FVG;
- không ghi future labels trong EA;
- một ZIP output.

Sau upload, offline tournament:
Logistic / HistGradientBoosting / ExtraTrees / MLP / GRU / TCN / PatchTransformer / bounded ensemble.

Validation bắt buộc: 6-month warmup, chronological monthly walk-forward, 32-bar purge, không random CV. ML gate nào được chọn vẫn phải quay lại tick-level MT5 re-simulation trước promotion.

## Evidence status V24

Chỉ static QA trước Windows run. Không claim MetaEditor/runtime PASS cho V24 cho đến khi user chạy kit.
