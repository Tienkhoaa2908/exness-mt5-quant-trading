# NEXT EXPERIMENT — V29.3 Compile + Stateful Replay Gate

Không chạy/reuse folder V29.0/V29.1/V29.2 cũ.

## Gate 1 — Windows compile

1. Dùng fresh candidate ZIP SHA-256 `a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`.
2. Giải nén vào folder hoàn toàn mới.
3. Double-click root `RUN_ADAPTIVE_EXPERT_LAB_V1.cmd`.
4. Runner phải báo `SOURCE PREFLIGHT PASS` trước MetaEditor.
5. MetaEditor phải **0 errors / 0 warnings**.
6. Nếu compile fail, upload duy nhất diagnostic ZIP mới; không sửa tay source trên máy Windows.

## Gate 2 — stateful replay

Chỉ khi Gate 1 PASS mới chạy 3 × 6-month stateful replay, Feb-2025 → Jul-2026. Một run → một ZIP.

Decision không dựa mean return đơn lẻ; cần positive-month breadth, worst month, MTM DD, AvgR, turnover, source mix và stress/parity gates.

GitHub CI hiện vẫn fail-closed vì historical recovery payload không đủ integrity để làm canonical release source. Không diễn giải CI đỏ này thành strategy failure.

REAL-MONEY LIVE TRADING vẫn cấm.
