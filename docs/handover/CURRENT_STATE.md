# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Không tháo tester/live guards. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native/external broker order trong research screening.

## Canonical runtime/data state

V29/V30 giữ catalog 12 candidates × 4 virtual books và adaptive shadow-expert semantics. V30 `MlDlFeatureLakeV1.mq5` bổ sung M15 bar-feature export cho offline ML/DL; không ghi future labels trong EA và không có native broker-order path.

Accepted V30 source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Windows MetaEditor: `0 errors / 0 warnings`.

Final Git Bash acquisition ZIP SHA-256:
`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Canonical 18m lake after half-open trim/stitch:

- 35,344 M15 rows, 2025-02 → 2026-07;
- 136 raw V30 feature columns;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf in accepted raw lake;
- 864 monthly-summary rows = 18 × 12 × 4;
- 28,128 total ledger trades;
- 7,483 `norm10k_r0p5_continuous` trades;
- summary ↔ ledger counts exact; PnL/AvgR only CSV-rounding differences.

Adaptive state is continuous across all chunks. Final Chunk-3 expert obs counts:

- EMA 590
- MACD 251
- BOS 221
- Trend 360
- Slow momentum 612

No additional MT5 run is needed to analyze the accepted 18-month lake.

## Mandatory causal timing contract

CRITICAL: `bar_features.time` is the OPEN timestamp of `r[1]`, the just-closed M15 bar. The feature row is only available after that bar closes.

Offline ML must use:

`feature_available_time = bar_features.time + 15 minutes`

Trade entries may only join rows satisfying:

`feature_available_time <= entry_time`

Any experiment using raw `bar_features.time <= entry_time` without the +15-minute availability shift is INVALID.

Incomplete future-label horizons remain NaN; never coerce missing future returns to class 0.

## Strict causal ML/DL V2 protocol

12 OOS months: 2025-08 → 2026-07. Baseline: 5,066 norm-book candidate-trades, pooled AvgR 0.189049R, sumR 957.72205R.

For each test month:

- previous month = score-calibration month;
- train only on trades with `exit_time < calibration_month_start`;
- frozen model scores calibration month;
- threshold is derived from calibration **scores only**;
- absolute threshold is applied unchanged to next test month;
- no test-month quantile peeking;
- no random K-fold.

## Duplicate-opportunity confound

Norm-book 18m:

- 7,483 candidate-trades;
- only 1,972 unique `(entry_time, direction)` opportunities;
- mean multiplicity ~3.795;
- 79.31% of opportunity groups contain >1 candidate variant.

OOS 12m:

- 5,066 candidate-trades;
- 1,347 unique opportunities;
- mean multiplicity ~3.761;
- 79.29% duplicated.

Therefore unweighted catalog-trade ML numbers are exploratory only.

Inverse-opportunity-weighted ExtraTrees with a global threshold:

- 40%-keep target: actual coverage ~49.1%, selected AvgR ~0.250R, CI crosses zero;
- 50%-keep target: actual coverage ~58.6%, selected AvgR ~0.257R, sumR retention ~79.7%, paired-month CI roughly [+0.016R,+0.127R].

Unique-opportunity-group ExtraTrees/HistGB models all have paired-month CIs crossing zero. No universal common market-opportunity ML edge is established.

## Model decisions

- Win/loss/tail classification: REJECT.
- Static MLP: no robust uplift.
- GRU64: no robust uplift.
- causal TCN64: no robust uplift.
- Patch Transformer64: no robust uplift.
- Unweighted catalog ExtraTrees: not promotion evidence.
- Weighted expected-R tree filtering: promising but context-dependent, not promotion-ready.

DL capacity does not beat the stronger tabular controls on the accepted 18m lake.

## Family-threshold gate completed

A shared inverse-opportunity-weighted ExtraTrees model was calibrated by family from previous-month score distributions.

Candidate-aware aggregate:

- 40%-keep target: actual coverage 50.14%, selected AvgR 0.2758R, sumR retention 73.14%, paired-month CI [+0.0169R,+0.1640R].
- 50%-keep target: coverage 58.86%, selected AvgR 0.2523R, retention 78.56%, CI [+0.0005R,+0.1188R].
- 60%-keep target: coverage 64.49%, selected AvgR 0.2397R, retention 81.76%, CI [+0.0086R,+0.1054R].

Candidate-blind control fails robustness at all three thresholds; every paired-month interval crosses zero. Therefore the effect is not a clean universal market-state filter and depends partly on family/candidate context.

Family diagnostics:

- EMA pullback is the strongest current lead; its candidate-aware weighted family threshold is positive across 40/50/60 targets, with high sumR retention.
- Adaptive router is a secondary lead mainly at the tighter 40%-target gate.
- Router EMA+BOS is marginal/unstable.
- Slow momentum is not robust by month.
- MACD sample is too small/unstable despite some positive bootstrap slices.
- BOS/FVG and Trend20 do not clear a stable gate; BOS/FVG remains a useful negative/control family.

This family analysis reuses the same 12 OOS months already inspected. It is robustness evidence, **not fresh confirmation**.

## Current decision

V30 feature lake: ACCEPTED for offline research.

No ML/DL model is promoted to PAPER/DEMO execution. REAL-MONEY LIVE remains forbidden.

Stop tuning/slicing the same 2025-08 → 2026-07 OOS sample. More optimization on those months now increases research-overfitting risk.

The next meaningful gate is a genuinely fresh chronological holdout after 2026-08-01, with frozen model/threshold rules. A complete August-2026 month is preferable to a partial-month test because V30 `OnDeinit()` finalizes the active month and would create artificial EOM closes at a partial tester end date.

When a fresh full month is available:

1. train using only pre-July-label history according to the frozen monthly protocol;
2. use July scores to freeze the family thresholds;
3. apply unchanged rules to unseen August data;
4. report candidate-trade and unique-opportunity economics;
5. no re-tuning on August;
6. only if fresh holdout survives should a new MT5 strategy variant / tick-level re-simulation be justified.

## Evidence / code

- `docs/research/v30_18m_feature_lake_acceptance_and_first_ml.md`
- `docs/research/v30_causal_ml_dl_tournament_v2.md`
- `docs/research/v30_family_threshold_gate_v2.md`
- `docs/adr/ADR-038-causal-feature-availability-and-opportunity-weighting.md`
- `scripts/v30_causal_research_v2.py`
- `scripts/v30_trade_tournament_v2.py`
- `scripts/v30_sequence_tournament_v2.py`
- `scripts/v30_opportunity_weighting_v2.py`
- `scripts/v30_family_gate_v2.py`
- `tests/test_v30_causal_research_v2.py`

Local research QA at this checkpoint: Python compile PASS for the V30 offline utilities and `pytest` 5/5 PASS; one non-fatal PyTorch nested-tensor warning from the Transformer forward test.

Historical V29 compile/distribution incidents (`missing helpers`, `dt.minute -> dt.min`, stale/corrupt recovery blob) remain lessons learned; do not reintroduce those artifacts.
