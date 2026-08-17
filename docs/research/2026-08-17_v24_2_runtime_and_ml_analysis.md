# V24.2 runtime + ML/DL analysis — 2026-08-17

## Runtime integrity

Uploaded runtime ZIP SHA-256: `228e4236674bbcecd80fe15fba2c91c644d2f417f0210aa788a5d2a0aa94ddb8`.

- internal bundle SHA-256: 25/25 PASS;
- MetaEditor: 0 errors / 0 warnings;
- 3 chunks, 18 monthly resets;
- 26 candidates × 4 books;
- 56,437 virtual trades;
- 35,347 bar-feature rows;
- tester-only, native/external broker orders = 0.

## Strategy result — USD40 @1%

`router_ema_bos8` is the strongest provisional virtual candidate by median monthly return:

- median +6.9630%;
- mean +5.8681%;
- positive 15/18 months;
- >=10%: 3/18; >=15%: 2/18;
- worst -5.2668%; best +16.0437%;
- max MTM DD 9.1954%;
- mean AvgR ~0.1885;
- median trades 36/month;
- median turnover ~172.02x initial capital/month.

Frozen `ema_h1_base` control: median +6.3236%, mean +4.8389%, positive 13/18, max MTM DD 9.0171%, mean AvgR ~0.1700, median turnover ~149.29x.

Paired monthly `router_ema_bos8 - ema_h1_base` mean ~+1.03 percentage points/month, median ~+1.17 pp, positive in 10/18 months. Bootstrap 95% CI of the mean includes zero (~-0.26 to +2.35 pp), so this is promising but not statistically decisive.

Mechanism analysis indicates the router benefit is partly opportunity exclusion: BOS occupancy blocks some later EMA entries. Ledger filtering therefore cannot reproduce tick-level sequence effects.

## ML/DL result

Direct direction prediction remains weak. Generic all-bar directional classifiers/sequence models are near random OOS; enriched MT5 microstructure/MTF features modestly improve MLP/TCN but not enough to promote a direction oracle.

The productive target is future regime magnitude. LightGBM future 16-bar range/ATR monthly walk-forward rank correlation is positive in all 12 OOS months. Therefore ML moves to routing/abstention rather than direct Buy/Sell prediction.

## V25 gate

V25 freezes monthly walk-forward OOF LightGBM range-percentile scores for Aug-2025 → Jul-2026 and replays them inside MT5. Direction stays mechanical. Three controls plus nine ML regime routes are simulated tick-by-tick, one virtual position/book.

V25 is screening, not untouched confirmation, because route ideas were informed by V24.2 diagnostics. Any winner still requires forward/native/cost-fidelity validation.

REAL-MONEY LIVE TRADING remains forbidden.
