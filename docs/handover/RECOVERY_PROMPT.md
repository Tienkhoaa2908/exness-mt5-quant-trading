# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch: `agent/v30-ml-dl-feature-lake`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale/uncontrolled grid/doubling after loss.
- Không commit login/password/token/secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Accepted V30 runtime/data

V30 `MlDlFeatureLakeV1.mq5` keeps the frozen 12-candidate × 4-book virtual catalog and exports M15 bar features for offline research. No future labels in EA; no native/external broker-order path.

Source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows compile: `0 errors / 0 warnings`.

Final acquisition ZIP SHA-256:
`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Canonical 18m lake:

- 35,344 M15 bars, 2025-02 → 2026-07;
- 136 raw fields;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in accepted raw lake;
- 864 monthly-summary rows;
- 28,128 total ledger trades;
- 7,483 norm-book trades.

Adaptive state is continuous. Final obs: EMA 590, MACD 251, BOS 221, Trend 360, Slow 612.

## CRITICAL causal timing rule

`bar_features.time` is the OPEN time of the just-closed M15 bar, not the availability timestamp.

Always use:

`feature_available_time = bar_features.time + 15 minutes`

Trade entries may only join rows with:

`feature_available_time <= entry_time`

Any experiment ignoring the +15-minute shift is INVALID.

Incomplete future-label horizons remain NaN; never map missing future returns to class 0.

## Strict monthly protocol

OOS research months: 2025-08 through 2026-07.

For each test month:

1. previous month = score-calibration month;
2. model fit only on trades with `exit_time < calibration_month_start`;
3. frozen model scores calibration month;
4. threshold uses calibration scores only;
5. apply absolute threshold unchanged to next test month;
6. no test-month quantile peeking;
7. no random K-fold.

## Duplicate-opportunity rule

Norm book is heavily duplicated across candidate variants.

18m: 7,483 candidate-trades -> 1,972 unique `(entry_time,direction)` groups, mean multiplicity ~3.795, 79.31% duplicated.

12m OOS: 5,066 candidate-trades -> 1,347 unique groups, mean multiplicity ~3.761, 79.29% duplicated.

Unweighted candidate-trade metrics are exploratory only.

Promotion claims require inverse group-multiplicity weighting and/or unique-opportunity fitting/evaluation.

## Current model decisions

- Win/loss/tail classification: REJECT.
- Static MLP: no robust uplift.
- GRU/TCN/PatchTransformer: no robust uplift; do not escalate DL.
- Unweighted ExtraTrees: not promotion evidence.
- Global inverse-opportunity-weighted ExtraTrees: weaker positive lead only around 50%-keep; not promotion-ready.
- Unique-opportunity ExtraTrees/HistGB: CIs cross zero; no universal common-state ML edge.

## Family-threshold gate — completed

Shared inverse-opportunity-weighted ExtraTrees with previous-month family score thresholds:

Candidate-aware:

- 40%-keep target: coverage 50.14%, selected AvgR 0.2758R, sumR retention 73.14%, paired-month CI [+0.0169R,+0.1640R].
- 50%-keep: coverage 58.86%, selected AvgR 0.2523R, retention 78.56%, CI [+0.0005R,+0.1188R].
- 60%-keep: coverage 64.49%, selected AvgR 0.2397R, retention 81.76%, CI [+0.0086R,+0.1054R].

Candidate-blind control: all 40/50/60 paired-month intervals cross zero. Therefore the stronger signal depends partly on family/candidate context and is not a universal market-state filter.

Family interpretation:

- EMA pullback = strongest current lead across 40/50/60 thresholds.
- Adaptive router = secondary lead mainly at 40% target.
- Router EMA+BOS = marginal/unstable.
- Slow momentum = not robust by month.
- MACD = too small/unstable despite some positive slices.
- BOS/FVG and Trend20 = no stable family gate; BOS/FVG remains negative/control family.

Important: these family hypotheses were inspected on the same 12 OOS months. They are robustness evidence, not fresh confirmation.

## Next action

Do not continue tuning/slicing 2025-08 → 2026-07. That now increases research-overfitting risk.

Next meaningful evidence must be a **fresh chronological holdout after 2026-08-01** with the procedure frozen before looking at its outcomes.

Prefer a complete August-2026 month. Do not use a partial-month Strategy Tester result as promotion evidence because V30 `OnDeinit()` calls `FinalizeMonth()` and would create artificial EOM closes at the test end. A partial month may only be a diagnostic with forced-EOM trades excluded and its resulting adaptive state discarded.

For full fresh holdout:

1. keep the V30 state-after-July checkpoint as the starting state;
2. use only pre-July-label history to fit according to the frozen protocol;
3. use July scores to freeze family thresholds;
4. run unseen August without re-tuning;
5. evaluate both candidate-trade and unique-opportunity economics;
6. if fresh August fails, reject the current family filter hypothesis;
7. if it passes, still require additional fresh evidence/tick-level re-simulation before PAPER/DEMO;
8. LIVE remains forbidden.

## Read first on recovery

- `docs/handover/CURRENT_STATE.md`
- `docs/research/v30_18m_feature_lake_acceptance_and_first_ml.md`
- `docs/research/v30_causal_ml_dl_tournament_v2.md`
- `docs/research/v30_family_threshold_gate_v2.md`
- `docs/adr/ADR-031-ml-dl-feature-lake-before-model-escalation.md`
- `docs/adr/ADR-038-causal-feature-availability-and-opportunity-weighting.md`
- `scripts/v30_causal_research_v2.py`
- `scripts/v30_trade_tournament_v2.py`
- `scripts/v30_sequence_tournament_v2.py`
- `scripts/v30_opportunity_weighting_v2.py`
- `scripts/v30_family_gate_v2.py`
- `tests/test_v30_causal_research_v2.py`

Historical V29 incidents remain lessons learned only: missing helpers, `dt.minute -> dt.min`, stale/corrupt recovery bundles. Do not reintroduce broken historical artifacts.
