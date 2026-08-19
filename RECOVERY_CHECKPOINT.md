# Recovery checkpoint — V29.3 Distribution Hardening

Ngày: 2026-08-19.

REAL-MONEY LIVE TRADING = FORBIDDEN.

Latest user diagnostic SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` là stale V29.1 và fail 1 error / 0 warnings vì `dt.minute`.

Active user-facing distribution: `v29_3_distribution_hardening`.

Pinned V29.2 decoded payload SHA-256:
`d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

V29.3 adds deterministic clean-checkout verification, CI build, payload manifest, stale-kit wrapper preflight và distribution-aware diagnostic packaging. Strategy logic không đổi.

Không chạy trực tiếp V29.0/V29.1/V29.2 folder cũ.

Next: CI artifact PASS → Windows MetaEditor 0/0 → stateful 18-month replay → robustness gates → PAPER/DEMO only. LIVE forbidden.
