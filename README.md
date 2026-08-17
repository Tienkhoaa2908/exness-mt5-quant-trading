# Exness / MetaTrader 5 Quant Trading — V24 ML/DL Feature Lake

Kho nghiên cứu hệ thống quant MT5/Exness.

**REAL-MONEY LIVE TRADING = FORBIDDEN.** Chỉ offline analysis, MT5 Strategy Tester và PAPER/DEMO sau safety gates. Không Martingale, uncontrolled grid, doubling after loss, không bỏ tester/live guards, không commit password/token/secret.

## Trạng thái

- V22 Signal Intelligence runtime đã PASS nhưng trade-level ML/DL không có information gain ổn định trên 2026.
- V23 Regime Router chưa có runtime bundle mới từ user; ZIP gần nhất vẫn là V22.
- V24 gom V23 regime-router và causal M15 feature-lake export trong **một run**.
- Sau V24, nhiều vòng ML/DL được chạy offline từ cùng ZIP; user không cần chạy MT5 lại cho từng model.

Chạy `RUN_ML_DL_FEATURE_LAKE_LAB_V1.cmd`, sau đó upload một ZIP duy nhất được tạo trên Desktop.
