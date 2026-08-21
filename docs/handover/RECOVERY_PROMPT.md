# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Branch / source of truth

`main` đang stale so với chuỗi nghiên cứu mới. Recovery source-of-truth trước V39 implementation là commit:

`97223ae7459ee401651b8e36d53f725854c79d3e`

Current milestone phải tiếp tục từ branch `agent/v39-selective-harvest` sau khi V39 release commit được chốt. Không phát triển V39 trên `main` cũ.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Stop-risk research ceiling <=1.00%/trade.
- V39 Stage A không launch MT5/MetaEditor và không có native/external order path.
- PAPER/DEMO chỉ sau gates; LIVE vẫn cấm.
- Không tăng risk hoặc sweep threshold chỉ để ép 15% geometric/tháng.

## Canonical evidence cần giữ

V30 accepted source SHA:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

V32 ZIP SHA:
`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

V34/V35 ZIP SHA:
`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted V34 source SHA:
`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

V36/V37 ZIP SHA:
`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

V38 exact-MT5 ZIP SHA:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

## Accepted V38 result

V38 PASS evidence:

- MetaEditor 0 errors / 0 warnings;
- V34 control reproduction PASS;
- 1,104 monthly rows = 12×23×4;
- 56,321 trades;
- summary↔ledger trade mismatch 0;
- 260,471 M1 telemetry rows;
- baseline USD40 M1 coverage 563/563.

12-month baseline: USD107.43 end, 8.58% geometric/tháng, DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501.

Unconditional fast exits are rejected. TP1R is close to baseline but cuts right-tail trends. +1R is retained only as selective decision zone.

## Accepted V36 clue

Transformer48x2 chronological Feb-Jul means:

- Hold AUC 0.6757;
- Protect AUC 0.6771;
- both >0.5 in 6/6 months.

Preserve V36 as sequence/tail-state evidence; do not relabel/retrain its accepted OOS predictions to improve V39 headline metrics.

## Current gate — V39 Selective Harvest Stage A

Research question: after a control trade is already around +1R, can a causal controller identify giveback-prone winners while preserving large trend winners?

Implemented Stage A contract:

- read-only/offline;
- accepted V38 control M1 telemetry only;
- decision zone current R >= +1.0R;
- M1 model predicts giveback risk and tail continuation;
- threshold from trailing 2-month calibration 85th percentile;
- no test-month threshold tuning;
- V36 Transformer used as external tail veto: `p_hold <=0.15`, age <=75m;
- first trigger per trade;
- false-big-winner rate is a hard promotion metric.

Stage-A pass requires at least 4 chronological folds, >=30 triggers, 3%-35% coverage, positive avoided giveback in >=75% folds, positive mean avoided giveback and false-big-winner rate <=20%.

`STAGE_A_PASS` is diagnostic only. It does not claim PnL/profitability and only permits design of a frozen Stage B exact-MT5 test.

## Current files

- `scripts/v39_selective_harvest_stage_a.py`
- `tests/test_v39_selective_harvest_static.py`
- `runtime/v39_selective_harvest/RUN_V39_SELECTIVE_HARVEST_STAGE_A_GIT_BASH.sh`
- `runtime/v39_selective_harvest/BOOTSTRAP_V39_SELECTIVE_HARVEST_ONE_SHOT_GIT_BASH.sh`
- `scripts/package_mt5_research.py`
- `scripts/package_mt5_research.cmd`
- `scripts/analyze_mt5_research_bundle.py`
- `docs/research/v39_selective_harvest_plan.md`
- `docs/adr/ADR-039-selective-harvest-stage-a-before-exact-mt5.md`

## One run -> one ZIP

V39 runner phải tự verify inputs/safety, chạy Stage A, tạo `V39_EVIDENCE.txt`, `bundle_manifest_sha256.txt` và duy nhất `v39_selective_harvest_stage_a.zip`.

Sau upload, verify bundle bằng `scripts/analyze_mt5_research_bundle.py` hoặc phân tích tương đương. Nếu evidence trong ZIP đủ thì không yêu cầu screenshot riêng.

## Historical runner lessons

Không reintroduce stale hardcoded generated-source hashes, Python→MQL escaping bugs, UTF-16 MetaEditor log decode failures, MSYS path conversion errors hoặc rerun tester sau checkpoint completion.
