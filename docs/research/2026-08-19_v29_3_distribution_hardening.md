# 2026-08-19 — V29.3 distribution hardening

## Policy note

V29.3 was a historical Strategy Tester/distribution-hardening milestone. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V29.3's no-order/virtual-research contract was phase-specific and is not a permanent prohibition on researching or preparing production/live trading with real capital.

## User evidence

Diagnostic: `mt5_quant_v29_adaptive_expert_DIAGNOSTIC_20260819_022329.zip`
SHA-256: `6f457681e2f868daf0939b74c7f63420f72b37ceb3375110f652bbd7be9f20f5`.

ZIP confirmed V29.1 source/runner and the exact MetaEditor error `undeclared identifier 'minute'`; the correct `MqlDateTime` member is `min`.

## Release-governance root cause

Historical recovery payload drift/corruption meant prior V29.1/V29.2 SHA claims were not sufficient as GitHub-reproducible source-of-truth. CI hardening correctly moved integrity checks before Windows execution.

## Hardening

- clean-checkout compileall + pytest;
- secret/tracked-login scan;
- historical recovery integrity inventory;
- conditional historical-test skip instead of collection crash;
- removal of tracked MT5 login from historical template;
- ADR-036 fail-closed stale-kit/release-integrity rule;
- handover updated without fabricated CI PASS.

## Fresh V29.3 candidate reconstruction

Source was rebuilt from the Windows V29.1 diagnostic source/runner, not corrupted historical recovery B64.

Strategy semantic correction:
`dt.minute` -> `dt.min`.

Runner added pre-MetaEditor source preflight for helper definitions, standard MQL structures, candidate/book counts, tester markers and absence of native-order APIs.

Candidate strategy SHA-256:
`eb5989c1854329a8487a45c5bf248ac37f61b9b4e3a962ff12667a4ee09eb5e2`.

Candidate runner SHA-256:
`0b66530c6baee57490caad35d866c5c1844961122a4444a088c32c497bf9868f`.

Candidate ZIP SHA-256:
`a415f79bd31df3f9928aaf25fc2992288fa1ca1ea4073aa90a375bb7e3597132`.

## Local QA evidence

- pytest 6/6 PASS;
- ZIP `testzip` PASS;
- internal manifest 10/10 PASS;
- secret/login scan PASS;
- `.minute` absent, `dt.min` present;
- no `OrderSend` / `CTrade` in V29.3;
- runner preflight precedes MetaEditor compile call.

Windows compile was not claimed until actually observed.

## Historical V29.3 execution scope

V29.3 build/QA did not connect to MT5/broker and did not send orders. Virtual-order research semantics were retained for that milestone.

Current project-wide production/live research/deployment intent is governed by ADR-049 and later V49 readiness evidence.
