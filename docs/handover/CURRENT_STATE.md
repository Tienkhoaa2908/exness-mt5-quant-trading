# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-20.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Không tháo tester/live guards. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native/external broker order trong research screening.

## Canonical strategy/runtime state

V29/V30 giữ catalog 12 candidates × 4 virtual books và adaptive shadow-expert semantics. V30 `MlDlFeatureLakeV1.mq5` bổ sung bar-level feature export cho offline ML/DL; không ghi future labels trong EA và không có native broker-order path.

Windows evidence cho V30 source SHA-256:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

MetaEditor compile gate đã PASS `0 errors / 0 warnings`.

Git Bash runtime hoàn tất hai chunk còn thiếu và đóng bundle thành công. Uploaded result ZIP SHA-256:

`8771ae988be46191c724e74f3a84b76b1bc7a0385a703ef963dee95414cdbb4a`

Không cần chạy MT5 thêm cho nghiên cứu 18 tháng hiện tại.

## V30 18-month feature-lake acceptance

Canonical trim dùng half-open interval cho ba chunk:

- `[2025-02-01, 2025-08-01)`
- `[2025-08-01, 2026-02-01)`
- `[2026-02-01, 2026-08-01)`

Mỗi raw chunk có đúng một pre-roll bar trước FromDate; row này được trim offline.

Accepted lake:

- 35,344 M15 rows, 18 tháng 2025-02 → 2026-07;
- 136 raw V30 feature columns;
- 0 duplicate timestamps;
- 0 NaN / 0 Inf trong canonical raw lake;
- 864 monthly-summary rows = 18 × 12 × 4;
- 28,128 trade-ledger rows;
- 7,483 trades trong `norm10k_r0p5_continuous`;
- summary ↔ ledger trade/win/loss counts khớp tuyệt đối;
- PnL/AvgR chỉ lệch cỡ 1e-6 do CSV rounding.

Expected constants/non-informative fields gồm `real_volume=0`, readiness flags luôn 1, `bb_rsi_dir=0`; không coi là corruption nhưng phải exclude khỏi model.

## Adaptive-state continuity

Observation counts:

Chunk 1:
- EMA 181
- MACD 79
- BOS 69
- Trend 108
- Slow momentum 210

After Chunk 2:
- EMA 393
- MACD 216
- BOS 184
- Trend 279
- Slow momentum 416

After Chunk 3:
- EMA 590
- MACD 251
- BOS 221
- Trend 360
- Slow momentum 612

Replay trade ledger qua EWMA equations khớp obs 100%; EWMA values chỉ lệch tối đa khoảng 1.9e-6 vì `r_multiple` trong CSV bị round.

## Mandatory causal timing contract

CRITICAL: `bar_features.time` là OPEN timestamp của `r[1]`, bar M15 vừa đóng. Row đó chỉ available khi bar đóng/next bar bắt đầu.

Offline ML phải dùng:

`feature_available_time = bar_features.time + 15 minutes`

Trade entry chỉ được join row có:

`feature_available_time <= entry_time`

Mọi ML/DL experiment join trực tiếp `bar_features.time <= entry_time` mà không +15 phút là INVALID.

Offline future labels cũng phải giữ NaN khi horizon chưa đủ; không được biến missing future return thành class 0.

## Strict causal ML/DL V2 gate

12 OOS months: 2025-08 → 2026-07, baseline 5,066 norm-book candidate-trades, pooled baseline AvgR 0.189049R.

Walk-forward contract:

- tháng trước test là score-calibration month;
- model fit chỉ dùng trades có `exit_time` trước calibration-month start;
- frozen model score calibration month;
- threshold lấy từ calibration scores, không dùng calibration labels để tune threshold;
- absolute threshold apply cho test month kế tiếp;
- không test-month quantile peeking, không random K-fold.

### Tabular findings

Engineered expert-state + market/trade context giúp ExtraTrees/HistGradientBoosting ở catalog-trade level. Unweighted ExtraTrees candidate-aware ban đầu cho selected AvgR ~0.289R ở ~43% coverage với paired-month CI > 0.

Nhưng đây KHÔNG phải promotion evidence vì duplicate-opportunity confound rất lớn.

### Duplicate-opportunity confound

Norm-book 18m:

- 7,483 candidate-trades;
- chỉ 1,972 unique `(entry_time, direction)` opportunities;
- mean multiplicity ~3.795;
- 79.31% opportunity groups có >1 candidate variant.

OOS 12m:

- 5,066 candidate-trades;
- 1,347 unique opportunities;
- mean multiplicity ~3.761;
- 79.29% groups duplicated.

Inverse `(entry_time,direction)` multiplicity weighting làm apparent ExtraTrees edge yếu đi đáng kể:

- 40%-keep calibration target: actual coverage ~49.1%, selected AvgR ~0.250R, CI crosses zero;
- 50%-keep target: actual coverage ~58.6%, selected AvgR ~0.257R, sumR retention ~79.7%, paired-month CI khoảng [+0.016R,+0.127R].

Unique-opportunity-group ExtraTrees/HistGB models đều có paired-month CI crossing zero. Vì vậy hiện chưa có bằng chứng đủ mạnh cho universal common market-opportunity ML gate.

### Model decisions

- Win/loss/tail classification: REJECT.
- Static MLP: no robust uplift.
- GRU64: no robust uplift.
- causal TCN64: no robust uplift.
- Patch Transformer64: no robust uplift.
- Unweighted catalog ExtraTrees: exploratory only, not promotable.
- Inverse-opportunity-weighted expected-R: promising but weak/family-dependent, not promotion-ready.

DL capacity không giải quyết được robustness problem trên 18m lake hiện tại.

## Family-specific clue

Weighted 50%-target diagnostics cho thấy response không đồng nhất:

- EMA `ema_h1_skip20`: positive lead;
- `router_ema_bos8`: positive lead;
- `slow_mom_timebox`: positive lead;
- `adaptive_ewma_hl8_thr0`: smaller positive lead;
- BOS/FVG degrades under same filter and phải được giữ làm negative/control family.

Không được áp một universal filter cho mọi family.

## Current decision / next gate

V30 feature lake: ACCEPTED cho offline research.

Không có model nào được promote sang PAPER/DEMO hay live execution. LIVE luôn forbidden.

Next gate hoàn toàn offline:

1. family-specific expected-R filtering;
2. inverse opportunity-multiplicity weighting bắt buộc;
3. same frozen previous-month score-calibration protocol;
4. explicit negative-control/exclusion check cho BOS/FVG;
5. report coverage, AvgR, sumR retention, worst month, bootstrap uplift và opportunity breadth theo family.

Chỉ nếu family-specific gate survive mới justify một MT5 tick-level re-simulation mới. Hiện tại user không cần chạy thêm MT5.

## Evidence/docs

- `docs/research/v30_18m_feature_lake_acceptance_and_first_ml.md`
- `docs/research/v30_causal_ml_dl_tournament_v2.md`
- `docs/adr/ADR-038-causal-feature-availability-and-opportunity-weighting.md`

Historical V29 compile/distribution incidents (`missing helpers`, `dt.minute -> dt.min`, stale/corrupt recovery blob) vẫn là lessons learned; không reuse historical broken artifacts.
