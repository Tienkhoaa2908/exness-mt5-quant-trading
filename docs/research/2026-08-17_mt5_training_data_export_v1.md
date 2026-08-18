# MT5 Training Data Export V1 — 2026-08-17

## Decision

User approved deeper ML/DL research and explicitly allowed exporting more data from the connected MT5 terminal for offline model training.

Create a separate DATA-ONLY exporter before the next strategy lab. It must not send orders or export credentials/account history.

## Export scope

Target: `XAUUSDm`.

Historical target bars requested from 2022-01-01 where terminal/server coverage permits:
- M1, M5, M15, M30, H1, H4, D1.

Cross-market context is auto-resolved from available MT5 symbols and exported when present:
- XAGUSD;
- EURUSD;
- GBPUSD;
- USDJPY;
- US500/SPX500;
- USTEC/NAS100;
- US30;
- USOIL/WTI;
- BTCUSD.

Raw target ticks are requested from 2026-06-01 in daily chunks. Empty/unavailable ranges are not fabricated; `coverage.csv` records actual first/last timestamps and row counts.

## Leakage discipline

`2026-08-01T00:00:00Z` is the frozen boundary:
- pre-boundary data -> `train_pre_holdout`;
- Aug-2026 onward -> `forward_holdout`.

Forward holdout is not to be used for training before model/routing rules are frozen.

## Planned research after upload

- cross-asset and multi-timeframe feature ablations;
- LightGBM/XGBoost/CatBoost regime models;
- GRU/TCN/patch-Transformer sequence models;
- multi-horizon return/range/volatility targets;
- raw-tick microstructure aggregation where real broker tick history exists;
- MT5 replay of any model/router finalist.

## Optional forward recorder

A second BAT records live forward ticks plus DOM snapshots when the broker exposes Market Depth. This data is fidelity/forward evidence by default, not automatically a training sample.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN.

No `order_send`, `OrderSend`, `CTrade`, Martingale/grid/doubling. No password/token/account-number/order-history export.

## Local release evidence

One-click kit: `mt5_quant_training_data_exporter_v1_one_click.zip`

SHA-256: `1380d8af0984d1a4820fd70482e04d54f3d4fa60b8413860f4f73e589c5cf924`

Local static QA:
- Python `py_compile` PASS;
- pytest 4/4 PASS;
- executable source order-path scan PASS;
- internal kit manifest 8/8 PASS;
- ZIP integrity PASS.

Windows runtime/export is not claimed until user runs the BAT and uploads the resulting data ZIP.