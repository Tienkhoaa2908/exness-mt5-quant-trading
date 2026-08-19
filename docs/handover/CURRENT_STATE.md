# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research screening.

## Strategy state

V29 adaptive shadow-expert catalog giữ nguyên 12 candidates × 4 virtual books. Không claim profitable/winner từ screening ngắn.

## Incident chain

- V29.0 BROKEN: 100 errors / 50 warnings do rơi 5 helper definitions.
- V29.1 sửa helpers nhưng diagnostic `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` cho thấy 1 error / 0 warnings do `dt.minute`.
- Official MQL5 member đúng là `dt.min`.
- V29.2 sửa source + member/source preflight.
- Diagnostic mới nhất chứng minh user vẫn chạy stale V29.1 folder. V29.3 vì vậy harden distribution layer.

## Active user-facing release

Distribution: `v29_3_distribution_hardening`.  
Pinned V29.2 payload decoded ZIP SHA-256: `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

Không chạy trực tiếp V29.0/V29.1/V29.2 folder cũ.

Clean-checkout CI bắt buộc:
- Python compile;
- pytest;
- secret/login scan;
- exact payload SHA;
- helper + predefined-structure member contracts;
- tester/safety/native-order checks;
- analyzer/template/chunk validation;
- deterministic V29.3 wrapper build.

CI chỉ upload artifact nếu toàn bộ gate PASS.

## Next gate

Sau khi V29.3 CI artifact PASS, user chạy đúng artifact đó trong fresh folder. MetaEditor phải **0 errors / 0 warnings**. Sau đó mới chạy single stateful 18-month Strategy Tester replay. Nếu robustness gates đạt thì chỉ PAPER/DEMO forward validation. LIVE vẫn cấm.
