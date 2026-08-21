# Windows MT5 / Exness — setup nghiên cứu hiện tại

- MT5 + MetaEditor đã hoạt động.
- Broker: Exness Technologies Ltd.
- Symbol account: `XAUUSDm`.
- Main timeframe: M15.
- Strategy Tester fidelity gate đã dùng `Every tick based on real ticks` khi exact-MT5 evidence cần thiết.
- REAL-MONEY LIVE TRADING = FORBIDDEN.

## Current V39 workflow

V39 Stage A là offline/read-only và **không mở MT5/MetaEditor**. Nó dùng accepted V38 exact-MT5 telemetry và accepted/recomputed V36 offline Transformer predictions.

1. Mở Git Bash.
2. Fetch và reset về branch V39 release được chỉ định trong handover.
3. Chạy `runtime/v39_selective_harvest/BOOTSTRAP_V39_SELECTIVE_HARVEST_ONE_SHOT_GIT_BASH.sh` hoặc direct Stage-A runner.
4. Runner bắt buộc chạy Python compile, V39 pytest/static tests, repository secret scan và Bash syntax gate.
5. Runner verify accepted V38 ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b` nếu phải recover từ ZIP.
6. V39 chỉ phân tích control path; không gửi order và không thay đổi risk.
7. Runner tạo `V39_EVIDENCE.txt`, `bundle_manifest_sha256.txt` và một ZIP duy nhất `v39_selective_harvest_stage_a.zip`.
8. Upload duy nhất ZIP đó.

Nếu cần đóng gói lại một output folder chuẩn, double-click `scripts/package_mt5_research.cmd`. Có thể verify ZIP bằng `scripts/analyze_mt5_research_bundle.py`.

## Exact MT5 future gate

Chỉ nếu V39 Stage A đủ ổn định mới xây Stage B. Stage B phải frozen trước khi exact-MT5 replay, giữ entry/router và initial risk unchanged, action chỉ sau khoảng +1R, và phải kiểm tra lại data/tick coverage mỗi run.

Không chuyển sang live/manual order để test lỗi. Stop-risk research ceiling giữ <=1.00%.
