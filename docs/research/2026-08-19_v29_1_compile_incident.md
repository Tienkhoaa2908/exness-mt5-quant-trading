# V29.0 Windows compile incident / V29.1 hotfix

Ngày: 2026-08-19.

## Runtime evidence
User Windows run of V29.0 failed before Strategy Tester:
- MetaEditor: 100 errors / 50 warnings;
- first cascade centered around calls to `ReadOne`;
- diagnostic ZIP creation also failed because runner path was null.

## Root cause
Adaptive refactor dropped five utility helper definitions while their call sites remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. The old static release checks covered delimiter balance, FileWrite width and safety, but did not assert that required helper definitions survived refactoring.

The diagnostic path bug was independent: `$MyInvocation.MyCommand.Path` was used inside a function, where it did not provide a stable script path.

## V29.1 corrective action
- restore five helpers from previously Windows-compiled V28 implementation;
- use `$PSScriptRoot` for main/diagnostic script root;
- add regression tests for helper definitions and diagnostic-root stability;
- preserve V29 catalog, risk, exit and adaptive rules unchanged.

## Local gate
- pytest 13/13 PASS;
- Python compile PASS;
- MQL delimiter balance PASS;
- five required helper definitions each exactly once;
- helper consistency vs V28 compiled base PASS;
- safety scan PASS;
- internal manifest 11/11 PASS;
- ZIP integrity PASS.

V29.1 release SHA-256: `b8176551870b218f47322bae72c7a78be2d0efde8eec7237dab91ab4f8aeb824`.
Patch: `recovery/v29_1_compile_hotfix.patch`, SHA-256 `c5f999e546b3aa67dbe704e9dbc90bf62510e2134aea4e8c3c44e5d759c0b65c`.

Windows MetaEditor 0/0 remains pending. V29.0 must never be reused.
