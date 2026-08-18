# ML Regime Replay Lab V1 — workflow

## Hypothesis

Directional ML trên V24.2 vẫn gần random, trong khi LightGBM dự báo future 16-bar range/ATR có Spearman OOS dương ở 12/12 monthly folds. Vì vậy ML chỉ làm regime router / abstention layer; direction vẫn do mechanical signal family xác định.

## Frozen score construction

- Source: V24.2 causal `bar_features.csv`.
- Target: `max(high[t+1:t+16]) - min(low[t+1:t+16])`, chia ATR14 tại t.
- Model: LightGBM regressor.
- Walk-forward: từng tháng Aug-2025 → Jul-2026.
- Purge: 32 M15 bars trước test month.
- Score: prediction percentile relative to predictions on that fold's training sample.
- EA chỉ đọc frozen OOF score; không tạo future labels và không train model trong tester.

Frozen score SHA-256: `5d8a6cc45074833a60d7e82b6a56f7ae72a9f4e0153b623cc439756751b16c91`.
Fold manifest SHA-256: `ed26b87484e1c4782614c64294520bc7fb3e6728c10f08fa77c8fe2d097739a7`.

## Catalog

3 controls + 9 ML candidates, 4 virtual books each. ML variants either suppress EMA in predicted high-range state or switch/add BOS/Trend/Donchian/Liquidity families there. Only one virtual position/book is permitted.

## Decision rule

Ưu tiên robust monthly distribution, positive-month count, AvgR, max MTM DD và turnover. Control parity phải đúng trước khi diễn giải ML variants.

V25 chỉ là screening vì routing catalog được informed bởi V24.2 diagnostics. Không promote trực tiếp sang PAPER/DEMO. REAL-MONEY LIVE TRADING remains forbidden.
