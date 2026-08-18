# Recovery checkpoint — V29.1 Adaptive Expert Compile Hotfix

Ngày: 2026-08-19.

REAL-MONEY LIVE TRADING = FORBIDDEN. Stop-risk research ceiling 1.00%/trade. No native broker orders.

## User-facing requirement
Không hiển thị Python/tooling nội bộ nếu user không yêu cầu. Tooling chạy âm thầm; user-visible tập trung vào evidence, artifact, hash, thao tác, lỗi và bước tiếp theo.

## V28 final decision
Calendar extraction is CLOSED. Core cross-asset range ML generalizes, but incremental calendar uplift and fixed scalar `range -> family` routing fail later confirmation. Do not run the old V28 replay kit.

## V29 catalog
12 candidates × 4 virtual books × 18 monthly accounting resets, Feb-2025 → Jul-2026. Controls EMA/MACD/BOS/Trend/EMA+BOS8; slow 16h+24h momentum controls; adaptive realized-R EWMA/change-severity variants. Catalog/risk/exit logic unchanged by V29.1.

## V29.0 compile incident
The first V29.0 release is BROKEN and must never be reused. User Windows MetaEditor produced 100 errors / 50 warnings before Strategy Tester started.

Root cause: five utility helper definitions were dropped during refactor while calls remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. Diagnostic packaging also failed because `$MyInvocation.MyCommand.Path` was null inside the diagnostic function.

## V29.1 fix and mandatory release gate
- restore all five helpers from previously Windows-compiled V28 code;
- use `$PSScriptRoot` for stable runner/diagnostic root;
- regression-test required helper definitions before packaging;
- retain delimiter/FileWrite/safety tests;
- do not call static QA Windows compile evidence.

Static V29.1 evidence: pytest 13/13 PASS; analyzer/tests py_compile PASS; MQL balance PASS; all five helpers defined exactly once; custom helper consistency vs V28 compiled base PASS; safety scan PASS; internal kit manifest 11/11 PASS; ZIP integrity PASS.

V29.1 release SHA-256: `b8176551870b218f47322bae72c7a78be2d0efde8eec7237dab91ab4f8aeb824`.
Hotfix patch: `recovery/v29_1_compile_hotfix.patch`, SHA-256 `c5f999e546b3aa67dbe704e9dbc90bf62510e2134aea4e8c3c44e5d759c0b65c`.

## Next action
Run only V29.1 in a fresh folder. First gate is Windows MetaEditor 0 errors / 0 warnings. If compile passes, run the one stateful Strategy Tester batch. If it passes robustness gates, proceed to PAPER/DEMO forward only. LIVE remains forbidden.
