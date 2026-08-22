# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Tester/live guards and no-order constraints must not be weakened.
- V44/V45 may advance PAPER/DEMO deployment validation only.
- `LIVE_AUTHORIZED=0` remains mandatory.

## Source of truth

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Current campaign branch: `agent/v45-multiyear-single-run-validation`.
Never use `git clean`; accepted ZIPs, `.venv`, state backups, compiled EAs, checkpoints and completed tester outputs can be untracked recovery assets.

Read together:

- `docs/handover/RECOVERY_PROMPT.md`
- `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
- `docs/research/v44_baseline_robustness_validation_results.md`
- `docs/research/v45_multiyear_single_run_validation_plan.md`
- `docs/research/v45_mt5_disk_failure_diagnosis.md`
- `docs/adr/ADR-045-multiyear-single-run-before-live-escalation.md`

## Accepted baseline economics

Accepted control `adaptive_ewma_hl8_thr0`, exact 2025-08-01 -> 2026-08-01:

- $40 -> $107.432645;
- +168.5816% total;
- 8.58163% geometric/month;
- DD 9.9038%;
- 563 trades;
- AvgR 0.214608R;
- PF 1.500756.

Threshold comparators:

- `adaptive_ewma_hl8_thr0p05`: $111.285257 / 8.900900% month / DD 10.4368% / PF 1.521009.
- `adaptive_ewma_hl10_thr0p05`: $110.025682 / 8.797648% month / DD 9.8587% / PF 1.530107.

## V44 accepted result — PAPER_DEMO_READY

Canonical V44 commit: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.
Accepted V44 ZIP SHA256: `550396cc2806538ae1f38ba596e3af705a08bcb2305335a14d0cfa39aabc8fa4`.
Integrity PASS: CRC, internal manifest 130/130, all 19 exact windows, exact annual control reproduction.

V44 restart robustness:

- control: monthly +9/12, quarter +3/4, half-year +2/2, sign agreement 10/12;
- HL8p05: monthly +8/12, quarter +3/4, half-year +2/2, sign agreement 10/12;
- HL10p05: monthly +9/12, quarter +3/4, half-year +2/2, sign agreement 11/12.

V45 freezes:

1. primary `adaptive_ewma_hl10_thr0p05`;
2. return shadow `adaptive_ewma_hl8_thr0p05`;
3. control `adaptive_ewma_hl8_thr0`.

## V45 protocol

One exact Strategy Tester invocation only:

- XAUUSDm / M15 / Model=0;
- Deposit=$40 USD / leverage 1:200;
- 2022-01-01 -> 2026-08-01;
- monthly summary and full trade ledger retained;
- first six observed months are warm-up;
- analyzer emits monthly, yearly, rolling 3/6/12m and friction-stress evidence.

### Anti-look-ahead state rule

The accepted restart state is from 2025-08 and must never be injected into the 2022 run. V45 backs up `v30_ml_dl_feature_lake_state.csv`, removes it before tester launch, cold-starts from reset adaptive scores, captures post-run state as evidence, then restores the pre-V45 state. Accepted V38 source semantics were inspected and support missing-state cold start.

## V45 first-run failure — root cause CONFIRMED

First attempted V45 tester run used HEAD `86a384cb90f1823bd9ec0c26231c7c32033fb118`.

Before MT5:

- static gates PASS 15/15;
- secret scan PASS;
- V34 causal tape PASS;
- accepted V38 parent PASS;
- deterministic source SHA PASS `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- compiler `Result: 0 errors, 0 warnings` PASS.

Diagnostic ZIP SHA256:
`3af2ab70f02920ad6fbd0eb5b3fd67ef66a550bf2db08bd523ee4b63372e8b1f`.

Confirmed log evidence:

- terminal started with only `3 / 136 Gb disk` free;
- XAUUSDm synchronized from 2021-01-03 through 2026-08-14;
- EA initialized successfully and printed `V45_MULTIYEAR_VALIDATION START` at 2022-01-01;
- tester logged `XAUUSDm: cannot generate history data, check disk space`;
- `0 ticks, 0 bars generated`;
- final tester result `no disk space in ticks generating function`;
- terminal exited with process rc `100018`.

Therefore there is still **no accepted V45 multi-year result**. The failure is disk exhaustion during tick generation, not compile, config, state, strategy, or missing 2022 history. Do not shorten the historical range because of this incident.

## MetaTester storage moved to D

The heavy tester-agent copies live under:

`%APPDATA%\MetaQuotes\Tester\D0E8209F77C8CF37AD8BF550E51FF075`

V45 now migrates that directory to:

`D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`

using:

`runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py`

The original C path becomes an NTFS directory junction to D, so MetaTrader continues using the same logical path while physical tick/history copies are stored on D.

Migration safety contract:

- MT5/MetaEditor/MetaTester closed;
- Robocopy source to dedicated D target;
- verify file count + byte count;
- rename C source to a temporary backup;
- create `mklink /J` from the original C path to D;
- verify exact junction target;
- only then delete the C backup;
- rollback the backup if junction creation/verification fails;
- idempotent if the exact junction already exists.

Do not move/delete Terminal broker history under `%APPDATA%\MetaQuotes\Terminal\<id>\bases`, Common Files state/tapes, project evidence or compiled EAs.

## Disk-space recovery now mandatory

After D migration, `PREPARE_V45_DISK.py` is junction-aware:

- terminal volume (normally C:) requires >=2 GiB for config/log/temp activity;
- physical MetaTester storage volume (normally D:) requires >=12 GiB for the 2022-2026 tick run;
- only recomputable tester temp/cache may be removed automatically;
- a blanket 12-GiB requirement on C is no longer valid after the junction exists.

Detailed diagnosis: `docs/research/v45_mt5_disk_failure_diagnosis.md`.

## V45 readiness gate

Primary HL10p05 after warm-up must satisfy all:

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
- SumR positive after -0.05R/trade stress.

No retuning on the same V45 sample after results are seen.

## Provenance

Accepted V38 ZIP SHA: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
Accepted V38 parent source SHA: `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
Verified V34 causal tape SHA: `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.
Frozen V45 source SHA: `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.

## Recovery ladder

`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`

- exact D junction migration must verify before tester launch;
- valid compile checkpoint -> reuse compile;
- disk preflight must PASS before tester launch;
- `MT5_DONE.json` -> collection-only, MT5 MUST NOT RERUN;
- `DONE.txt` -> analysis/package only, MT5 MUST NOT RERUN;
- packaging-only failure -> package-only recovery;
- explicit UTF-8, no runtime shell patcher, no `set +e`/ERR-trap launcher pattern;
- MT5 completion = new `LATEST` + complete manifested output, not terminal rc alone.

## V45 entrypoints

Canonical Git Bash bootstrap:
`runtime/v45_multiyear_validation/BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh`

Tester-storage migration to D:
`runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py`

Disk preflight:
`runtime/v45_multiyear_validation/PREPARE_V45_DISK.py`

Tracked orchestrator:
`runtime/v45_multiyear_validation/RUN_V45_MULTIYEAR_ONE_SHOT.py`

Diagnostic-only collector:
`runtime/v45_multiyear_validation/DIAGNOSE_V45_MT5_FAILURE_GIT_BASH.sh`

Package-only recovery:
`runtime/v45_multiyear_validation/PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh`

Expected successful ZIP:
`runtime/v45_multiyear_validation/OUTPUT_V45/v45_multiyear_single_run_validation.zip`
