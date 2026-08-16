# 2026-08-16 — Monthly rescreen stall + profit-giveback review

## Uploaded diagnostic

User diagnostic ZIP SHA-256:

`1248ea05553b71f484d186cc640323a918ec715a8b1324c18f17966da0897fc4`

All 25 paths listed in its `bundle_manifest_sha256.txt` recomputed successfully.

## Why the previous runner appeared to hang

The old `Monthly Quality / Exit Re-screen V1` runner launched a new MT5 terminal for every calendar month. On the user's machine, the first eight months (`2025_02` through `2025_09`) ran successfully; individual month tests took roughly 1–2 minutes. The next launch (`2025_10`) hit broker-service synchronization failure:

- `12:00:56` — authorization failed: `Service is not available`;
- `12:01:44` — tester: `not synchronized with trade server`;
- automatic testing then remained alive without a fresh research artifact;
- the terminal eventually exited after roughly 11 minutes.

Subsequent retries encountered the same service-unavailable / not-synchronized state.

This was not evidence that the strategy calculation itself required unlimited time. It was a runner design weakness: `Start-Process -Wait` had no watchdog, and 18 separate MT5 startups created 18 separate opportunities for broker startup/synchronization failure.

The diagnostic packager also had two evidence gaps:

1. checkpoint destination was not pre-created before the recursive copy;
2. it searched an obsolete `mt5_quant\quality_exit_lab` path while current runs are under `mt5_quant\runs`.

Both are superseded in Profit Protection Lab V1.

A recovery QA check also found that V17 Git history referenced `experiments/monthly_quality_exit_rescreen_v1/{template.ini,windows.csv}` from tests/runner but did not track those ignored experiment files. V18 restores them explicitly so a clean clone passes the full test suite.

## User-observed exit problem

The current H1 finalist design uses a mostly static exit geometry: initial stop around `2*ATR` and fixed TP around `2R`. The previous experimental runner variant only moved to break-even after reaching +1R. Therefore a trade can become meaningfully profitable and later retrace a large fraction of open profit before either fixed TP or stop closes it.

That behavior is now a first-class research target rather than a visual anecdote. The next lab records, per trade:

- MFE in R;
- MAE in R;
- realized R;
- MFE-to-exit giveback in R;
- profit-capture efficiency;
- count of trades that reached at least +1R but finished at <=0R.

## Next research design

`ProfitProtectionLabV1.mq5` keeps the two H1-aligned entry families fixed and changes only exit/profit-protection logic. Eight pre-registered policies per family:

1. fixed 2R control;
2. break-even at +0.75R;
3. lock +0.25R after +0.75R;
4. lock +0.50R after +1R;
5. stepped locks with 2.5R TP;
6. 0.75R peak-distance trail after +1R with 3R TP;
7. lock 50% of peak R after +1R with 4R TP;
8. take 50% at +1R when lot-step permits; otherwise lock +0.5R; remainder uses break-even and 3R TP.

Initial stop remains 2 ATR to isolate profit-management effects. Any winning virtual policy must later return to native MT5 for dynamic SL/partial-close parity.

## Performance/reliability changes

The lab replaces expensive per-tick `OrderCalcProfit` MTM calls with R-space arithmetic after initial risk-at-stop is calculated. This is XAUUSD/USD-account screening math and therefore still requires native confirmation.

The Windows runner now uses three six-month chunks instead of 18 terminal startups. Each EA run resets all books at calendar-month boundaries internally, preserving independent monthly results while reducing authentication/synchronization surface area.

Runner hardening:

- 30-second heartbeat while MT5 is active;
- bounded chunk watchdog;
- automatic one-time retry;
- early detection of broker `Service is not available` + `not synchronized` combination;
- checkpoint reuse;
- recovery scan of valid Common Files artifacts if checkpoint is lost;
- diagnostic ZIP captures checkpoint and correct `mt5_quant\runs` artifacts.

## Safety

- Tester-only virtual orders.
- `CTrade` is not used in this lab.
- External broker orders = 0.
- Real-money live trading remains forbidden.
- Approved stop-risk research ceiling remains 1.00% per trade.