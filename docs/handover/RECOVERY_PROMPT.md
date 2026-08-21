# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Source of truth

Do not reconstruct state from memory when GitHub/evidence disagree.

Current branch:
`agent/v40-upgrade-campaign`

Base accepted V39 commit:
`a28146448c4cf8020e6fa1147e39d97506fa08e6`

Windows recovery:

`git fetch --no-tags origin "+refs/heads/agent/v40-upgrade-campaign:refs/remotes/origin/agent/v40-upgrade-campaign"`

`git checkout -B agent/v40-upgrade-campaign refs/remotes/origin/agent/v40-upgrade-campaign`

Do not use `git clean`; accepted V36/V38 runtime outputs and Python environments may be untracked.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk <=1.00%/trade.
- No Martingale, uncontrolled grid or doubling after loss.
- Do not remove tester/live guards.
- V40 Stage A is offline/read-only and launches no MT5/MetaEditor.
- Do not tune risk merely to force 15% geometric/month.

## Canonical evidence

- V30 source SHA:
  `4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`
- V31.1 ZIP:
  `7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`
- V32 ZIP:
  `3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`
- V34/V35 ZIP:
  `ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`
- V34 source:
  `8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`
- V36/V37 ZIP:
  `7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`
- V38 exact ZIP:
  `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`
- V39 accepted HOLD ZIP:
  `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`

Exact baseline remains:
$40 -> $107.43 over 12 months, 8.58% geometric/month, DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501.

15% geometric/month target would imply about $214.01 from $40 over 12 months. It is not achieved.

## Frozen evidence

V32 DeepMLP keep60 remains frozen risk-efficiency evidence:
near-same Feb-Jul return with DD reduced from 10.82% to 7.36%, 153 vs 222 trades, AvgR 0.325 vs 0.240, PF 1.833 vs 1.558.

V36 Transformer remains reproducible sequence evidence:
final-R Spearman 0.5148, Hold AUC 0.6757, Protect AUC 0.6771, both AUCs >0.5 in 6/6 months.

Do not retune either evidence lane on its accepted window.

## V39 decision

V39 fusion is HOLD:
17 triggers, 3/6 positive months, 32% mean monthly false-big-winner. Do not promote to exact-MT5 and do not rescue it by sweeping quantiles, `p_hold`, source/direction filters or risk.

Root problem is event ordering.

## V40 research contract

Decision zone:
`current_R >= +1R`.

First-passage events:

- down barrier = `current_R - 0.25R`;
- up barrier = `max(current_R + 0.75R, +2R)`.

Primary model:
HistGradientBoostingClassifier for GIVEBACK_FIRST vs TAIL_FIRST.

Fixed chronology:
past fully-exited train -> trailing 2-month calibration -> one-month test.
Threshold = 80th percentile calibration probability.
No test-month tuning.

Primary action:
`STATIC_PROTECT_0.25R`.

Secondary:
`SELECTIVE_TRAIL_0.25R`.

Both add zero entries and do not change initial risk.

Stage-A PASS requires:
>=5 folds, >=30 triggers, 5%-35% coverage, mean AUC >=0.60, GIVEBACK_FIRST rate >=60%, TAIL_FIRST rate <=25%, positive static shadow delta in >=4 test months, and total static delta R >0.

Shadow equity is not exact-MT5 PnL. A PASS only permits frozen Stage B exact-MT5.

## Runner hardening

V40 Windows schema lesson that must not regress:

- canonical entry `scripts/v40_upgrade_campaign_stage_a.py` adapts schema and re-exports the frozen research core `scripts/v40_upgrade_campaign_stage_a_core.py`;
- accepted V38 `trades.csv` can already carry `signal_sources`;
- never blindly merge another same-named M15 column into it;
- preserve the existing non-empty `signal_sources`, fill blanks from M15, and reject/avoid `_x/_y` suffix collisions;
- dependency-free static suite includes a synthetic regression test for this exact case.

Must preserve:

- explicit branch refspec;
- no `git clean`;
- pytest optional/static fallback;
- tracked-source secret scan;
- V36 full dependency probe including sklearn/scipy;
- one run -> one ZIP;
- internal manifest and CRC verification.

## Output contract

User runs one Git Bash bootstrap and uploads only:

`runtime/v40_upgrade_campaign/OUTPUT_V40_STAGE_A/v40_upgrade_campaign_stage_a.zip`

On receipt:
1. verify outer SHA;
2. CRC/testzip;
3. verify every manifest hash;
4. verify head/branch/input SHAs;
5. report exact baseline vs shadow policy vs 15% target separately;
6. evaluate gate without discretionary rescue tuning;
7. if PASS, design frozen exact-MT5 Stage B;
8. if HOLD, identify structural failure and preserve baseline.
