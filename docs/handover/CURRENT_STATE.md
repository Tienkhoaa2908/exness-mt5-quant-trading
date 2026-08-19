# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research screening.

## Strategy state

V29 adaptive shadow-expert catalog giữ nguyên 12 candidates × 4 virtual books. Không claim profitable/winner từ screening ngắn.

## Incident chain đã xác minh

- V29.0 BROKEN: 100 errors / 50 warnings do rơi 5 helper definitions.
- V29.1 sửa helpers nhưng Windows diagnostic SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` cho thấy MetaEditor **1 error / 0 warnings** tại `AdaptiveExpertLabV1.mq5(680,10)` vì `dt.minute`.
- MQL5 `MqlDateTime` member đúng là `min`.
- Git history chứng minh `recovery/v29_adaptive_expert_lab_one_click.zip.b64` không từng được thay bằng một V29.1/V29.2 payload mới; blob vẫn là V29.0 historical payload. V29.1/V29.2 tồn tại dưới dạng patch/docs/local release claims.
- Local-header recovery trên blob historical phát hiện CRC corruption và archive truncation. Các SHA V29.1/V29.2 cũ không còn được coi là GitHub-reproducible source-of-truth.

## V29.3 distribution hardening

Branch/PR vẫn fail-closed: CI không upload user release từ historical recovery blob.

Đã thêm:
- Python compile + pytest gate trên clean checkout;
- secret/tracked-login scan;
- V21 legacy test skip có điều kiện thay vì crash collection;
- xóa tracked account Login khỏi historical template;
- recovery integrity inventory;
- ADR/research/handover cho stale-kit prevention.

## Canonical V29.3 candidate từ Windows evidence

Một fresh candidate đã được dựng từ chính V29.1 `AdaptiveExpertLabV1.mq5` + `runner.ps1` trong user diagnostic nói trên.

Strategy source chỉ thay đúng một semantic line:

`dt.minute -> dt.min`

Runner được harden thêm pre-MetaEditor source preflight cho:
- 5 helper definitions bắt buộc;
- `MqlDateTime` / `MqlRates` / `MqlTick` member contracts;
- candidate/book counts;
- tester/safety markers;
- forbidden native-order tokens.

Candidate ZIP SHA-256: `a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`.

Candidate strategy source SHA-256: `eb5989c1854329a8487a45c5bf248ac37f61b9b4e3a962ff12667a4ee09eb5e2`.

Local QA evidence:
- pytest 6/6 PASS;
- ZIP integrity `testzip` PASS;
- internal manifest 10/10 PASS;
- secret/login scan PASS;
- `OrderSend` / `CTrade` absent;
- no cache artifacts.

Đây **chưa phải Windows compile evidence** và candidate artifact hiện chưa được materialize thành GitHub-hosted canonical release. Không fabricated CI PASS.

## Next gate

User chỉ chạy fresh V29.3 candidate, tuyệt đối không reuse folder V29.0/V29.1/V29.2. MetaEditor phải **0 errors / 0 warnings**. Nếu compile PASS mới chạy single stateful 18-month Strategy Tester replay. Nếu robustness gates đạt thì chỉ PAPER/DEMO forward validation. LIVE vẫn cấm.
