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
2. Fetch branch bằng explicit refspec để tương thích cả repo local có remote fetch config hạn chế:
   `git fetch --no-tags origin "+refs/heads/agent/v39-selective-harvest:refs/remotes/origin/agent/v39-selective-harvest"`.
3. Materialize/reset local branch bằng:
   `git checkout -B agent/v39-selective-harvest refs/remotes/origin/agent/v39-selective-harvest`.
4. Chạy `runtime/v39_selective_harvest/BOOTSTRAP_V39_SELECTIVE_HARVEST_ONE_SHOT_GIT_BASH.sh` hoặc direct Stage-A runner.
5. Runner bắt buộc chạy Python compile, V39 static tests, repository secret scan và Bash syntax gate. Nếu selected Python có `pytest`, runner dùng pytest; nếu không có, runner chạy trực tiếp `tests/test_v39_selective_harvest_static.py`, dùng dependency-free fallback đã tích hợp. Không cần cài pytest và không được bỏ qua test gate.
6. Runner verify accepted V38 ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b` nếu phải recover từ ZIP.
7. Nếu accepted V36 predictions chưa có, V36 offline runner reuse `.venv` hiện hữu và probe đầy đủ `numpy,pandas,torch,sklearn,scipy`. Nếu thiếu sklearn stack, runner repair bằng `scikit-learn==1.8.0`; package đã cài như `torch==2.7.1` được giữ lại, không xóa venv. Sau repair runner in exact versions rồi mới train.
8. V39 chỉ phân tích control path; không gửi order và không thay đổi risk.
9. Runner tạo `V39_EVIDENCE.txt`, `bundle_manifest_sha256.txt` và một ZIP duy nhất `v39_selective_harvest_stage_a.zip`.
10. Upload duy nhất ZIP đó.

Không dùng `git clean` trong recovery vì accepted V36/V38 runtime evidence có thể là untracked local data cần được giữ lại.

Nếu cần đóng gói lại một output folder chuẩn, double-click `scripts/package_mt5_research.cmd`. Có thể verify ZIP bằng `scripts/analyze_mt5_research_bundle.py`.

## Exact MT5 future gate

Chỉ nếu V39 Stage A đủ ổn định mới xây Stage B. Stage B phải frozen trước khi exact-MT5 replay, giữ entry/router và initial risk unchanged, action chỉ sau khoảng +1R, và phải kiểm tra lại data/tick coverage mỗi run.

Không chuyển sang live/manual order để test lỗi. Stop-risk research ceiling giữ <=1.00%.
