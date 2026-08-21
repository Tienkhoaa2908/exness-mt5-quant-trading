# Exness / MetaTrader 5 Quant Trading System

**REAL-MONEY LIVE TRADING = FORBIDDEN.**

Kho nghiên cứu quant cho MT5/Exness. Không Martingale, uncontrolled grid hoặc doubling after loss.

## Active milestone — V39 Selective Harvest Stage A

V38 exact-MT5 đã PASS integrity và control reproduction. Không có fast-exit arm vô điều kiện nào đạt promotion rule. Accepted baseline `adaptive_ewma_hl8_thr0` vẫn là control; +1R là decision zone, không phải universal TP.

Accepted V38 ZIP SHA-256:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Primary 12-month control: USD107.43 end, 8.58% geometric/tháng, max DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501.

V39 Stage A là offline/read-only diagnostic. Nó ghép V38 M1/tick-path causal proxies với accepted V36 Transformer tail-veto để chọn `HARVEST_NOW` versus `KEEP_BASELINE_EXIT` sau khoảng +1R. Stage A không launch MT5/MetaEditor, không gửi order và không phải PnL evidence.

Chỉ nếu Stage A ổn định mới thiết kế frozen Stage B policy rồi đưa lại vào exact MT5. Mục tiêu 15% geometric/tháng chỉ là aspirational target; không tăng stop-risk >1.00% hoặc tune threshold để ép target.

## One run -> one ZIP

Sau run quan trọng dùng ZIP mà runner in ra hoặc `scripts/package_mt5_research.cmd`. Bundle chuẩn phải có `bundle_manifest_sha256.txt`; kiểm tra bằng `scripts/analyze_mt5_research_bundle.py`.

## Recovery

Đọc `docs/handover/CURRENT_STATE.md`, `docs/handover/RECOVERY_PROMPT.md`, `docs/research/v38_fast_harvest_results.md`, `docs/research/v39_selective_harvest_plan.md` và ADR-039.
