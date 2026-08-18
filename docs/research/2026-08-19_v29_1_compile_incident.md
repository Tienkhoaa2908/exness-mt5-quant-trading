# V29 compile incident chain / V29.2 hotfix

Ngày: 2026-08-19.

## V29.0
Windows MetaEditor failed before Strategy Tester with 100 errors / 50 warnings. Root cause: refactor dropped five shared helper definitions while call sites remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. Diagnostic ZIP creation also failed because the runner path was unstable.

## V29.1
Corrective action restored all five helpers from previously Windows-compiled V28 code and switched diagnostic/main script-root logic to `$PSScriptRoot`. Diagnostic packaging then worked correctly.

User Windows V29.1 evidence:
- MetaEditor: 1 error / 0 warnings;
- exact compiler error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`;
- diagnostic ZIP successfully captured source, compile log, runner and error record.

Root cause: `SignalSlowMomentum` referenced `dt.minute`, but `MqlDateTime` uses `min` for minutes.

## V29.2
- replace `dt.minute` with `dt.min`;
- add a regression test validating every referenced member on declared `MqlDateTime` variables against the official contract: `year, mon, day, hour, min, sec, day_of_week, day_of_year`;
- preserve V29 catalog/risk/exit/adaptive rules unchanged;
- preserve working diagnostic bundle behavior.

Local QA:
- pytest 14/14 PASS;
- analyzer/tests py_compile PASS;
- MQL delimiter balance PASS;
- helper consistency PASS;
- MqlDateTime member-contract lint PASS;
- safety scan PASS;
- manifest 11/11 PASS;
- ZIP integrity PASS.

V29.2 release SHA-256: `7e74deeb41f7f573c39014454ea5b47f93d9c2bcdfe7a2882aa9c1e819782e5c`.
Patch: `recovery/v29_2_compile_hotfix.patch`.

V29.0 and V29.1 must not be reused. Windows MetaEditor 0/0 remains the first acceptance gate.
