# 2026-08-19 — V29.3 distribution hardening

## User evidence

Diagnostic: `mt5_quant_v29_adaptive_expert_DIAGNOSTIC_20260819_022329.zip`  
SHA-256: `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`

ZIP xác nhận:
- source/runner là V29.1;
- MetaEditor 1 error / 0 warnings;
- exact error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`;
- V29.1 source SHA-256 `02590d9fe520a137b44c01226f17500a8813dc89ce2117bcb500bcb727159d57`;
- V29.1 runner SHA-256 `8878dc04e9fec9b516c9c9836e940cfd4965ce5dd783a58f4e434748c9317b50`.

MQL5 `MqlDateTime` member đúng là `min`.

## Release-governance root cause

Audit Git history + CI recovery cho thấy lỗi không dừng ở stale folder:

1. `recovery/v29_adaptive_expert_lab_one_click.zip.b64` được tạo ở V29.0 và blob không được thay bằng V29.1/V29.2 artifact.
2. V29.1/V29.2 chủ yếu cập nhật patch/docs/local release SHA claims.
3. Clean-checkout decode historical blob không tạo được valid ZIP central directory.
4. Local-header recovery xác nhận CRC failure tại `scripts/analyze_adaptive_expert_bundle.py`, sau runner có transport gap/truncation và không còn đầy đủ local payload entries.
5. Vì vậy các V29.1/V29.2 SHA claims cũ không đủ làm GitHub-reproducible source-of-truth.

CI mới đã làm đúng việc: **block artifact trước khi user nhận** thay vì đẩy lỗi sang Windows.

## Hardening đã push

- clean-checkout `compileall` + pytest;
- secret/tracked-login scan;
- historical recovery integrity inventory;
- V21 historical test skip có điều kiện thay vì collection crash;
- xóa tracked MT5 login khỏi historical template;
- ADR-036 fail-closed stale-kit/release-integrity rule;
- PR/handover cập nhật đúng trạng thái, không fabricated CI PASS.

## Fresh V29.3 candidate reconstruction

Nguồn dựng lại là **Windows V29.1 diagnostic source/runner**, không dùng historical recovery B64.

Strategy source diff V29.1 → V29.3 có đúng một semantic change:

```diff
- if(dt.minute!=0 || (dt.hour!=0 && dt.hour!=8)) return true;
+ if(dt.min!=0 || (dt.hour!=0 && dt.hour!=8)) return true;
```

Runner thêm pre-MetaEditor source preflight cho:
- `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`;
- `MqlDateTime`, `MqlRates`, `MqlTick` member contracts;
- `CANDIDATE_COUNT=12`, `BOOK_COUNT=4`;
- tester/safety markers;
- reject `OrderSend`, `CTrade`, `MqlTradeRequest`, `TRADE_ACTION_*`.

Analyzer/config/tests được dựng lại từ frozen V29 contract thay vì dùng corrupted historical analyzer member.

Candidate strategy SHA-256:
`eb5989c1854329a8487a45c5bf248ac37f61b9b4e3a962ff12667a4ee09eb5e2`

Candidate runner SHA-256:
`0b66530c6baee57490caad35d866c5c1844961122a4444a088c32c497bf9868f`

Candidate ZIP SHA-256:
`a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`

## Local QA evidence

- pytest **6/6 PASS**;
- ZIP `testzip` PASS;
- 11 ZIP members, không cache/pyc;
- internal manifest **10/10 PASS**;
- secret/login scan PASS;
- `.minute` absent, `dt.min` present;
- no `OrderSend` / `CTrade`;
- runner preflight nằm trước MetaEditor compile call.

Không claim Windows compile PASS: MetaEditor chưa chạy candidate này.

## Safety

Không kết nối MT5/broker trong build/QA; không gửi order. Virtual-order research semantics giữ nguyên. LIVE forbidden.

## Acceptance

User chỉ chạy fresh V29.3 candidate. MetaEditor **0 errors / 0 warnings** là gate đầu tiên. Chỉ sau compile PASS mới chạy stateful 18-month replay → một ZIP.
