# Recovery checkpoint — V27 Economic Calendar / event-aware ML-DL

Ngày: 2026-08-18.

REAL-MONEY LIVE TRADING = FORBIDDEN.

## User-facing output requirement — non-negotiable
User explicitly requires that future coordinator/recovery sessions **do not show internal Python/tooling code** before or after normal answers unless the user asks to see code.

Do not expose:
- scratch Python;
- artifact-packaging code;
- tool-call payloads;
- implementation plumbing;
- internal helper scripts merely because they were executed.

User-visible output should contain only useful deliverables: conclusions, evidence, file links, SHA-256, instructions, diagnostics and next steps. Preserve this requirement across recovery.

## Current research state
- V25 established ML range-regime scores as useful mainly for abstention/routing efficiency, not statistically decisive return uplift.
- V26 exported broad MT5 historical data including cross-asset bars and 17.7M XAUUSDm broker ticks.
- Cross-asset M30 range modeling remains stronger than direct-direction modeling.
- V1.3 low-timeframe top-up obtained XAU M5/M15 and context M5; these add range information but do not create stable direction alpha. Do not request more M1 unless new evidence justifies it.
- Current orthogonal-data gate is V27 MT5 Economic Calendar.

## V27.2 status
Calendar exporter compiles with 0 errors / 0 warnings and runs real progress. It was stopped by runner hard watchdog before completion, not by a calendar API error. Diagnostic showed approximately 24k rows, 80 chunks and progress into CNY with `last_error=0`.

A partial recovery utility was created to copy the incomplete-but-useful calendar run directly from MT5 Common Files.

User screenshot confirms recovery utility completed for run `20260818_093825`, calendar CSV size about 5.72 MB, and printed output path:
`C:\Users\welcome\OneDrive\Desktop\mt5_quant_calendar_PARTIAL_RECOVERY_20260818_141210.zip`

If user reports no file, check OneDrive Desktop first. Do not rerun the 90-minute exporter unless partial data is actually missing or unusable.

## Validation rules
- chronological walk-forward only;
- no random CV;
- no same-sample threshold tuning promoted as confirmation;
- partial Aug-2026 has already been inspected;
- final model/routing changes require MT5 replay;
- no real-money live trading.
