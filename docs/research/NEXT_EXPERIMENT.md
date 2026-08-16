# NEXT EXPERIMENT — Focused Entry State Lab V2

Multi-Factor Edge Lab V1 đã hoàn tất runtime screening.

Kết luận V21:
- `ema_h1_base` vẫn là research control tốt nhất, median USD40@1% +6.3236%/tháng;
- quality boolean gate giảm turnover/DD nhưng lọc quá tay và làm mất expectancy;
- `quality_streak` chưa phải test hợp lệ vì `streak_guard_reject=0` toàn bộ sample;
- BB+RSI branch có 0 raw signals và cần component diagnostics;
- MACD/Trend có alpha nhưng không vượt EMA control và decay mạnh trong 2026;
- liquidity sweep standalone bị demote; BOS+FVG chỉ giữ exploratory.

Gate kế tiếp: `Focused Entry State Lab V2`.

## Mục tiêu

Không mở rộng strategy zoo. Tập trung sửa entry discrimination của những family đã có evidence.

Một lần chạy phải gom các ablation sau trên cùng tick stream:
1. EMA, MACD, Trend20 và BOS+FVG làm core families; BB+RSI chạy diagnostic ladder riêng trong cùng batch.
2. Sửa two-win -> third-entry streak state machine đúng hypothesis đã pre-register.
3. Tách LONG/SHORT exhaustion, đặc biệt EMA SHORT.
4. Score-based entry thay boolean all-or-nothing quality gate.
5. Component counters cho ADX, DI, ATR regime, candle body, close location, distance/chase, H1 alignment, session bucket và prior-trade state.
6. Threshold ladder hữu hạn, đóng trước khi chạy; không optimizer mở vô hạn.
7. Frozen exit: 2 ATR initial stop, peak-lock 50% sau +1R, TP4R.
8. 4 capital/risk books như V21; stop-risk research ceiling 1.00%.
9. 18 independent monthly resets, bounded 3 x six-month chunks, one-click và đúng một output ZIP.
10. Promotion phải dựa trên median/positive months/worst month/max MTM DD/turnover + 2025/2026 stability, không chỉ peak return.

Finalist từ virtual screening vẫn phải quay lại native MT5 và real-tick fidelity gate khi coverage phù hợp.

REAL-MONEY LIVE TRADING = FORBIDDEN.
