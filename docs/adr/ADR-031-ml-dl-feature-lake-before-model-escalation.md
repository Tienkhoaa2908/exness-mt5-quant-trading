# ADR-031 — Xây feature lake theo bar trước khi đẩy mạnh ML/DL

## Trạng thái

Accepted for research — 2026-08-17.

## Bối cảnh

Signal Intelligence V22 đã có telemetry ở mức trade entry, nhưng năm base family chỉ tạo khoảng 3.3k trade events trong 18 tháng. Benchmark theo thời gian 2025 → 2026 trên tập này cho thấy model phức tạp hơn chưa tạo information gain ổn định:

- Logistic Regression AUC ~0.495;
- XGBoost ~0.497;
- LightGBM ~0.493;
- CatBoost ~0.504;
- MLP ~0.492;
- GRU ~0.474;
- TCN ~0.478;
- tiny Transformer ~0.500.

Đây là bằng chứng rằng tăng model capacity trên sparse trade-level snapshot chưa giải quyết được regime drift. Không được diễn giải là ML/DL vô dụng; dataset hiện tại chưa đủ giàu về temporal state.

## Nguồn nghiên cứu

- Lim, Zohren, Roberts (2019), *Enhancing Time Series Momentum Strategies Using Deep Neural Networks*, arXiv:1904.04912 / Journal of Financial Data Science. Reference cho sequence learning, direct performance objective và turnover regularization; không copy code/parameter.
- Bai, Kolter, Koltun (2018), *An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling*, arXiv:1803.01271. Reference cho TCN như baseline sequence model bên cạnh GRU/LSTM.
- Nie et al. (ICLR 2023), *A Time Series is Worth 64 Words: Long-term Forecasting with Transformers*, arXiv:2211.14730. Reference cho patch-based Transformer và representation pretraining; không coi forecasting SOTA là bằng chứng trading edge.

## Quyết định

V24 `ML/DL Feature Lake + Regime Router Lab V1` chạy một lần trên MT5 và làm hai việc đồng thời:

1. giữ toàn bộ 26 V23 regime-router candidates × 4 books để không mất gate regime hiện tại;
2. xuất **một dòng causal feature cho mỗi M15 bar** để tạo dataset sequence đủ lớn cho nghiên cứu ML/DL offline mà không phải chạy MT5 lại cho từng model.

Feature lake gồm:
- OHLCV/spread;
- lagged returns 1/2/4/8/16/32;
- realized volatility 8/32;
- candle geometry;
- ATR14/ATR50;
- EMA 10/20/50/200/300 distances;
- RSI2/RSI14;
- MACD;
- ADX/+DI/-DI;
- Bollinger position/width;
- H1 EMA50/EMA200 structure;
- Donchian 20/55 position;
- session/day-of-week;
- raw direction của EMA, Trend20, RSI2, MACD, Donchian55, BB+RSI, liquidity sweep, BOS+FVG.

EA **không ghi future label**. Future returns/MFE/MAE labels chỉ được tạo offline sau khi bundle đóng, tránh accidental feature leakage trong MQL.

## ML/DL tournament pre-register

Sau khi user upload một V24 ZIP, cùng dataset được dùng nhiều lần offline:

- Logistic Regression baseline;
- HistGradientBoosting;
- ExtraTrees;
- MLP;
- GRU;
- TCN;
- patch Transformer;
- ensemble chỉ khi OOS components có information gain độc lập.

Validation:
- chronological walk-forward;
- 6 tháng warm-up;
- test từng tháng kế tiếp;
- purge tối thiểu 32 M15 bars quanh boundary;
- không random K-fold;
- thresholds/gates chỉ là discovery cho đến khi được đưa trở lại MT5 tick-level re-simulation.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. V24 chỉ Strategy Tester/virtual books/data export. Không `OrderSend`, không `CTrade`, không Martingale/grid/doubling. Research stop-risk ceiling vẫn 1.00%/trade.
