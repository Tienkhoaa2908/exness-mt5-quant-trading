# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit secret.
- Không gọi `order_send`/native broker order để test.

## Latest verified runtime
V22 Signal Intelligence bundle SHA-256 `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`, integrity 22/22 PASS, MetaEditor 0/0, 18 months, external orders 0.

ZIP gần nhất user upload lại chính là V22, không phải V23.

## Current gate
V24 `ML/DL Feature Lake + Regime Router Lab V1`.

Một MT5 run thu cả V23 regime-router results và bar-level causal feature lake. Sau đó nghiên cứu ML/DL chạy offline nhiều vòng từ một ZIP duy nhất.

Model catalog pre-register: Logistic, HistGradientBoosting, ExtraTrees, MLP, GRU, TCN, PatchTransformer; ensemble chỉ sau OOS evidence.

Validation: chronological walk-forward; 6-month warmup; test monthly; purge 32 M15 bars; không random split; conditional offline diagnostics không được gọi là tick-level backtest.
