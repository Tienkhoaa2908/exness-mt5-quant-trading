# ADR-030 — Family-specific regime routing trước ML phức tạp

## Trạng thái

Accepted for research, 2026-08-16.

## Bối cảnh

Signal Intelligence V22 xác nhận hai điều:
1. soft score chung gần như không discriminate được EMA/Trend/BOS vì đa số signal đã có score cao;
2. train-12/test-6 meta-labeling bằng Logistic Regression và shallow gradient boosting có AUC gần 0.5, không có bằng chứng generalization.

Trong khi đó, edge của MACD/Trend/BOS thay đổi mạnh giữa 2025 và 2026 và conditional diagnostics cho thấy directional H1 EMA50-EMA200 separation có quan hệ mạnh hơn với expectancy của các family breakout/momentum. EMA lại có pathology riêng ở server-hour 20-23.

Một latent-regime model phức tạp ở bước này sẽ tăng degrees of freedom và multiple-testing risk. Vì vậy gate kế tiếp dùng observable rule-based regime proxy trước.

## Quyết định

V23 Regime Router Lab V1:
- EMA: control, adaptive, skip hour 20, skip hour 22, targeted SHORT third-entry rearm 0.5/1.0 ATR trong 16 M15 bars;
- MACD: H1-gap 0/8/10;
- Trend20: H1-gap 0/3/5/8;
- BOS+FVG: H1-gap 0/4/8/10;
- selective routers: EMA + từng gated family, loose/balanced/strict, adaptive và targeted-exhaustion ablations.

Tất cả chạy chung một tick stream, 26 candidates x 4 books = 104 virtual books, 18 monthly resets, 3 six-month chunks, một ZIP output.

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Virtual orders only; không `OrderSend`, không `CTrade`.
- Stop-risk research ceiling 1.00%/trade.
- Không Martingale, uncontrolled grid, doubling after loss.
- Router chỉ giữ một virtual position/book; không stacked XAU risk.

## Promotion gate

Không promote dựa trên conditional ledger. Candidate phải:
- beat EMA control về robust monthly profile, không chỉ best month;
- giữ max MTM DD hợp lý;
- không tăng turnover/churn mất kiểm soát;
- không chỉ thắng ở một năm;
- nếu là virtual finalist thì phải quay lại native MT5 parity trước PAPER/DEMO.
