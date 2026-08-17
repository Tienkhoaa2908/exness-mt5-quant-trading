# Recovery checkpoint — V24 ML/DL Feature Lake + Regime Router Lab V1

Ngày: 2026-08-17.

REAL-MONEY LIVE TRADING = FORBIDDEN.

## Latest runtime evidence
V22 bundle `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`: 22/22 hashes PASS, MetaEditor 0 errors / 0 warnings, 18 months, external broker orders 0.

## Decision
Trade-level ML/DL benchmark không vượt random enough để promote. Chuyển sang causal M15 feature lake, giữ V23 regime-router trong cùng run để không tăng số lần user phải chạy MT5.

## V24 outputs
Mỗi chunk phải có:
- `monthly_summary.csv`;
- `trades.csv`;
- `bar_features.csv`;
- `manifest.txt`.

Bundle cuối gồm 3 chunks, source, runner, compile log, configs và SHA-256 manifest.

Recovery payload SHA-256: `f842b09075c459646df28150e83a57b65a694d45e4da2fe265ec326b938fa636`.

## Offline research after upload
- build future labels only outside EA;
- train linear/tree/deep sequence models bằng monthly walk-forward;
- no random CV;
- final ML/DL gate phải quay lại MT5 tick-level re-simulation.
