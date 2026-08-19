# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/uncontrolled grid/doubling after loss.
- Không commit login/password/token/secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Current strategy

V29 adaptive shadow-expert catalog: 12 candidates × 4 virtual books. Compile/distribution hardening không đổi strategy/risk/exit/adaptive semantics ngoài compile correction `dt.minute -> dt.min`.

## Compile/distribution incidents — MUST NOT REPEAT

- V29.0 BROKEN: missing `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`.
- V29.1 Windows diagnostic SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`: MetaEditor 1 error / 0 warnings tại line 680 do `dt.minute`; MQL5 dùng `min`.
- Historical `recovery/v29_adaptive_expert_lab_one_click.zip.b64` vẫn là V29.0 blob và bị CRC corruption/truncation. V29.1/V29.2 patch/docs/local release SHA không được dùng làm canonical GitHub release evidence.
- CI hiện fail-closed để ngăn historical recovery blob tạo user release.

## V29.3 candidate evidence

Fresh candidate được reconstructed từ đúng source/runner trong user diagnostic V29.1.

Strategy source chỉ thay đúng một semantic line: `dt.minute -> dt.min`.

Runner thêm pre-MetaEditor source preflight cho:
- 5 required helpers;
- `MqlDateTime`, `MqlRates`, `MqlTick` members;
- candidate/book counts;
- tester/safety markers;
- forbidden native-order tokens.

Candidate strategy SHA-256:
`eb5989c1854329a8487a45c5bf248ac37f61b9b4e3a962ff12667a4ee09eb5e2`

Candidate ZIP SHA-256:
`a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`

Local QA: pytest 6/6 PASS, ZIP integrity PASS, internal manifest 10/10 PASS, secret/login scan PASS, no native-order tokens, no cache artifacts.

Không fabricated GitHub CI PASS: candidate hiện chưa materialize thành GitHub-hosted canonical artifact.

## Next action

Chỉ chạy fresh V29.3 candidate, không reuse V29.0/V29.1/V29.2 folders cũ. First Windows acceptance gate: MetaEditor 0 errors / 0 warnings. Nếu qua thì single stateful 18-month Strategy Tester batch → một ZIP. Sau robustness gates chỉ PAPER/DEMO; LIVE forbidden.
