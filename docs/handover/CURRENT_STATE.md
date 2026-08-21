# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade; no Martingale/grid/doubling.
- Do not remove tester/live guards or add native/external order paths.
- V42 is exact MT5 Strategy Tester research, not live execution.

## Source of truth

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Current research branch: `agent/v42-baseline-router-exact-mt5`.
V42 starts from V41 implementation commit `60cd93ad9eefd07447f65b2e6909a20edf60f3ae`. Windows recovery uses an explicit refspec and must not run `git clean`, because accepted runtime evidence/checkpoints/environments can be untracked.

## Exact baseline / target

Accepted control: `adaptive_ewma_hl8_thr0`, `usd40_r1p0_cent_continuous`.
12-month exact V38 control: $40 -> $107.432645; about +168.6% total; about 8.58% geometric/month; max DD about 9.90%; 563 trades; AvgR about 0.215R; PF about 1.501.
15% geometric/month would imply about $214.01 after 12 months from $40. It remains aspirational, not an acceptance override.

## Baseline architecture

The control is a causal realized-R EWMA performance router, not neural. Experts: EMA skip20, MACD gap10, BOS/FVG gap8, Trend20 gap5 and Slow Momentum 16h+24h. Half-life=8, threshold=0; selected expert owns direction.
Existing exact candidates already cover HL8/10/12 threshold variants and fast5/slow20 change-proxy. V42 adds bounded switching hysteresis rather than renaming those old parameter probes.

## Recent evidence

- V32 DeepMLP keep60: frozen risk-efficiency evidence, not return winner.
- V36 Transformer: predictive state signal accepted/reproducible, but V39-V41 failed to monetize it robustly.
- V38 ZIP `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`: accepted exact control; universal fast exits rejected.
- V39 ZIP `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`: HOLD.
- V40 ZIP `e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`: HOLD.
- V41 ZIP `f7e508816f96cb033f327582013fc0cf3c8583693b820c445de9c7156f469f7f`: HOLD. Shadow entry/action/integrated ended about $72.50/$88.51/$69.35 vs $107.43 baseline; no V41 Stage B.

## V42 research contract

V42 exact-MT5 appends six challengers to accepted V38: five 15-minute direction-switch hysteresis arms covering frozen adaptive routers, plus one HL8 30-minute sensitivity arm. Builder clones exact `SetupAdaptiveRouter` arguments from the accepted V38 source.
No expert signal, entry/exit geometry, sizing or risk changes. Expensive V38 M1/M15 telemetry is disabled; monthly summary, trade ledger and manifest remain mandatory.
Analyzer hard-reproduces accepted V38 control before any challenger comparison. A preregistered material-uplift gate can only freeze a challenger for fresh chronological confirmation; no same-sample retuning.

## V42 provenance / runtime recovery history

### Immutable V38 parent

The first V42 attempt exposed historical source-builder byte drift: current V34 reconstruction emitted `228b3ec7...` while an old runner expected `8bae2c56...`. Do not bless the new historical hash.

V42 uses only accepted V38 exact bundle `runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`, outer SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`, CRC-tests it, extracts the unique accepted `V38FastHarvestLab.base.a.mq5`, then builds V42 from those bytes. V34 tape/state hashes remain mandatory runtime dependencies.

### Windows UTF-8

One retry stopped in static tests because Windows Python decoded a generated UTF-8 shell file with CP1252. All V42 test text reads are now explicit UTF-8 and bootstrap exports `PYTHONUTF8=1` plus `PYTHONIOENCODING=utf-8`.

### Bash ERR trap

One retry stopped because `set +e` does not suppress a global Bash `ERR` trap. V42 no longer uses `set +e`; Windows process return codes are captured only in `if command; then rc=0; else rc=$?; fi` contexts.

### MetaEditor artifact race — latest observed state

The 2026-08-21 20:12 retry passed 15 static gates, accepted V38 parent verification, V42 deterministic double-build and MQL lint. MetaEditor returned rc=1 and the then-current runner declared the compile log absent after a fixed wait. Diagnostic directory listing immediately afterwards showed all three artifacts already present:

- `V42BaselineRouterLab.mq5` size 98214;
- `V42BaselineRouterLab.log` size 3298;
- `V42BaselineRouterLab.ex5` size 97958.

Therefore MetaEditor had in fact completed compilation; the failure was a runner timing/postcondition race, not a strategy or MQL-source failure. Strategy Tester still had not launched, so no V42 PnL exists yet.

## Canonical runtime architecture after the incident

Do not dynamically patch shell scripts at runtime. That architecture was removed.

The canonical full runner now follows the proven V32/V34/V38 shape directly:

`bootstrap -> direct runner -> accepted V38 provenance -> V42 source -> compile artifact checkpoint -> MT5 -> analyzer -> one ZIP`.

Compile success is artifact-driven: current V42 source hash + compiler log final `Result: 0 errors, 0 warnings` + non-empty EX5. Existing valid compiled artifacts are reusable via a source-hash marker / timestamp recovery check; the runner does not delete them before testing reuse. A fresh compile polls the combined log+Result+EX5 postcondition rather than failing on a fixed log-existence deadline.

Static tests run `bash -n` on bootstrap, full runner and resume runner and compare the V42 direct runner shape with successful V32/V34/V38 runners.

## Immediate recovery path for the already compiled V42 EA

Because the latest failed attempt already produced `V42BaselineRouterLab.mq5/.log/.ex5`, the next execution should **not compile again**.

Use:

`runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`

The resume path:

- never launches MetaEditor;
- requires installed V42 source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`;
- requires existing compile log with final `Result: 0 errors, 0 warnings` and non-empty EX5 newer than/equal to the installed source;
- re-verifies accepted V38 ZIP, V34 tape and frozen state;
- launches only Strategy Tester with `AllowLiveTrading=0` / no DLL;
- waits for a new `LATEST` run id and complete `monthly_summary.csv`, `trades.csv`, `manifest.txt` plus safety markers;
- analyzes and packages one CRC/SHA-manifested ZIP.

If the existing compile log is not 0/0, resume must fail and print the actual compile log; it must not silently recompile or weaken the gate.

Plan: `docs/research/v42_baseline_router_exact_mt5_plan.md`. ADR: `docs/adr/ADR-042-exact-mt5-baseline-router-upgrade.md`.

## One run -> one ZIP

For a clean future run: `runtime/v42_baseline_router_exact_mt5/BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh`.
For the current already-compiled recovery: `runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`.

Upload only `runtime/v42_baseline_router_exact_mt5/OUTPUT_V42/v42_baseline_router_exact_mt5.zip`.
On upload verify outer SHA, CRC, internal manifest, evidence HEAD/branch, accepted V38 parent ZIP/source hashes, compiler evidence, tester manifest and hard control reproduction. Report exact baseline vs historical routers vs V42 challengers vs 15% target using DONE / EVIDENCE / DECISIONS / ISSUES / NEXT.
