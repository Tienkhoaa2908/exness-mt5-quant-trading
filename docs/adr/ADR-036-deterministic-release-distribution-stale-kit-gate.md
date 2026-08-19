# ADR-036 — Deterministic release distribution và stale-kit gate

Ngày: 2026-08-19  
Trạng thái: ACCEPTED — amended after recovery-integrity audit

## Bối cảnh

V29.0 và V29.1 đã làm user mất nhiều vòng chạy vì lỗi có thể bắt trước Windows runtime. Diagnostic SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` xác nhận V29.1 source/runner thực tế và MetaEditor 1 error / 0 warnings do `MqlDateTime.minute`; MQL5 dùng `min`.

Audit sau đó phát hiện vấn đề lớn hơn ở release governance:
- `recovery/v29_adaptive_expert_lab_one_click.zip.b64` vẫn là blob V29.0 historical payload;
- V29.1/V29.2 chỉ cập nhật patch/docs/local release claims, không commit một canonical payload mới;
- historical recovery archive có CRC corruption/truncation;
- vì vậy các SHA V29.1/V29.2 đã ghi trước đây không đủ tư cách làm GitHub-reproducible source-of-truth.

## Quyết định

1. Historical V29 recovery B64 bị hạ xuống **migration/historical evidence only**. Không được dùng trực tiếp để phát hành.
2. Mọi user-facing release mới phải được dựng từ một source snapshot có provenance rõ, có strategy-source SHA, runner SHA, ZIP SHA và internal manifest.
3. Release gate phải fail-closed nếu source/artifact không materialize hoặc integrity không đạt.
4. Stale V29.0/V29.1/V29.2 folder không được reuse.
5. Trước MetaEditor phải chạy source preflight cho:
   - required helper definitions;
   - `MqlDateTime`, `MqlRates`, `MqlTick` member contracts;
   - catalog counts;
   - tester/safety markers;
   - forbidden native-order tokens.
6. Clean-checkout CI phải chạy Python compile, pytest, secret/tracked-login scan và artifact integrity checks. Không whitelist để ép CI xanh khi release materialization chưa sạch.
7. Static/CI PASS không được diễn giải thành Windows compile evidence.

## V29.3 candidate evidence

Fresh V29.3 candidate được reconstructed từ source/runner thực sự trong Windows diagnostic V29.1. Strategy source chỉ thay đúng một semantic line: `dt.minute -> dt.min`; runner chỉ harden distribution/preflight/diagnostic semantics.

Candidate strategy source SHA-256:
`eb5989c1854329a8487a45c5bf248ac37f61b9b4e3a962ff12667a4ee09eb5e2`

Candidate ZIP SHA-256:
`a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`

Local QA: pytest 6/6 PASS, ZIP integrity PASS, internal manifest 10/10 PASS, secret/login scan PASS, no `OrderSend`/`CTrade`, no cache artifacts.

Candidate trên chưa được coi là GitHub-hosted canonical release cho tới khi source/artifact materialization hoàn tất. CI hiện fail-closed có chủ đích.

## Hệ quả

- Không đổi strategy/risk/exit/adaptive logic ngoài field-name compile correction đã kiểm chứng.
- Không gọi broker/order trong CI/builder.
- MetaEditor 0 errors / 0 warnings vẫn là runtime acceptance gate đầu tiên.
- REAL-MONEY LIVE TRADING vẫn bị cấm.
