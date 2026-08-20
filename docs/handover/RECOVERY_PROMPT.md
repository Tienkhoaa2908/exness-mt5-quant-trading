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
- Virtual candidate multiplicity is research only; later same-symbol combined risk must remain <=1.00% aggregate stop-risk.

## Canonical V30 data contract

Accepted V30 source SHA:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

Canonical lake = 35,344 unique M15 rows, 136 raw fields, 2025-02-01 through 2026-07-31.

Chunk stitching MUST be:

- chunk1 `[2025-02-01, 2025-08-01)`;
- chunk2 `[2025-08-01, 2026-02-01)`;
- chunk3 `[2026-02-01, 2026-08-01)`.

Trim each raw chunk before concatenation. Later chunks contain pre-roll rows.

Causal availability:

`feature_available_time = bar_features.time + 15 minutes`

All joins/inference use only features available by decision time.

## Accepted exact-MT5 milestones

V31.1 ZIP SHA:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:

`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Primary Feb-Jul 2026 continuous USD40:

- baseline `adaptive_ewma_hl8_thr0`: USD62.3573, 7.6807% geo/month, DD 10.8159%, 222 trades, 0.2401R AvgR, PF 1.5579;
- frozen DeepMLP keep60 challenger: USD62.1444, 7.6193% geo/month, DD 7.3639%, 153 trades, 0.3250R, PF 1.8326.

Freeze keep60 for genuinely fresh confirmation. Do not retune Feb-Jul 2026.

V34/V35 ZIP SHA:

`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted generated V34 source SHA:

`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

V34 12-month continuous USD40:

- adaptive baseline: USD107.432645, 8.58% geo/month, DD 9.90%, 563 trades, 0.215R, PF 1.501;
- SMC/ICT: USD66.83, 4.37%, DD 15.58%, 1,077 trades, 0.066R, PF 1.108;
- Price Action marginal;
- current Wyckoff and L1 microstructure proxies rejected.

SMC monthly-return correlation to baseline is low (~0.13), so it remains a potentially independent but weak/high-turnover specialist.

V35 generic all-expert AI router is REJECTED: USD24.49 end, -7.85% geo/month, DD 39.71%, -0.105R AvgR, PF 0.788, losses in 6/6 months.

## Accepted V36 / V37 diagnostics

Uploaded ZIP SHA:

`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

V36 Transformer48x2 chronological means:

- future-delta Spearman +0.0403;
- Hold AUC 0.6757;
- Protect AUC 0.6771;
- both AUCs >0.5 in 6/6 months.

Development-only clue: current R >= +1R and Transformer `p_hold <0.10` produced 603 first triggers; original final exits average 0.205R below trigger mark and 79.3% finish below it. This is not PnL evidence because an intervention changes subsequent path/state.

Preserve V36; do not discard the AI system.

V37 generic SMC quality filter is REJECTED/REDESIGN. Do not threshold-tune it on Feb-Jul.

## Current gate — V38 Fast Harvest Lab exact MT5

User strategy thesis: XAUUSD should not be treated as a long-hold stock problem. Preserve useful baseline/AI research but explicitly test faster impulse harvesting and lower time-in-market.

V38 is an incremental exit-only overlay on the accepted V34 source. All 17 V34 candidates stay present; the adaptive baseline remains the mandatory control. Six preregistered clones of `adaptive_ewma_hl8_thr0` change only exit timing:

1. TP +0.50R;
2. TP +0.75R;
3. TP +1.00R;
4. after MFE >=0.75R, close while profitable on 0.25R giveback;
5. after MFE >=0.50R, causal 60-second velocity-decay exit with current R >=0.25R;
6. hard 30-minute timebox.

Hard stop is processed before V38 fast exit. Existing V34 protection/TP remains active when a fast rule does not fire. Entry/router logic, 2ATR initial stop and risk fractions are unchanged.

Exact contract:

- XAUUSDm M15, Model=0 / Every Tick;
- 2025-08-01 through 2026-08-01;
- Deposit USD40, leverage 1:200;
- continuous USD40 decision book;
- accepted state-after-chunk1;
- tester-only, no native/external orders.

V38 must reproduce the accepted V34 control before any result is interpreted:

- 12 months;
- 563 control trades;
- final USD107.432645;
- exact accepted monthly control trade counts and monthly ending-capital path within CSV rounding tolerance.

V38 also exports causal `intra_trade_m1_fast.csv` for the untouched control path: current R/MFE/MAE/giveback, one-minute delta R, completed-minute tick count/imbalance, directional mid net move, tick-path/range and spread. Use this later to extend V36 into a short-horizon 5–15 minute continuation/decay AI; it does not replace V36.

Primary files:

- `scripts/build_v38_fast_harvest_source.py`
- `scripts/analyze_v38_fast_harvest_mt5.py`
- `tests/test_v38_fast_harvest_static.py`
- `runtime/v38_fast_harvest/RUN_V38_FAST_HARVEST_EXACT_MT5_GIT_BASH.sh`
- `runtime/v38_fast_harvest/BOOTSTRAP_V38_FAST_HARVEST_ONE_SHOT_GIT_BASH.sh`
- `docs/research/v38_fast_harvest_lab_plan.md`

Local pre-Windows QA produced deterministic V38 generated-source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12` twice from the accepted V34 source; Python compile, 3 static tests, generated-MQL lint and Bash syntax checks passed locally. This is NOT Windows MetaEditor/runtime evidence. The runner intentionally double-builds instead of relying on a stale hardcoded V38 hash.

## Historical runner lessons

Do not reintroduce:

- stale hardcoded source hashes after generator changes;
- Python-to-MQL raw-string/backslash bugs;
- lint false positives on escaped backslashes;
- UTF-16 MetaEditor-log decoding failures;
- Bash `set -u` dependent-local declarations such as `local tag=... dest="$CP/$tag"`;
- MSYS path-conversion errors;
- rerunning MT5 after `MT5_DONE.txt` exists; collection/analysis recovery must be checkpointed.

Aspirational 15% geometric/month remains unmet. Never raise stop-risk above 1.00% merely to force the target.
