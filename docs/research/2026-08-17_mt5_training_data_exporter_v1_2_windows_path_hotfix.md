# MT5 Training Data Exporter V1.2 — Windows path hotfix

Ngày: 2026-08-17.

## Runtime issue in V1.1

User run failed before Python discovery with:
`Resolve-Path : Illegal characters in path.`

Root cause: the CMD wrapper passed `%~dp0` as a quoted `-Root` argument to PowerShell. `%~dp0` ends with a backslash, and on the reported Windows/PowerShell command-line path this could arrive with a literal quote character, making the path invalid before the bootstrap entered its normal diagnostics.

## V1.2 fix

- remove `-Root "%~dp0"` from the CMD → PowerShell call;
- derive package root inside PowerShell from `$PSScriptRoot`;
- replace `Resolve-Path -LiteralPath $Root` with `Get-Item` on the derived directory;
- keep the hardened Python discovery from V1.1;
- keep local `.venv`, dependency checks and diagnostic ZIP behavior;
- make the optional live microstructure recorder reuse `.venv\Scripts\python.exe` instead of calling `py -3`.

## Local QA

- Python `py_compile`: PASS;
- pytest: 8/8 PASS;
- executable order-path scan: PASS;
- internal kit manifest: 9/9 PASS;
- ZIP integrity: PASS.

Release artifact SHA-256:
`ff3ec7baeedf440f58ba4fce0e49158e6f6fe7ba0f8b24f32065b17d7acc2c7b`

## Safety

DATA ONLY. REAL-MONEY LIVE TRADING = FORBIDDEN. No order path, no account/order-history export.

Windows runtime export is not claimed until user runs V1.2 and uploads either the result ZIP or a diagnostic ZIP.
