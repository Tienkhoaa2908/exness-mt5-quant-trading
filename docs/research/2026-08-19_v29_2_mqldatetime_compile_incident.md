# V29.1 Windows compile incident / V29.2 correction

Ngày: 2026-08-19.

## Windows evidence
User diagnostic ZIP SHA-256: `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`.

MetaEditor result: **1 error / 0 warnings**.
Exact compiler error: `AdaptiveExpertLabV1.mq5(680,10): error 256: undeclared identifier 'minute'`.

## Root cause
`SignalSlowMomentum` used `dt.minute`, but the official MQL5 `MqlDateTime` structure exposes `min`, not `minute`.

This is independent of the earlier V29.0 missing-helper incident. V29.0 and V29.1 are both retired and must not be reused.

## V29.2 corrective action
- change only the strategy-source member access `dt.minute -> dt.min`;
- preserve candidate catalog, risk, exits and adaptive-state rules;
- add regression validation for all `MqlDateTime` member accesses against the official field set;
- also validate used `MqlRates` and `MqlTick` member names;
- add a user-machine PowerShell source preflight before MetaEditor for required helper markers, `.minute`, candidate count, tester guard and forbidden order-path tokens;
- retain the V29.1 diagnostic-path correction.

## V29.2 local release gate
- pytest **16/16 PASS**;
- analyzer/tests py_compile PASS;
- MQL and PowerShell delimiter checks PASS;
- required helper-definition checks PASS;
- MqlDateTime/MqlRates/MqlTick member-contract lint PASS;
- user-machine source-preflight regression PASS;
- FileWrite/safety scans PASS;
- internal kit manifest **17/17 PASS**;
- ZIP integrity PASS;
- no cache artifacts.

V29.2 release SHA-256: `d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

Windows MetaEditor **0 errors / 0 warnings** remains the first runtime acceptance gate. Static QA is not Windows compile evidence.
