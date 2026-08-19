# Exness / MetaTrader 5 Quant Trading System

**REAL-MONEY LIVE TRADING = FORBIDDEN.**

Kho nghiên cứu quant MT5/Exness. Không Martingale, uncontrolled grid, doubling after loss; không bỏ tester/live guards; không commit password/token/secret/login.

## Active milestone

User-facing release: **v29_3_distribution_hardening**.

V29.3 không thay đổi strategy. Nó harden distribution để user không còn chạy nhầm stale V29.0/V29.1/V29.2 folder.

CI verify pinned V29.2 payload SHA-256 `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`, chạy static/safety/tests, rồi mới build và upload một V29.3 one-click artifact.

Windows gate kế tiếp vẫn là MetaEditor **0 errors / 0 warnings**, sau đó mới full 18-month stateful replay.

Xem `docs/handover/CURRENT_STATE.md` và `docs/research/NEXT_EXPERIMENT.md`.
