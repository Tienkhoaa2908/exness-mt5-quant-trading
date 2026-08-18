# V26 top-up analysis and V27 economic-calendar data gate

Ngày: 2026-08-18.

## V1.3 low-timeframe top-up runtime
- uploaded ZIP SHA-256 `5cd3ff37a5f6177e0b2346c57d206d4dd2f32c341bcb97a447f5beb9eb48da33`;
- internal manifest 37/37 PASS;
- terminal `maxbars=1,000,000`;
- total exported bar rows 2,036,382;
- XAUUSDm M5/M15 and all nine context M5 series exported successfully from 2024 through Aug-2026;
- XAUUSDm M1 still returned MT5 `Invalid params` because the requested 2024-present minute history exceeds one million bars.

## ML/DL finding from top-up
Low-TF information is useful mainly for regime magnitude, not direction.

Using a 4h horizon:
- low-TF-only LightGBM range model: mean monthly OOS Spearman ~0.428, positive 12/12 months;
- low-TF-only direction model: mean OOS AUC ~0.501;
- adding 135 raw low-TF features directly to the established M30/cross-asset feature set did not improve mean range rank-correlation in a matched screening experiment;
- a fixed rank ensemble with 10-20% low-TF weight produced only a small mean uplift in the matched screening engine (~0.457 -> ~0.460), insufficient to justify complexity by itself;
- TCN over 72 M5 bars also underperformed the existing M30/cross-asset sequence signal (validation range rho ~0.34, direction ~0.49).

Decision: do not request another M1 export now. More price granularity shows diminishing returns.

## Next orthogonal data source: MT5 Economic Calendar
MetaTrader 5 exposes historical calendar values through `CalendarValueHistory`, including actual/forecast/previous/revised values, event importance and metadata. The API uses trade-server time, so the exporter records raw server timestamps and current server-vs-GMT metadata; offline joining must validate timezone/DST before model use.

V27 exporter currencies: USD, EUR, GBP, JPY, CNY; history from 2022-01-01 to run time.

One-click release SHA-256: `d4243cf04f0d7085111d62e02a4ca7840e1db363848b8cc1048ded5911110557`.

Safety: DATA ONLY; REAL-MONEY LIVE TRADING = FORBIDDEN; no `OrderSend`, no `CTrade`, `AllowLiveTrading=0` in startup config.
