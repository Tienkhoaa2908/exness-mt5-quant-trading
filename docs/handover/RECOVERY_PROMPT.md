# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật an toàn
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Luật giao tiếp với user — MUST READ / MUST PRESERVE
- User không muốn thấy code Python nội bộ, scratch code, code đóng gói artifact, tool payload hoặc implementation plumbing xuất hiện trước/sau câu trả lời.
- Không trình bày code nội bộ chỉ vì tool đã chạy. Chỉ hiện code khi user chủ động yêu cầu xem code.
- Phần trả lời user ưu tiên DONE / EVIDENCE / DECISIONS / ISSUES / NEXT khi phù hợp; file, SHA-256, thao tác và chẩn đoán.
- Tooling nội bộ phải chạy âm thầm. Yêu cầu này phải được giữ sau mọi recovery.

## V28 is closed
Calendar extraction is CLOSED; do not request more data exports. Core cross-asset range ML generalizes, but incremental calendar uplift and fixed scalar `range -> family` routing failed later confirmation. Do not run old V28 replay kit.

## Current gate — V29 Adaptive Change-Point + Multi-Horizon Expert Lab
Frozen catalog remains 12 candidates × 4 books × 18 months. Candidate/risk/exit/adaptive rules are unchanged by compile hotfixes.

## Compile incidents — MUST READ / MUST NOT REPEAT
V29.0 is BROKEN: Windows MetaEditor produced 100 errors / 50 warnings because refactor dropped five helper definitions while call sites remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. V29.0 also had a diagnostic-path bug. Never run it again.

V29.1 restored those helpers and fixed diagnostic packaging. User Windows diagnostic ZIP SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` then produced exactly **1 error / 0 warnings**. Exact compiler error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`.

Root cause V29.1: `SignalSlowMomentum` used `dt.minute`, but official MQL5 `MqlDateTime` fields are `year, mon, day, hour, min, sec, day_of_week, day_of_year`; correct minute field is `min`.

V29.2 replaces `dt.minute` with `dt.min` and adds prevention layers:
- development regression lint validating every referenced `MqlDateTime` member against the official field contract;
- validation of used `MqlRates` and `MqlTick` members;
- user-machine PowerShell source preflight before MetaEditor for required helper markers, invalid `.minute`, candidate count, tester guard and forbidden order-path tokens.

Future MQL release QA must include helper-definition consistency, standard-structure member contract checks, user-machine source preflight, delimiter/FileWrite/safety checks, artifact integrity, then Windows MetaEditor 0 errors / 0 warnings as first runtime acceptance gate. Do not call static QA compile evidence.

V29.2 local QA:
- pytest **16/16 PASS**;
- analyzer/tests py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- required helper definitions PASS;
- MqlDateTime/MqlRates/MqlTick member-contract lint PASS;
- runner source-preflight regression PASS;
- executable safety scan PASS;
- internal kit manifest **17/17 PASS**;
- ZIP integrity PASS; no cache artifacts.

V29.2 release SHA-256: `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.
Incident report: `docs/research/2026-08-19_v29_2_mqldatetime_compile_incident.md`.
V29.2 patch: `recovery/v29_2_compile_hotfix.patch`.
V29.0 and V29.1 must not be reused.

## Next action after recovery
Give/run only V29.2 in a fresh folder. First acceptance gate is Windows MetaEditor **0 errors / 0 warnings**. If compile passes, allow the single 18-month stateful Strategy Tester batch to complete. If robust replay gates pass, proceed to PAPER/DEMO forward validation only. REAL-MONEY LIVE TRADING remains forbidden.
