# V27 — Event-aware Economic Calendar analysis

Ngày: 2026-08-18.

## Recovered calendar bundle

- user upload SHA-256: `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`;
- internal manifest: 5/5 PASS;
- recovered run: `20260818_093825`;
- `calendar_values.csv`: 24,085 rows, ~5.72 MB;
- latest progress before watchdog: CNY, 80 chunks, 24,085 rows, last_error=0.

CSV QA found 68 rows where `event_name` contains an unescaped comma (`Average Weekly Earnings, Regular Pay y/y` etc.), producing 28 fields instead of the expected 27. These rows were repaired deterministically offline by rejoining the split `event_name`; no rows were dropped. Future exporter revisions must CSV-escape/quote text fields containing delimiters.

## Coverage used for event-aware modeling

The partial export contains major-calendar history through 2026-03-10 for USD/EUR/GBP/JPY, but some earlier 90-day chunks failed with calendar timeout. To avoid training through coverage gaps, the event-aware screening uses the continuous major-currency region from mid-2024 onward and tests Aug-2025 through Feb-2026.

Validation discipline:
- chronological expanding walk-forward;
- 16-hour purge before each monthly test;
- same causal M30 price/cross-asset feature construction for control and calendar variants;
- future 4h normalized range is the primary target;
- no random CV.

## Range-regime result

Seven monthly OOS folds Aug-2025 → Feb-2026:

- price/cross-asset baseline mean Spearman: ~0.5028;
- calendar-only mean Spearman: ~0.3676, positive 7/7 months;
- combined price + calendar mean Spearman: ~0.5285, positive 7/7 months;
- mean monthly uplift vs baseline: ~+0.0257 Spearman;
- combined beats baseline in all 7 tested months;
- paired t-test p ~0.0106 and Wilcoxon p ~0.0156, but n=7 and this is still screening, not final confirmation.

Top/bottom range discrimination:
- baseline bottom-20% realized future range ~2.16 ATR vs top-20% ~4.53 ATR, ratio ~2.16x;
- combined bottom-20% ~2.09 ATR vs top-20% ~4.56 ATR, ratio ~2.25x.

## What calendar information is actually useful

Ablation shows the uplift is overwhelmingly from **USD high-impact schedule/proximity**, not from actual/forecast surprise values:

- baseline + all schedule/proximity features: mean Spearman ~0.5269;
- baseline + USD schedule/proximity only: ~0.5278;
- baseline + non-USD schedule only: ~0.5004;
- baseline + actual/forecast surprise block: ~0.5008.

High-importance USD event proximity and count features (`minutes to/since`, events in next 2h/4h/8h/24h) are among the strongest event features. Therefore the calendar should primarily be treated as an ex-ante volatility/regime clock, not a direct macro-direction oracle.

## Direction result

Calendar does **not** improve stable direct direction prediction:
- baseline direction mean AUC ~0.5246;
- calendar-only ~0.5119;
- combined ~0.5171.

A small rank blend can move direction AUC only marginally (~0.5266 at a 30% calendar rank weight), which is not enough to hand Buy/Sell ownership to ML.

Decision remains: mechanical strategy families own direction; ML/calendar controls regime routing and abstention.

## Trade-ledger diagnostic

Joining the event-aware OOS range score to existing V24 strategy trades (USD40@1%) is screening only. It suggests family-specific routing rather than a blanket news blackout:

- EMA lowest event-aware range quintile has negative AvgR (~-0.13R), while mid quintiles are materially stronger;
- Trend high-range quintile deteriorates in this sample;
- BOS performs best in mid-range quintiles rather than monotonically at the highest score;
- simple `do not trade near news` is not supported: some entries within 60 minutes of a high-impact USD release remain strongly positive, while 1–4h pre-event windows can be weaker for EMA.

Do not turn these same-sample quintiles into production thresholds. They are hypothesis-generation only.

## Next gate

Freeze the event-aware **range/regime** architecture around USD schedule/proximity. Do not add surprise-heavy features or direct direction ownership. Any routing thresholds derived from these seven folds must be labeled screening and then replayed on later untouched calendar periods before promotion.

Safety invariant: REAL-MONEY LIVE TRADING = FORBIDDEN. No native broker orders. Stop-risk research ceiling remains 1.00%/trade.
