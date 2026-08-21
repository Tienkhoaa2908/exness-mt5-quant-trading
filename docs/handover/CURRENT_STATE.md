# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Research stop-risk ceiling: 1.00%/trade.
- Current V39 Stage A không launch MT5/MetaEditor và không có native/external broker-order path.
- PAPER/DEMO chỉ được xem xét sau safety/economic gates; LIVE vẫn cấm.
- Nếu sau này combine agents trên cùng symbol, aggregate stop-risk phải <=1.00%.

## Repository recovery state

`main` hiện là historical/stale line và không chứa chuỗi nghiên cứu V22→V39 mới nhất. Commit recovery source-of-truth trước V39 implementation là:

`97223ae7459ee401651b8e36d53f725854c79d3e` — `research: define V39 selective-harvest controller gate`.

Milestone V39 phải chạy từ branch `agent/v39-selective-harvest` sau khi release commit được chốt, không chạy từ `main` cũ.

## Accepted canonical data / model evidence

### V30 feature lake

Accepted source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Canonical M15 lake: 35,344 unique rows, 2025-02-01→2026-07-31, 136 raw fields, 0 duplicate timestamps. Causal availability rule:

`feature_available_time = bar_features.time + 15 minutes`

### V31.1 / V32

V31.1 ZIP SHA:
`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:
`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Feb-Jul 2026 continuous USD40:

| Mode | End USD | Geo/month | Max DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 |
| DeepMLP keep60 | 62.1444 | 7.6193% | 7.3639% | 153 | 0.3250R | 1.8326 |

DeepMLP keep60 remains frozen as risk-efficiency evidence; do not retune Feb-Jul 2026.

### V34 / V35

V34/V35 ZIP SHA:
`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted generated V34 source SHA:
`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

12-month continuous USD40 baseline:

- end USD107.43;
- 8.58% geometric/tháng;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

V35 generic all-expert router is rejected. SMC remains weak/high-turnover research-only specialist.

### V36 sequence-DL diagnostic

V36/V37 ZIP SHA:
`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Transformer48x2 chronological Feb-Jul means:

- future-delta Spearman +0.0403;
- final-R Spearman +0.5148;
- Hold AUC 0.6757;
- Protect AUC 0.6771;
- both AUC heads >0.5 in 6/6 months.

V36 is preserved as tail-state evidence. It is not PnL evidence by itself.

## Accepted V38 exact-MT5 evidence

Uploaded ZIP SHA-256:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Integrity/evidence:

- MetaEditor 0 errors / 0 warnings;
- V34 control reproduction PASS;
- 1,104 monthly rows = 12×23×4;
- 56,321 trades;
- summary↔ledger trade mismatch = 0;
- 260,471 M1 telemetry rows;
- baseline USD40 M1 coverage = 563/563 trades.

Primary continuous-USD40 comparison:

| Exit | End USD | Geo/month | DD | Trades | AvgR | Median hold |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 107.43 | 8.58% | 9.90% | 563 | 0.215R | 157.7m |
| TP 0.50R | 65.09 | 4.14% | 8.50% | 1069 | 0.056R | 41.6m |
| TP 0.75R | 90.13 | 7.00% | 9.42% | 880 | 0.109R | 64.9m |
| TP 1.00R | 104.42 | 8.32% | 10.23% | 750 | 0.158R | 94.4m |
| GB 0.25 after 0.75R | 96.65 | 7.63% | 10.11% | 831 | 0.133R | 70.7m |
| Velocity exit | 83.41 | 6.32% | 9.89% | 979 | 0.087R | 51.4m |
| Timebox 30m | 54.25 | 2.57% | 12.92% | 1388 | 0.028R | 30m |

Decision: all unconditional fast exits are rejected as production candidates. +1R is a promising decision zone but not a universal TP. Right-tail preservation is the current problem.

## Current milestone — V39 Selective Harvest Stage A

V39 Stage A is offline/read-only. It uses accepted V38 control telemetry and accepted V36 Transformer predictions.

Implemented contract:

- only evaluate states with current unrealized R >= +1.0R;
- M1 HistGradientBoosting models estimate giveback risk and tail continuation;
- M1 harvest score threshold comes from the trailing 2-month calibration 85th percentile;
- no test-month threshold tuning;
- V36 Transformer is an external tail veto, not retrained from OOS predictions;
- fusion requires `p_hold <= 0.15` and V36 state age <=75 minutes;
- first trigger per trade;
- false harvest of large winners is a first-class rejection metric.

Stage-A PASS requirements are bounded and diagnostic: >=4 folds, >=30 triggers, 3%-35% coverage, avoided-giveback positive in at least 75% of folds, positive mean avoided giveback, false-big-winner rate <=20%.

`STAGE_A_PASS` is permission to design Stage B only. It is not exact-MT5 PnL, not evidence of profitability, and does not authorize PAPER/DEMO/LIVE.

Primary files:

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

After every important run, upload one ZIP only. The bundle must contain `bundle_manifest_sha256.txt`; verify hashes/CRC with `scripts/analyze_mt5_research_bundle.py` or equivalent. Do not request screenshots if the ZIP already contains sufficient evidence.

## Decision stack

- Baseline `adaptive_ewma_hl8_thr0`: KEEP / control.
- DeepMLP keep60: KEEP frozen risk-efficiency evidence.
- V36 Transformer: KEEP sequence/tail-state evidence.
- SMC: KEEP research-only specialist lane.
- V35 generic router: REJECT.
- V37 generic SMC quality gate: REJECT / redesign.
- V38 universal fast exits: REJECT.
- +1R selective harvest decision zone: current V39 research lane.
- 15% geometric/month: aspirational and unmet. Never increase risk or curve-fit thresholds merely to force it.
