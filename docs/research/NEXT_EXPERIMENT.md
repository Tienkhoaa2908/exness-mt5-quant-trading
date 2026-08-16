# NEXT EXPERIMENT — Profit Protection Lab V1

The previous monthly Quality/Exit re-screen is superseded because its 18-terminal-start runner encountered broker-service synchronization failure and had no bounded watchdog.

## Objective

Keep the two H1-aligned entry families fixed and test whether explicit profit protection improves the one-calendar-month USD 40 profile without raising stop-risk above the current 1.00% research ceiling.

The target failure mode is measurable: trades that reach material open profit and later give back most of it or finish non-positive.

## Catalog

Two entry families x eight exit policies = 16 candidates:

1. fixed 2R control;
2. BE at +0.75R;
3. lock +0.25R at +0.75R;
4. lock +0.50R at +1R;
5. stepped locks, TP 2.5R;
6. trail 0.75R behind peak after +1R, TP 3R;
7. lock 50% of peak R after +1R, TP 4R;
8. take 50% at +1R, move remainder to BE, TP 3R.

Initial stop is fixed at 2 ATR for all candidates.

Each candidate runs four books: normalized 10k @0.50%, USD40 @0.50%, USD40 @0.75%, USD40 @1.00%.

## Monthly evidence

The EA resets all candidate books at every calendar-month boundary and records 18 independent months from 2025-02 through 2026-07.

Per-trade path metrics include MFE, MAE, giveback R, capture efficiency, and whether MFE >= +1R later finished <=0R.

## Runtime

Three MT5 starts only, each covering six months. The runner has heartbeat, watchdog, broker-unavailable detection, one retry, checkpoint reuse and Common Files recovery.

Run:

`scripts/run_profit_protection_lab_v1.cmd`

Virtual screening only; any finalist must return to native MT5. Real-money live trading remains forbidden.