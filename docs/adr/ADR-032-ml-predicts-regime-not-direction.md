# ADR-032 — ML dự báo regime, không trực tiếp đoán hướng

## Trạng thái
Accepted for research screening — 2026-08-17.

## Bối cảnh
V24.2 bar-feature lake cho thấy generic direction models chỉ quanh random OOS, kể cả boosting và sequence DL. Ngược lại future-range / volatility regression có rank correlation ổn định qua monthly walk-forward.

## Quyết định
1. Không dùng ML/DL như direct Buy/Sell oracle.
2. Frozen mechanical signal families quyết định direction.
3. ML chỉ route/abstain theo predicted future range regime.
4. V25 replays OOF scores tick-by-tick trong MT5 để xử lý đúng opportunity exclusion, position occupancy, churn và exit path.
5. Risk ceiling vẫn 1.00%/trade; LIVE bị cấm.

## Validation
Một V25 winner chỉ là provisional. Cần untouched forward/native MT5 parity và cost/fidelity stress trước PAPER/DEMO.
