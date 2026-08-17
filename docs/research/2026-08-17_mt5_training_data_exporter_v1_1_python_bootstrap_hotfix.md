# MT5 Training Data Exporter V1.1 — Python bootstrap hotfix

Ngày: 2026-08-17

## Runtime failure observed

V1 failed before any MT5 data request. Windows `py.exe` existed, but `py -3` resolved to a deleted interpreter path:
`C:\Users\welcome\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

Therefore the old runner incorrectly treated presence of `py.exe` as evidence of a working Python installation.

## Fix

V1.1:
- never blindly executes `py -3`;
- enumerates concrete interpreter paths, including `py -0p`, PATH and common user/system Python install directories;
- validates each candidate by actually executing it and requiring Python 3.8+ x64;
- creates a local `.venv` inside the exporter folder;
- installs/verifies `MetaTrader5` and `numpy` only inside that venv;
- if no working Python exists, offers an explicit user prompt to install Python 3.12 via `winget` in user scope;
- creates `mt5_training_data_export_DIAGNOSTIC_*.zip` on Desktop on bootstrap/export failure;
- keeps the CMD window open.

## Static evidence

- pytest: 6/6 PASS;
- Python py_compile: PASS;
- release manifest: 9/9 PASS;
- ZIP integrity: PASS;
- no order path in exporter source.

One-click release SHA-256:
`3c58f14179cdb9e5138434a1931e84a3ca5e10f258da68104f2fee7d22133341`

## Safety

DATA ONLY. REAL-MONEY LIVE TRADING remains forbidden. No password/token/account/order-history export and no order-send path.
