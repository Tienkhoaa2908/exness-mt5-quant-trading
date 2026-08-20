# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Primary research branch: `agent/v30-ml-dl-feature-lake`.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Do not remove tester/live guards.
- No Martingale/uncontrolled grid/loss doubling.
- Do not commit/request credentials or secrets.
- No native/external broker orders in current research gates.
- Research stop-risk ceiling: 1.00%/trade.
- PAPER/DEMO only after gates; LIVE remains forbidden.

## Canonical V30 data contract

Accepted V30 source SHA:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Canonical lake = 35,344 unique M15 rows, 136 raw fields, 2025-02-01 through 2026-07-31.

Chunk stitching MUST be:

- chunk1 `[2025-02-01, 2025-08-01)`;
- chunk2 `[2025-08-01, 2026-02-01)`;
- chunk3 `[2026-02-01, 2026-08-01)`.

Trim each raw chunk before concatenation. Do not globally concatenate raw chunks because later chunks contain pre-roll rows.

Causal availability rule:

`feature_available_time = bar_features.time + 15 minutes`

Every entry/current-bar/telemetry join must use only `feature_available_time <= decision_time`.

## Accepted exact-MT5 milestones

V31.1 ZIP SHA:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Primary Feb-Jul 2026 continuous USD40:

- baseline `adaptive_ewma_hl8_thr0`: USD62.3573, 7.6807% geo/month, DD 10.8159%, 222 trades, 0.2401R AvgR, PF 1.5579;
- frozen DeepMLP keep60 challenger: USD62.1444, 7.6193% geo/month, DD 7.3639%, 153 trades, 0.3250R, PF 1.8326.

Freeze keep60 for fresh confirmation. Do not retune Feb-Jul 2026.

V34/V35 ZIP SHA:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

V34 12-month continuous USD40:

- adaptive baseline: USD107.43, 8.58% geo/month, DD 9.90%, 563 trades, 0.215R, PF 1.501;
- SMC/ICT: USD66.83, 4.37%, DD 15.58%, 1,077 trades, 0.066R, PF 1.108;
- Price Action marginal;
- current Wyckoff and L1 microstructure proxies rejected.

SMC monthly-return correlation to the adaptive baseline is low (~0.13), so it remains a potentially independent but weak/high-turnover specialist.

V35 generic all-expert AI router is REJECTED: USD24.49 end, -7.85% geo/month, DD 39.71%, -0.105R AvgR, PF 0.788, losses in 6/6 months.

## Accepted V36 / V37 read-only diagnostics

Uploaded ZIP SHA:

`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Read `docs/research/v36_v37_results.md`.

### V36 sequence DL

Chronological Feb-Jul 2026 means:

| Model | Future-delta Spearman | Hold AUC | Protect AUC |
|---|---:|---:|---:|
| GRU48 | +0.0187 | 0.6426 | 0.6150 |
| causal TCN48 | -0.0116 | 0.6152 | 0.5524 |
| **Transformer48x2** | **+0.0403** | **0.6757** | **0.6771** |

Direct future-delta regression remains weak. Transformer binary sequence heads are stable and both AUCs exceed 0.5 in all six months.

Development-only first-trigger clue: when current unrealized R >= +1.0R and Transformer `p_hold < 0.10`, 603 first triggers occur; original final exit averages 0.205R below trigger mark, 79.3% finish below trigger mark, and mean avoided giveback is positive in all six inspected months. This is not PnL evidence; exact MT5 intervention is required.

### V37 SMC quality filter

Current generic keep60-style SMC filter is REJECTED/REDESIGN:

- HistGB and ExtraTrees reduce AvgR and sumR;
- MLP gives only tiny mean AvgR uplift and retains too little SMC sumR with unstable months.

Do not send current V37 to MT5 and do not threshold-tune the same score on Feb-Jul.

## Current next gate — V38 exact-MT5 neural exit protection

Build one bounded development gate around the sequence classification signal:

- no entry-risk increase;
- act only after a position is already >= +1R unrealized;
- low Transformer hold probability triggers a bounded profit-protection/exit hypothesis;
- exact MT5 continuous USD40 is final judge;
- no offline subset-PnL reconstruction;
- any development winner must be frozen before a genuinely fresh holdout.

MQL5 has native ONNX support and can validate ONNX models in Strategy Tester, so prefer tester-side inference or an equally causal in-EA implementation rather than replaying static baseline decisions after intervention changes path/state.

## Historical runner lessons

Do not reintroduce:

- stale hardcoded source hashes after generator changes;
- Python-to-MQL raw-string/backslash bugs;
- lint false positives on escaped backslashes;
- UTF-16 MetaEditor-log decoding failures;
- Bash `set -u` dependent-local declarations such as `local tag=... dest="$CP/$tag"`;
- MSYS path-conversion errors;
- collection reruns after `MT5_DONE.txt` exists.

Aspirational 15% geometric/month remains unmet. Never raise stop-risk above 1.00% merely to force the target.
