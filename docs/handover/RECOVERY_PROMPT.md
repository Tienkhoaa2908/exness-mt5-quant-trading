# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Start here

Current branch:

`agent/v43-confidence-aware-router-exact-mt5`

Before modifying or running anything, read:

1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
3. `docs/research/v43_confidence_aware_router_exact_mt5_plan.md`
4. `docs/adr/ADR-043-confidence-aware-credit-routing.md`

Do not ask the user to reconstruct history from memory. Repository history, exact evidence, handover docs and runtime artifacts are the source of truth.

Never run `git clean`; accepted ZIPs, compiled EA artifacts, `.venv`, state, checkpoints and completed outputs may be untracked and required for recovery.

## Safety

- REAL-MONEY LIVE TRADING forbidden.
- Strategy Tester only.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale/grid/doubling.
- `AllowLiveTrading=0` and `AllowDllImport=0` in tester config.
- No native/external broker-order path.
- No result authorizes live trading.

## Exact baseline / target

Accepted control:

`adaptive_ewma_hl8_thr0` / `usd40_r1p0_cent_continuous`

2025-08-01 -> 2026-08-01, XAUUSDm M15 Model=0, USD40:

- `$40 -> $107.432645`;
- `+168.5816%` total;
- `8.58163%` geometric/month;
- max DD `9.9038%`;
- 563 trades;
- AvgR `0.214608R`;
- PF `1.500756`.

15%/month implies about `$214.01` after 12 months from `$40`; it remains aspirational.

Hard control reproduction vectors must not be weakened in the exact analyzer.

## Accepted provenance

Accepted V38 exact ZIP:

`runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`

SHA256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Accepted V38 parent source SHA:

`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`

Accepted V30 source SHA:

