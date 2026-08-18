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

V29.1 restored those helpers and fixed diagnostic packaging. Windows then produced exactly 1 error / 0 warnings: line 680 used `dt.minute` on `MqlDateTime`.

Official `MqlDateTime` minute member is `min`, not `minute`. V29.2 fixes `dt.minute -> dt.min` and adds a release regression lint validating referenced `MqlDateTime` members against the standard field contract.

Mandatory release QA now includes helper-definition consistency + standard-structure member lint + delimiter/FileWrite/safety + artifact integrity. Static QA is never represented as Windows compile evidence.

V29.2 local evidence:
- pytest 14/14 PASS;
- analyzer/tests py_compile PASS;
- MQL delimiter balance PASS;
- helper consistency PASS;
- MqlDateTime member-contract lint PASS;
- safety scan PASS;
- internal kit manifest 11/11 PASS;
- ZIP integrity PASS.

V29.2 release SHA-256: `7e74deeb41f7f573c39014454ea5b47f93d9c2bcdfe7a2882aa9c1e819782e5c`.
Patch: `recovery/v29_2_compile_hotfix.patch`.
V29.0 and V29.1 must not be reused.

## Next gate
User runs only V29.2 in a fresh folder. Accept the batch only if MetaEditor reports 0 errors / 0 warnings. If compile passes, let the single stateful 18-month Strategy Tester batch complete. If robustness gates pass, next endpoint is PAPER/DEMO forward validation only. LIVE remains forbidden.
