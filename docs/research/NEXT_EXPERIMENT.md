# NEXT EXPERIMENT — V29.3 Compile + Stateful Replay Gate

Không chạy folder V29.0/V29.1/V29.2 cũ.

1. Dùng **verified CI artifact** `v29_3_distribution_hardening`.
2. Giải nén vào fresh folder.
3. Double-click root `RUN_ADAPTIVE_EXPERT_LAB_V1.cmd`.
4. V29.3 wrapper verify payload manifest + stale-source marker trước khi gọi V29.2 runner.
5. MetaEditor phải 0 errors / 0 warnings.
6. Chỉ khi compile PASS mới chạy 3 × 6-month stateful replay, Feb-2025 → Jul-2026.
7. Một run → một ZIP.

Decision không dựa mean return đơn lẻ; cần positive-month breadth, worst month, MTM DD, AvgR, turnover, source mix và stress/parity gates.

REAL-MONEY LIVE TRADING vẫn cấm.
