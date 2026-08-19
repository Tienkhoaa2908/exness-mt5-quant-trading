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

V29 adaptive shadow-expert catalog: 12 candidates × 4 virtual books. Compile/distribution hardening không đổi strategy/risk/exit/adaptive semantics.

## Compile/distribution incidents — MUST NOT REPEAT

V29.0 BROKEN: missing `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`.

V29.1 diagnostic SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`: 1 error / 0 warnings, line 680 dùng `dt.minute`. Official MQL5 field là `min`.

V29.2 sửa source và source/member preflight. Tuy nhiên stale V29.1 folder vẫn runnable, nên user đã chạy nhầm.

## Active release

Chỉ user-facing release `v29_3_distribution_hardening`.

Nó được CI build deterministic từ pinned V29.2 payload SHA-256 `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334` và thêm:
- release identity;
- payload hash manifest;
- wrapper preflight;
- outer diagnostic identity.

CI phải verify exact payload, helper/member contracts, `.minute` absence, tester/safety/native-order paths, analyzer, template/chunks, pytest và secret/login scan trước khi upload artifact.

Không chạy trực tiếp V29.0/V29.1/V29.2 folders c�I.

## Next action

Lấy only verified V29.3 CI artifact. First Windows acceptance gate: MetaEditor 0 errors / 0 warnings. Nếu qua thì single stateful 18-month Strategy Tester batch → một ZIP. Sau robustness gates chỉ PAPER/DEMO; LIVE forbidden.
