# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch at this checkpoint: `agent/v30-ml-dl-feature-lake`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/uncontrolled grid/doubling after loss.
- Không commit login/password/token/secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Current accepted runtime/data state

V30 `MlDlFeatureLakeV1.mq5` keeps the frozen 12-candidate × 4-book V29/V30 virtual catalog and exports a causal M15 feature lake for offline research. It has no future labels in the EA and no native/external broker-order path.

Accepted V30 source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows MetaEditor evidence: `0 errors / 0 warnings`.

Final Git Bash data-acquisition ZIP SHA-256:
`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

No additional MT5 run is required for the current offline gate.

## Canonical 18-month lake

Three half-open chunks:

- `[2025-02-01, 2025-08-01)`
- `[2025-08-01, 2026-02-01)`
- `[2026-02-01, 2026-08-01)`

After canonical trim/stitch:

- 35,344 M15 bars;
- 136 raw V30 feature fields;
- 18 months, 2025-02 through 2026-07;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in the accepted raw lake;
- 864 monthly-summary rows;
- 28,128 total trade-ledger rows;
- 7,483 `norm10k_r0p5_continuous` trades.

Summary ↔ ledger counts match; PnL/AvgR differences are only CSV-rounding scale.

Adaptive-state continuity is accepted. Final expert observation counts after Chunk 3:

- EMA 590
- MACD 251
- BOS 221
- Trend 360
- Slow momentum 612

## CRITICAL causal timing rule

Do not join ML samples using raw `bar_features.time <= entry_time`.

The EA exports `r[1]` and stamps it with that closed bar's OPEN time. Therefore:

`feature_available_time = bar_features.time + 15 minutes`

Trade entries may use only feature rows satisfying:

`feature_available_time <= entry_time`

Any prior or future experiment that ignores this +15-minute availability shift is INVALID.

Incomplete future-label horizons must remain NaN; never coerce missing future returns into class 0.

## Strict monthly ML protocol

OOS months: 2025-08 through 2026-07 after six-month warm-up.

For each test month:

1. previous month = score-calibration month;
2. train only on trades whose `exit_time` is before calibration-month start;
3. fit frozen model;
4. score calibration month;
5. choose threshold from calibration **scores only**;
6. apply absolute threshold unchanged to next test month;
7. no test-month quantile peeking;
8. no random K-fold.

Economic OOS metrics, turnover/opportunity breadth and drawdown/tail diagnostics matter more than AUC.

## Duplicate-opportunity rule — MUST NOT IGNORE

The norm-book catalog contains heavy repeated opportunities.

Full 18 months:

- 7,483 candidate-trades;
- 1,972 unique `(entry_time,direction)` opportunity groups;
- mean multiplicity ~3.795;
- 79.31% groups duplicated.

OOS 12 months:

- 5,066 candidate-trades;
- 1,347 unique groups;
- mean multiplicity ~3.761;
- 79.29% duplicated.

Therefore unweighted candidate-trade ML metrics are exploratory only.

Before any promotion claim, require at least one of:

- inverse `(entry_time,direction)` multiplicity sample weighting; or
- unique-opportunity-group fitting/evaluation.

A universal market-opportunity model must survive the unique-opportunity control.

## Current model decisions

- Win/loss/tail classification: REJECT.
- Static MLP: no robust economic uplift.
- GRU64: no robust uplift.
- causal TCN64: no robust uplift.
- Patch Transformer64: no robust uplift.
- Unweighted ExtraTrees on engineered state: attractive catalog-level numbers but NOT promotion evidence because duplication materially amplifies results.
- Inverse-opportunity-weighted ExtraTrees: weaker signal. Around a 50%-keep calibration target, actual coverage ~58.6%, selected AvgR ~0.257R vs 0.189R baseline, sumR retention ~79.7%, paired-month CI remains slightly positive. Still not promotion-ready.
- Unique-opportunity common-state ExtraTrees/HistGB: paired-month CIs cross zero; no universal ML edge established.

## Next action

Do **not** ask the user to run MT5 now.

Next gate is offline family-specific expected-R research:

- inverse opportunity-multiplicity weighting mandatory;
- same strict previous-month frozen-score calibration;
- evaluate EMA, router and slow-momentum positive leads separately;
- keep BOS/FVG as negative/control family because current weighted filter degrades it;
- report per-family coverage, AvgR, sumR retention, worst month, paired-month bootstrap and opportunity breadth;
- reject any family whose uplift is not robust or whose turnover/drawdown tradeoff is worse.

Only if the family-specific gate survives should a new MT5 tick-level re-simulation be built. PAPER/DEMO only after gates. LIVE remains forbidden.

## Read first on recovery

- `docs/handover/CURRENT_STATE.md`
- `docs/research/v30_18m_feature_lake_acceptance_and_first_ml.md`
- `docs/research/v30_causal_ml_dl_tournament_v2.md`
- `docs/adr/ADR-031-ml-dl-feature-lake-before-model-escalation.md`
- `docs/adr/ADR-038-causal-feature-availability-and-opportunity-weighting.md`

Historical V29 incidents remain relevant only as stale-artifact/compile lessons: missing helpers, `dt.minute -> dt.min`, and corrupt/stale recovery bundles must not be reintroduced.
