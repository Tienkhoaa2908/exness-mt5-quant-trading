# Exness / MetaTrader 5 Quant Trading System

**REAL-MONEY LIVE TRADING = FORBIDDEN.**

Kho nghiên cứu quant MT5/Exness. Không Martingale, uncontrolled grid, doubling after loss; không bỏ tester/live guards; không commit password/token/secret/login.

## Active milestone — V29.3 distribution hardening

Mục tiêu hiện tại là loại bỏ class lỗi compile/release vặt trước khi user phải chạy Windows.

Audit đã xác minh historical `recovery/v29_adaptive_expert_lab_one_click.zip.b64` vẫn là V29.0 blob và bị CRC/truncation; các V29.1/V29.2 release SHA cũ không còn được dùng làm canonical source-of-truth.

Fresh V29.3 candidate được reconstructed từ chính Windows V29.1 diagnostic source/runner. Strategy source chỉ đổi `dt.minute -> dt.min`; runner thêm pre-MetaEditor helper/member/safety/native-order preflight.

Candidate ZIP SHA-256:
`a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`

Local QA: pytest 6/6 PASS, ZIP + internal manifest PASS, secret/login scan PASS, no native-order tokens. Đây chưa phải Windows compile evidence và GitHub CI vẫn fail-closed cho tới khi canonical artifact materialization hoàn tất.

Windows gate kế tiếp: MetaEditor **0 errors / 0 warnings**. Chỉ sau đó mới full 18-month stateful replay.

Xem `docs/handover/CURRENT_STATE.md`, `docs/research/2026-08-19_v29_3_distribution_hardening.md` và `docs/research/NEXT_EXPERIMENT.md`.
