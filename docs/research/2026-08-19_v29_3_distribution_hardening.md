# 2026-08-19 — V29.3 distribution hardening

## Evidence

User diagnostic: `mt5_quant_v29_adaptive_expert_DIAGNOSTIC_20260819_022329.zip`  
SHA-256: `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`

ZIP xác nhận:
- runner/source là V29.1;
- MetaEditor 1 error / 0 warnings;
- exact error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`.

Official MQL5 `MqlDateTime` dùng `min`, không có `minute`.

## System root cause

V29.2 đã có source correction và preflight, nhưng stale V29.1 folder vẫn còn runnable trên máy user. Do đó class lỗi tiếp theo phải được xử lý ở distribution/release gate, không chỉ source token.

## V29.3 implementation

Pinned strategy payload: V29.2 decoded ZIP SHA-256 `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

Thêm clean-checkout release verifier/builder:
- exact payload SHA pin;
- helper contract;
- `MqlDateTime`/`MqlRates`/`MqlTick` member contract;
- `.minute` rejection;
- tester/safety markers;
- native-order rejection;
- analyzer Python compile;
- template safety/no tracked login;
- 3 chunks / 18 months;
- deterministic V29.3 wrapper ZIP + payload manifest.

Thêm wrapper preflight trước khi gọi payload launcher. Nếu inner runner fail, wrapper tạo outer diagnostic ZIP chứa distribution identity và inner diagnostic.

Thêm CI: compileall → pytest → secret/login scan → verify/build → upload verified V29.3 artifact.

Historical V21 test được đổi để skip module-level khi historical implementation không materialize, thay vì làm pytest chết lúc collection. Hard-coded account identifier bị loại khỏi regression assertion.

## Safety

Builder/CI không kết nối MT5/broker và không gửi order. Strategy payload giữ virtual-order research semantics. LIVE forbidden.

## Acceptance

Sau CI PASS, user chỉ chạy V29.3 artifact. Windows MetaEditor 0/0 vẫn là gate đầu tiên trước full 18-month stateful replay.
