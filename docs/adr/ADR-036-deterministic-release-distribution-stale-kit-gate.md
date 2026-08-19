# ADR-036 — Deterministic release distribution và stale-kit gate

Ngày: 2026-08-19  
Trạng thái: ACCEPTED

## Bối cảnh

V29.0 và V29.1 đã làm user mất nhiều vòng chạy vì lỗi có thể bắt trước Windows runtime. Diagnostic mới nhất SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` xác nhận user vẫn chạy stale V29.1 sau khi V29.2 đã tồn tại.

Lỗi trực tiếp V29.1 là `MqlDateTime.minute`; MQL5 chính thức dùng `min`. V29.2 đã sửa source và có source preflight, nhưng distribution layer chưa ngăn user nhầm folder cũ.

## Quyết định

Từ V29.3, release user-facing được build deterministic từ **pinned V29.2 payload** có decoded ZIP SHA-256:

`d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`

CI trên clean checkout phải:
1. decode đúng recovery payload;
2. verify exact payload SHA;
3. verify MQL helper definitions;
4. verify field contracts `MqlDateTime`, `MqlRates`, `MqlTick`;
5. reject `.minute`/native execution paths;
6. verify tester/safety markers;
7. compile-check Python analyzer;
8. verify template safety + 3 chunks / 18 months;
9. chạy pytest + secret/login scan;
10. chỉ khi tất cả PASS mới build và upload V29.3 one-click artifact.

V29.3 wrapper thêm:
- distribution release identity;
- hash manifest cho toàn payload;
- preflight lại payload trước khi gọi V29.2 launcher;
- outer diagnostic wrapper ghi distribution identity nếu inner run fail.

User không chạy trực tiếp V29.0/V29.1/V29.2 folder cũ nữa; chỉ chạy artifact V29.3 do CI build.

## Hệ quả

- Không đổi strategy/risk/exit/adaptive logic.
- Không gọi broker/order trong CI hoặc builder.
- Static/CI PASS vẫn **không** phải Windows compile evidence.
- MetaEditor 0 errors / 0 warnings vẫn là runtime acceptance gate đầu tiên.
- REAL-MONEY LIVE TRADING vẫn bị cấm.
