# ADR-039 — Selective-harvest Stage A trước exact MT5

Ngày: 2026-08-21

## Trạng thái

Accepted for research workflow.

## Bối cảnh

V38 exact-MT5 cho thấy các fast exit vô điều kiện đều không đạt promotion rule. TP +1R là arm gần control nhất nhưng cắt mất right-tail trong các tháng trend mạnh. Vì vậy tiếp tục sweep TP cố định trên cùng sample sẽ tăng data-snooping mà không giải quyết đúng bài toán.

## Quyết định

Trước bất kỳ exact-MT5 intervention nào, V39 phải chạy một Stage A offline/read-only trên accepted V38 control path.

Stage A dùng hai nguồn tín hiệu tách biệt:

- M1/tick-path causal proxies từ V38 để ước lượng giveback risk và tail continuation;
- accepted V36 Transformer OOS `p_hold` làm external tail-preservation veto, không retrain V36 trên chính OOS predictions.

Decision zone chỉ bắt đầu khi unrealized R >= +1.0R. Threshold của M1 score được lấy từ trailing calibration window, không tune trên test month. Mỗi trade chỉ ghi first trigger.

`STAGE_A_PASS` chỉ có nghĩa là tín hiệu đủ ổn định để thiết kế Stage B. Nó không phải PnL evidence, không cho phép PAPER/DEMO và không được diễn giải thành profitable/winner.

## Promotion sang Stage B

Chỉ xem xét Stage B nếu Stage A có tối thiểu 4 chronological folds, trigger coverage hữu ích nhưng bounded, avoided giveback dương và ổn định, đồng thời false-harvest của right-tail winners nằm trong giới hạn preregistered.

Stage B phải dùng frozen causal policy trong exact MT5. Early exit làm thay đổi re-entry/state/path nên không được replay một baseline trade-key decision tape như thể economics không đổi.

## Packaging/recovery

Workflow chuẩn là một run -> một ZIP. ZIP phải có `bundle_manifest_sha256.txt`, evidence file, inputs/outputs cần thiết và phải qua CRC + SHA verification. `scripts/package_mt5_research.cmd` là entry point chuẩn cho packaging thủ công sau các run quan trọng.

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Stage A không launch MT5/MetaEditor và không có native/external order path.
- Stop-risk ceiling giữ <=1.00%/trade.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Không tăng risk hoặc sweep threshold chỉ để ép mục tiêu 15% geometric/tháng.