`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

V34 specialist tape SHA:

`d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`

Frozen state SHA:

`5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`

## V42 = HOLD — accepted exact evidence

V42 Strategy Tester run completed successfully on 2026-08-21 under evidence head:

`9ddd9a99c708e66f62f0eae7bd85750ad32f2f13`

V42 compiled source SHA:

`142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`

Compiler: `Result: 0 errors, 0 warnings`.

User-supplied completed-output RAR SHA:

`3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`

18/18 completed bundle hashes verified. Recovered exact ZIP SHA:

`3176850e89e1c36ac87be7ff827d34209646da10aaeacfe0d0a013ebeeaa6066`

Control reproduced exactly.

Best V42 challenger `v42_cp_fast5_slow20_switch15m`:

- end `$106.387574`;
- geo/month `8.493214%`;
- DD `9.6614%`;
- 507 trades;
- AvgR `0.243553R`;
- PF `1.534444`;
- beats control 6/12 months.

`eligible_to_freeze_for_fresh_holdout=[]`.

V42 = HOLD. Do not retune switch delays on this 12-month window.

Useful historical exact threshold parents:

- `adaptive_ewma_hl8_thr0p05`: `$111.285257`, `8.900900%/month`, DD `10.4368%`, 531 trades, PF `1.521009`;
- `adaptive_ewma_hl10_thr0p05`: `$110.025682`, `8.797648%/month`, DD `9.8587%`, 537 trades, PF `1.530107`.

These are frozen V43 parents/hypotheses, not promoted strategies.

## Current V43 contract

V43 changes credit allocation only when currently active LONG and SHORT experts conflict and their causal EWMA scores are close. It does not add a time delay to direction changes.

Frozen V43 source SHA:

`487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a`

Exactly four challengers:

- `v43_hl8_thr0p05_conf0p05`;
- `v43_hl10_thr0p05_conf0p05`;
- `v43_hl8_thr0p05_conf0p10`;
- `v43_hl10_thr0p05_conf0p10`.

Margins 0.05R/0.10R are frozen before results. No same-window margin retuning or rescue sweep.

### Confidence-aware logic

- same parent EWMA variant and min-score threshold;
- if only one direction has an eligible active expert: use it immediately;
- if both directions active and strongest LONG/SHORT score gap >= margin: use leader immediately;
- if both active and gap < margin: keep candidate-specific incumbent direction only if that direction remains active;
- exact tie with no incumbent: abstain;
- no fixed direction-switch time delay;
- mandatory manifest marker: `v43_global_time_hysteresis=0`.

No expert signal, entry/exit geometry, sizing, capital model or risk is changed.

## V43 gates

Candidate must pass exact control reproduction, then both a material control gate and incremental frozen-parent gate.

Control gate:

- end >=105% control;
- geo uplift >=+0.50pp/month;
- DD <=control+1pp;
- improved return/DD;
- >=10 positive months;
- beats control >=7/12 months;
- worst month >=-5%;
- turnover <=110% control;
- trades >=75% control.

Parent gate:

- end > frozen parent;
- geo > parent;
- return/DD not worse;
- DD <=parent+0.50pp;
- beats parent >=7/12 months;
- turnover <=105% parent;
- trades >=90% parent.

PASS only permits a frozen fresh chronological confirmation.

## Windows runtime incident knowledge — mandatory

The following are established facts and must not be rediscovered by another trial-and-error cycle.

### 1. immutable V38 parent

Historical V34 source reconstruction changed bytes (`228b3ec7...`) relative to a stale accepted hash (`8bae2c56...`). Never bless a new historical hash merely to pass a runner. Use accepted V38 ZIP SHA/CRC + exact source extraction.

### 2. CP1252 / UTF-8

A V42 static test crashed because Windows Python used CP1252 for a UTF-8 shell file. All tracked text reads must use explicit UTF-8/UTF-8-SIG. Export `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` before Python subprocesses.

### 3. ERR trap / `set +e`

Under `set -Eeuo pipefail` plus a global ERR trap, `set +e` did not prevent the trap from killing the runner when MetaEditor returned rc=1. Never use `set +e` around Windows launchers. Use `if command; then rc=0; else rc=$?; fi`.

### 4. runtime patcher architecture rejected

Do not recreate a Python runtime patcher or generated/self-modifying shell runner. Use direct tracked shell entrypoints shaped after successful V32/V34/V38 workflows.

### 5. compile artifact gate

MetaEditor can return rc=1 while valid `.log` and `.ex5` are created moments later. Compile success is intended source SHA + final `Result: 0 errors, 0 warnings` + non-empty EX5. Check existing compile artifacts before deleting them; fresh compile polls combined postconditions.

### 6. MT5 durable completion

Terminal return code alone is not enough. Require a new LATEST run id/folder plus complete `monthly_summary.csv`, `trades.csv`, `manifest.txt` with tester/no-order/experiment markers. Wait for artifact flushing and recover collection from the existing run if possible.

### 7. MSYS manifest format

Git Bash/MSYS `sha256sum` may emit `<hash> *filename`. Do not parse platform `sha256sum` display format with `line.split('  ',1)` or similar. Use `scripts/package_research_bundle_portable.py`, which hashes in Python and writes canonical manifest rows.

### 8. package-only recovery

Every expensive exact run must have package-only recovery. If exact MT5 + analyzer outputs already exist, package them; **do not rerun MT5** because ZIP creation failed.

### 9. no `git clean`

Untracked runtime artifacts may be required to resume. Use explicit refspec fetch + tracked reset only.

### 10. recovery ladder

Resume one stage after the last durable success:

`provenance -> compile -> MT5 -> collection -> analysis -> packaging`

If packaging failed, run packaging only. If analysis failed with complete run outputs, rerun analysis only. If collection failed after new LATEST exists, collect that run. Do not restart earlier expensive stages without evidence that they are invalid.

Full details: `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`.

## V43 runtime paths

One-shot clean runner:

`runtime/v43_confidence_router_exact_mt5/BOOTSTRAP_V43_CONFIDENCE_ROUTER_ONE_SHOT_GIT_BASH.sh`

Direct exact runner:

`runtime/v43_confidence_router_exact_mt5/RUN_V43_CONFIDENCE_ROUTER_EXACT_MT5_GIT_BASH.sh`

Package-only recovery:

`runtime/v43_confidence_router_exact_mt5/PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh`

Output:

`runtime/v43_confidence_router_exact_mt5/OUTPUT_V43/v43_confidence_router_exact_mt5.zip`

The bootstrap may invoke package-only recovery only if exact evidence, analyzer output and required run files already exist. It must not mask compile, MT5 or analyzer failures.

## Required QA before user run

- Python helpers/tests compile.
- Dependency-free static suite passes if pytest unavailable.
- `bash -n` bootstrap/direct/package-only entrypoints.
- explicit UTF-8 contract.
- secret scan.
- immutable V38 SHA/CRC/source contract.
- deterministic V43 source SHA must equal `487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a`.
- generated MQL no-order/tester lint.
- no `set +e`, no runtime patcher, no `git clean`.
- portable bundle packager present.

After exact output arrives, verify outer ZIP SHA, CRC, internal manifest, evidence head/branch, compiler evidence, tester safety markers and exact control reproduction before interpreting V43 economics.
