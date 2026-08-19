# V30 — chạy Chunk 2 + Chunk 3 bằng Git Bash

Mục đích: bỏ PowerShell orchestration. Script Bash chỉ compile EA, chạy hai Strategy Tester chunk còn thiếu, đọc locator do EA tạo, copy output/state, rồi ZIP. Không trim/validate dataset trên Windows.

## Trước khi chạy

1. Đóng MetaTrader 5 hoàn toàn.
2. Không xóa `%APPDATA%\MetaQuotes\Terminal\Common\Files`.
3. State Chunk 1 đã nằm trong repo và có hash check.
4. EA được reconstruct từ các base64 text parts trong repo và bắt buộc khớp SHA-256 trước compile.
5. REAL-MONEY LIVE TRADING = FORBIDDEN. EA/tester không có native order path.

## Chạy bằng Git Bash

Clone hoặc update branch `agent/v30-ml-dl-feature-lake`, sau đó chạy:

```bash
cd runtime/v30_gitbash_chunks2_3
bash ./RUN_V30_CHUNKS_2_3_GIT_BASH.sh
```

## Script sẽ tự làm

- tìm đúng MT5 data folder qua `origin/origin.txt`;
- reconstruct exact `MlDlFeatureLakeV1.mq5` từ source parts và verify SHA-256;
- copy EA vào `MQL5/Experts/mt5_quant`;
- MetaEditor compile và bắt buộc `0 errors / 0 warnings`;
- reset chain về state Chunk 1 đã được kiểm chứng;
- chạy Chunk 2: `2025.08.01 -> 2026.02.01`;
- lấy `run_folder` từ `ML_DL_FEATURE_LAKE_LATEST.txt`;
- copy `bar_features.csv`, `monthly_summary.csv`, `trades.csv`, `manifest.txt` và state sau Chunk 2;
- chạy Chunk 3: `2026.02.01 -> 2026.08.01`;
- copy cùng bộ file + state cuối;
- tạo một ZIP duy nhất trong `OUTPUT_GIT_BASH`.

Không có PowerShell. Không chạy lại Chunk 1.

## Nếu lỗi sau khi Chunk 2 đã xong

Không xóa folder `OUTPUT_GIT_BASH`. Chạy lại cùng lệnh Bash. Nếu checkpoint Chunk 2 đầy đủ, script sẽ in:

```text
REUSE CHECKPOINT chunk2_2025_08__2026_02 -- MT5 NOT RERUN
```

và đi thẳng sang Chunk 3/packaging.

## Khi hoàn thành

Cuối màn hình sẽ hiện:

```text
UPLOAD THIS ONE ZIP:
C:\...\OUTPUT_GIT_BASH\mt5_quant_v30_chunks2_3_GIT_BASH_....zip
SHA256=...
```

Upload đúng ZIP đó. Sau đó không cần chạy MT5 cho từng ML/DL model; labeling/training/walk-forward chạy offline.
