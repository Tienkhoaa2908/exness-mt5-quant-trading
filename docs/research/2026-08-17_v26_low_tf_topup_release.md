# V26 low-timeframe top-up exporter V1.3

The verified V1.2 export showed `terminal_maxbars=100000`, causing XAUUSDm M1/M5/M15 and all context M5 requests to fail with MT5 `Invalid params` while higher timeframes and raw ticks succeeded.

V1.3 is additive only. It exports:
- XAUUSDm M1/M5/M15 from 2024-01-01;
- context M5 for XAG, EURUSD, GBPUSD, USDJPY, US500, USTEC, US30, USOIL, BTCUSD when available;
- no raw ticks, because 17.7M ticks were already captured in V1.2.

It refuses to run unless `terminal_info.maxbars >= 1,000,000` and prints the exact MT5 setting path.

Local QA:
- pytest 9/9 PASS;
- kit manifest 7/7 PASS;
- ZIP integrity PASS;
- one-click SHA-256 `b22d27396e10810c0acc24d66078725207dad5545392d9f6c3f65eb296a3ac30`.

Safety: DATA ONLY; REAL-MONEY LIVE TRADING = FORBIDDEN; no order path.
