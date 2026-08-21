# V40 Upgrade Campaign — First-Passage Monetization + Upgrade Audit

Ngày thiết kế: 2026-08-21.

## Mục tiêu

V40 là Stage A offline/read-only để nghiên cứu các mảng còn có thể nâng cấp mà không phá accepted baseline:

1. sửa target exit sau +1R từ eventual-giveback sang first-passage event order;
2. so sánh hai action bảo vệ profit không tạo thêm entry/turnover;
3. audit source/direction stability để tìm lane nghiên cứu tiếp theo, không dùng làm production filter trên cùng sample;
4. audit calibration V36 Transformer;
5. giữ V32 DeepMLP keep60 như frozen risk-efficiency benchmark;
6. xuất exact baseline, calibrated shadow economics và khoảng cách tới 15%/tháng trong cùng bundle.

## Source of truth

- Accepted V38 exact-MT5 ZIP SHA: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
- Accepted V39 Stage-A ZIP SHA: `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`.
- V39 accepted result: `STAGE_A_HOLD`.
- Exact 12-month control: start $40, end $107.43, geometric/month 8.58%, max DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501.
- 15% geometric/month remains aspirational; equivalent 12-month $40 target is about $214.01.

## Primary target redesign

Decision zone remains `unrealized_r >= +1.0R`.

From each current M1 state define two competing future barriers:

- `GIVEBACK_FIRST`: price first reaches `current_R - 0.25R`;
- `TAIL_FIRST`: price first reaches `max(current_R + 0.75R, +2.0R)`;
- `CENSORED`: neither barrier is reached before the baseline exit.

Primary model: `HistGradientBoostingClassifier`, binary training on resolved `GIVEBACK_FIRST` vs `TAIL_FIRST`.

Causal feature set uses only current/past M1 telemetry and rolling deltas. No future feature enters the model.

Chronology:

- train: resolved states whose trade exited before calibration start;
- calibration: trailing 2 calendar months before test, resolved and fully exited before test;
- test: one calendar month;
- score threshold: fixed 80th percentile of calibration `P(GIVEBACK_FIRST)`;
- no test-month threshold tuning.

## Actions

Primary action: `STATIC_PROTECT_0.25R`.

When first signal fires, do not exit immediately; set a static protective floor at `trigger_R - 0.25R` and keep the baseline exit if the floor is never hit.

Secondary structural action: `SELECTIVE_TRAIL_0.25R`.

When first signal fires, activate a 0.25R trailing giveback floor from the running post-trigger peak. It adds no entry and does not change initial risk.

`IMMEDIATE` is retained only as a diagnostic comparator, not the intended promotion action.

## Stage-A gate

Primary action may be promoted only to a frozen exact-MT5 Stage B design if all conditions hold:

- >=5 chronological folds;
- >=30 unique first triggers;
- 5%-35% trigger coverage;
- mean resolved giveback-vs-tail AUC >=0.60;
- GIVEBACK_FIRST rate among triggers >=60%;
- TAIL_FIRST trigger rate <=25%;
- static-protect shadow delta positive in >=4 test months;
- total static-protect shadow delta R >0.

No source/direction filter, score quantile, barrier or risk sweep on the same sample may be used to force a PASS.

## Economics reporting

Three layers must stay separate:

1. **Exact accepted baseline**: $40 -> $107.43, 8.58% geo/month, DD 9.90%.
2. **Calibrated shadow policy**: V40 trade-level R path revalued with one risk scale calibrated so baseline shadow exactly reproduces $107.43. This is a ranking/projection tool only.
3. **Aspirational target**: 15% geometric/month, about $214.01 from $40 over 12 months.

A shadow result is never called exact-MT5 PnL.

## Frozen / diagnostic lanes

- V32 DeepMLP keep60 remains frozen: near-same return with materially lower DD and turnover on Feb-Jul 2026; do not retune.
- V36 Transformer remains sequence-state evidence and is audited for probability calibration, not retrained into V40 primary target.
- Source/direction segments are diagnostic only; no production gating from this development sample.
- SMC remains research-only specialist.

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Stage A does not launch MT5 or MetaEditor and cannot send broker orders.
- No Martingale, uncontrolled grid or loss-doubling.
- Research stop-risk ceiling remains <=1.00%/trade.
- V40 actions add zero entries and do not increase initial risk.

## One run -> one ZIP

Runner output: `runtime/v40_upgrade_campaign/OUTPUT_V40_STAGE_A/v40_upgrade_campaign_stage_a.zip`.

Bundle contains summary, folds, triggers, trade-level shadow, action metrics, monthly action metrics, segment metrics, V36 calibration, evidence, source/test copies and `bundle_manifest_sha256.txt`.
