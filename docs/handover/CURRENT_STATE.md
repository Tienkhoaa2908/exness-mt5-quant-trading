# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety invariant
REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research labs.

## User-facing requirement — MUST PRESERVE
Không hiển thị Python nội bộ, scratch/artifact-packaging code, tool payload hoặc implementation plumbing nếu user không yêu cầu. Tooling chạy âm thầm; user-visible chỉ cần kết luận/evidence/file/SHA/thao tác/lỗi/bước tiếp theo.

## V28 closed
Calendar extraction is CLOSED. Core cross-asset range prediction generalizes, but fixed scalar `range -> family` mapping and incremental calendar uplift failed later confirmation. Do NOT run old V28 replay kit.

## V29 current gate
Frozen 12-candidate adaptive shadow-expert catalog remains unchanged. Slow 16h+24h momentum is an orthogonal expert; adaptive variants use causal realized-R EWMAs/change severity; validated range ML remains context only.

## Compile incident history
V29.0 is BROKEN: Windows MetaEditor produced 100 errors / 50 warnings because five shared utility helpers were dropped during refactor while calls remained. Its diagnostic path also failed.

V29.1 restored those helpers and fixed diagnostic packaging. User Windows diagnostic ZIP SHA-256 `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5` then showed exactly **1 error / 0 warnings**: `AdaptiveExpertLabV1.mq5(680,10): undeclared identifier 'minute'`.

Official MQL5 `MqlDateTime` minute member is `min`, not `minute`. V29.2 fixes `dt.minute -> dt.min` and adds both development member-contract lint and a user-machine source preflight before MetaEditor.

Mandatory MQL release QA now includes helper-definition consistency + MqlDateTime/MqlRates/MqlTick member lint + user-machine source preflight + delimiter/FileWrite/safety + artifact integrity. Static QA is never represented as Windows compile evidence.

V29.2 local evidence:
- pytest **16/16 PASS**;
- analyzer/tests py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- helper consistency PASS;
- MqlDateTime/MqlRates/MqlTick member-contract lint PASS;
- runner source-preflight regression PASS;
- safety scan PASS;
- internal kit manifest **17/17 PASS**;
- ZIP integrity PASS; no cache artifacts.

V29.2 release SHA-256: `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.
Incident report: `docs/research/2026-08-19_v29_2_mqldatetime_compile_incident.md`.
Patch: `recovery/v29_2_compile_hotfix.patch`.
V29.0 and V29.1 must not be reused.

## Next gate
User runs only V29.2 in a fresh folder. Accept the batch only if MetaEditor reports 0 errors / 0 warnings. If compile passes, let the single stateful 18-month Strategy Tester batch complete. If robustness gates pass, next endpoint is PAPER/DEMO forward validation only. LIVE remains forbidden.
