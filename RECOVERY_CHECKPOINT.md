# Recovery checkpoint — V29.2 Adaptive Expert Compile Gate

Ngày: 2026-08-19.

REAL-MONEY LIVE TRADING = FORBIDDEN. Stop-risk research ceiling 1.00%/trade. No native broker orders.

## User-facing requirement
Không hiển thị Python/tooling nội bộ nếu user không yêu cầu. Tooling chạy âm thầm; user-visible tập trung vào evidence, artifact, hash, thao tác, lỗi và bước tiếp theo.

## V28 final decision
Calendar extraction is CLOSED. Core cross-asset range ML generalizes, but incremental calendar uplift and fixed scalar `range -> family` routing failed later confirmation. Do not run old V28 replay kit.

## V29 catalog
12 candidates × 4 virtual books × 18 monthly accounting resets, Feb-2025 → Jul-2026. Controls EMA/MACD/BOS/Trend/EMA+BOS8; slow 16h+24h momentum controls; adaptive realized-R EWMA/change-severity variants. Catalog/risk/exit logic unchanged by compile hotfixes.

## Compile incident chain
V29.0 is BROKEN and must never be reused. Windows MetaEditor: 100 errors / 50 warnings. Root cause: missing shared helper definitions after refactor; diagnostic path bug also prevented ZIP creation.

V29.1 restored helpers and fixed diagnostic packaging. User Windows run then failed with exactly 1 error / 0 warnings: `AdaptiveExpertLabV1.mq5(680,10): undeclared identifier 'minute'`.

V29.2 corrects `dt.minute` to `dt.min` in `SignalSlowMomentum`. Official MQL5 `MqlDateTime` uses fields `year, mon, day, hour, min, sec, day_of_week, day_of_year`.

Mandatory release QA now includes:
- custom helper definition consistency;
- standard MQL structure member contract lint, starting with `MqlDateTime`;
- user-machine source preflight before MetaEditor for helper definitions and invalid `.minute` token;
- delimiter/FileWrite/safety scans;
- artifact manifest/ZIP integrity;
- Windows MetaEditor 0/0 remains the first runtime acceptance gate.

Static V29.2 evidence: pytest 15/15 PASS; analyzer/tests py_compile PASS; MQL balance PASS; helper consistency PASS; MqlDateTime contract PASS; runner preflight regression PASS; safety scan PASS; internal kit manifest 11/11 PASS; ZIP integrity PASS; no cache artifacts.

V29.2 release SHA-256: `d6cb34f77724bb4c5c115259f196e61352150f35c55ad1b06629ab34b9060a63`.
Patch: `recovery/v29_2_compile_hotfix.patch`.
V29.0 and V29.1 must not be reused.

## Next action
Run only V29.2 in a fresh folder. First gate: Windows MetaEditor 0 errors / 0 warnings. If compile passes, run the one stateful 18-month Strategy Tester batch. If robustness gates pass, proceed to PAPER/DEMO forward only. LIVE remains forbidden.
