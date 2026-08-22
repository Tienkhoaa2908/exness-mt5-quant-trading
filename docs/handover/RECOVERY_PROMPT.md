# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current campaign

Branch: `agent/v45-multiyear-single-run-validation`
Base canonical V44 commit: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`
Never `git clean`.

Read first:

1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
3. `docs/research/v44_baseline_robustness_validation_results.md`
4. `docs/research/v45_multiyear_single_run_validation_plan.md`
5. `docs/research/v45_mt5_disk_failure_diagnosis.md`
6. `docs/adr/ADR-045-multiyear-single-run-before-live-escalation.md`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Research risk <=1.00%/trade. No Martingale/grid/doubling. Strategy Tester only with `AllowLiveTrading=0`, `AllowDllImport=0`, no native/external broker orders. `LIVE_AUTHORIZED=0`.

## Accepted V44 result

Accepted V44 ZIP SHA256: `550396cc2806538ae1f38ba596e3af705a08bcb2305335a14d0cfa39aabc8fa4`.

V44 = `PAPER_DEMO_READY`; 19/19 exact windows completed and annual control reproduced exactly at $107.432645 / 563 trades.

Frozen V45 candidates:

1. primary `adaptive_ewma_hl10_thr0p05` — annual $110.025682, 8.797648%/month, DD 9.8587%, PF 1.530107, restart sign agreement 11/12;
2. return shadow `adaptive_ewma_hl8_thr0p05` — annual $111.285257, 8.900900%/month, DD 10.4368%;
3. control `adaptive_ewma_hl8_thr0` — annual $107.432645, 8.58163%/month, DD 9.9038%.

Do not retune these on V45.

## V45 exact protocol

One continuous Strategy Tester invocation only:

- XAUUSDm / M15 / Model=0;
- Deposit=$40 USD / leverage 1:200;
- 2022-01-01 -> 2026-08-01;
- first 6 observed months warm-up/excluded from readiness;
- monthly summary and full trade ledger retained;
- analyzer emits monthly, yearly and rolling 3/6/12-month reports.

## Critical anti-look-ahead state contract

Never inject accepted 2025-08 state SHA `5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0` into a 2022 historical run.

V45 backs up Common Files `v30_ml_dl_feature_lake_state.csv`, deletes it before launch, runs cold-start, records post-run state for evidence, and restores the pre-V45 state afterward. Accepted V38 source supports missing-state cold start because `LoadAdaptiveState()` resets adaptive scores first and `OnInit()` continues when the file is absent.

## Provenance

Accepted V38 ZIP SHA: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
Accepted V38 source SHA: `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
Verified V34 causal tape SHA: `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.
Frozen V45 source SHA: `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.

## Confirmed first-run failure

First V45 attempt HEAD `86a384cb90f1823bd9ec0c26231c7c32033fb118` passed static/source/compile gates but terminal returned rc `100018` and produced no accepted run output.

Diagnostic ZIP SHA256: `3af2ab70f02920ad6fbd0eb5b3fd67ef66a550bf2db08bd523ee4b63372e8b1f`.

Root cause is confirmed disk exhaustion, not missing 2022 history or EA failure:

- terminal startup showed only `3 / 136 Gb disk` free;
- XAUUSDm history existed from 2021 through 2026;
- V45 EA initialized successfully;
- tester logged `cannot generate history data, check disk space`;
- `0 ticks, 0 bars generated`;
- final tester result `no disk space in ticks generating function`;
- terminal exited with process rc `100018`.

Do not shorten the V45 date range because of this incident.

## MetaTester D-drive migration contract

The heavy local-agent copies are under:

`%APPDATA%\MetaQuotes\Tester\D0E8209F77C8CF37AD8BF550E51FF075`

Canonical bootstrap first runs:

`runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py`

Default physical target:

`D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`

The script copies with Robocopy, verifies file count + bytes, renames the C source to a temporary backup, creates an NTFS directory junction at the original C path pointing to D, verifies exact target resolution, then deletes the C backup. On junction failure it restores the original C directory. It is idempotent when the exact junction already exists.

It must never move/delete Terminal broker history, Common Files state/tapes, accepted evidence, repo files or compiled EAs.

After migration, `PREPARE_V45_DISK.py` is volume-aware:

- terminal volume (normally C:) >=2 GiB;
- physical MetaTester volume (normally D:) >=12 GiB;
- only recomputable tester temp/cache may be removed automatically.

Do not restore a blanket 12-GiB C-drive requirement after MetaTester storage has been redirected to D.

## V45 readiness gate

Primary HL10 threshold0.05 must pass all after warm-up:

- >=42 evaluation months;
- >=60% positive months;
- >=3 full calendar years;
- >=75% full years positive;
- worst full year >=-15%;
- >=75% positive rolling-12m windows;
- worst rolling-12m >=-15%;
- max MTM DD <=20%;
- PF >=1.20;
- worst month >=-15%;
- SumR remains positive after -0.05R/trade friction stress.

Result may be `MULTIYEAR_ROBUSTNESS_PASS` or `HOLD`. A pass permits continued paper/demo deployment validation only.

## Recovery ladder

`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`

Do not restart an earlier expensive stage when a later stage alone failed.

V45 checkpoints:

- exact D junction migration must verify before tester launch;
- valid compile checkpoint = exact V45 source SHA + final `Result: 0 errors, 0 warnings` + non-empty EX5;
- junction-aware disk preflight must pass before tester launch;
- `MT5_DONE.json` = tester completed and run folder known; collection only, MT5 MUST NOT RERUN;
- `DONE.txt` = tester artifacts collected; analysis/package only, MT5 MUST NOT RERUN;
- completed bundle + packaging failure = package-only recovery.

Historical failures already fixed/prohibited: immutable V38 provenance, explicit UTF-8, no Bash `set +e` under ERR trap, no runtime shell patcher, artifact-driven MetaEditor acceptance, new-LATEST MT5 completion, portable Python bundle manifest, package-only recovery, cold-start anti-look-ahead, diagnostic-first rc handling, and D-drive MetaTester storage migration.

## Entry points

Canonical Git Bash one-shot: `runtime/v45_multiyear_validation/BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh`.
Tester-storage migration: `runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py`.
Disk preflight: `runtime/v45_multiyear_validation/PREPARE_V45_DISK.py`.
Tracked orchestrator: `runtime/v45_multiyear_validation/RUN_V45_MULTIYEAR_ONE_SHOT.py`.
Package-only: `runtime/v45_multiyear_validation/PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh`.
Expected ZIP: `runtime/v45_multiyear_validation/OUTPUT_V45/v45_multiyear_single_run_validation.zip`.

On receipt verify outer SHA, ZIP CRC, canonical internal manifest, evidence HEAD/branch/source, safety markers, month coverage, annual results, rolling-12m stability, friction stress and primary HL10 gate. Do not retune on this sample after seeing results.
