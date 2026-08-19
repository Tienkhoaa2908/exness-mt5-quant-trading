# V29 compile incident chain / V29.2 hotfix

Ngày: 2026-08-19.

## V29.0
Windows MetaEditor failed before Strategy Tester with 100 errors / 50 warnings. Root cause: refactor dropped five shared helper definitions while call sites remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. Diagnostic ZIP creation also failed because the runner path was unstable.

## V29.1
Corrective action restored all five helpers from previously Windows-compiled V28 code and switched diagnostic/main script-root logic to `$PSScriptRoot`. Diagnostic packaging then worked correctly.

User Windows V29.1 diagnostic ZIP SHA-256: `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`.
MetaEditor: **1 error / 0 warnings**.
Exact compiler error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`.

Root cause: `SignalSlowMomentum` referenced `dt.minute`, but MQL5 `MqlDateTime` uses `min` for minutes.

## V29.2
- replace `dt.minute` with `dt.min`;
- validate every referenced member on `MqlDateTime` against the official field set;
- also validate used `MqlRates` and `MqlTick` members;
- add user-machine source preflight before MetaEditor for helper markers, invalid `.minute`, candidate count, tester guard and forbidden order-path tokens;
- preserve V29 catalog/risk/exit/adaptive rules unchanged;
- preserve working diagnostic bundle behavior.

Local QA:
- pytest **16/16 PASS**;
- analyzer/tests py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- helper consistency PASS;
- standard-structure member-contract lint PASS;
- source-preflight regression PASS;
- safety scan PASS;
- internal manifest **17/17 PASS**;
- ZIP integrity PASS; no cache artifacts.

V29.2 release SHA-256: `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.
Patch: `recovery/v29_2_compile_hotfix.patch`.
Incident detail: `docs/research/2026-08-19_v29_2_mqldatetime_compile_incident.md`.

V29.0 and V29.1 must not be reused. Windows MetaEditor 0/0 remains the first acceptance gate.
