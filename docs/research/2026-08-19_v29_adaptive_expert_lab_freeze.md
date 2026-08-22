# V29 Adaptive Expert Lab — frozen pre-runtime gate

Ngày: 2026-08-19.

## Policy note

V29 was a historical Strategy Tester research milestone. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V29's tester/no-native-order contract was phase-specific and is not a permanent prohibition on researching or preparing production/live trading with real capital.

## Scope

V29 replaces the rejected fixed `range percentile -> family` rule with causal shadow-expert tracking. No new user data/exporter is required.

## Frozen catalog

12 candidates × 4 virtual books × 18 independent monthly accounting resets (Feb-2025 → Jul-2026), including controls, orthogonal slow-momentum controls and adaptive EWMA/change-point probes.

Adaptive shadow experts: EMA skip20, MACD gap10, BOS/FVG gap8, Trend gap5 and slow momentum. Only normalized control-book realized R updates causal EWMA scores. The CP probe controls adaptation speed rather than Buy/Sell direction.

## Stateful runner contract

- three sequential 6-month Strategy Tester chunks;
- monthly PnL/risk accounting resets remain independent;
- adaptive expert score state carries across chunk boundaries;
- each retry restores exact pre-chunk adaptive state;
- checkpoint reuse requires matching source/template/chunk fingerprint and state snapshot;
- monthly summary + trade ledger remain enabled.

## Static QA

- pytest 11/11 PASS;
- Python analyzer py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- summary header/row field-count check PASS;
- MQL5 FileWrite parameter-limit check PASS;
- V29 executable safety scan PASS for its tester-only contract;
- no cache artifacts in release ZIP.

One-click release SHA-256: `a0a859b42052dca6592c04274b33bccf85ae986f0f235212458fc76eec0ded69`.
Internal kit manifest: 11/11 PASS. ZIP integrity PASS.

Windows MetaEditor/runtime was not yet claimed at this checkpoint. A successful historical V29 batch would advance the then-current research workflow toward paper/demo forward validation.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
