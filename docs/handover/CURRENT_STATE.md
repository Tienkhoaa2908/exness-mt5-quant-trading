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
12-month exact control: $40 -> $107.432645; +168.5816% total; 8.58163% geometric/month; max DD 9.9038%; 563 trades; AvgR 0.214608R; PF 1.500756.
15% geometric/month would imply about $214.01 after 12 months from $40. It remains aspirational, not an acceptance override. Exact gap remains 6.41837 percentage points/month.

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
- V42 exact-MT5 run completed successfully on 2026-08-21 from verified compiled EA. User-supplied RAR outer SHA256 `3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`; internal bundle manifest 18/18 hashes verified after accounting for MSYS `sha256sum` binary-marker format. V42 status = HOLD; no challenger is eligible to freeze.

## V42 exact result — HOLD

Control reproducibility passed exactly: `$40 -> $107.432645`, 8.58163% geometric/month, DD 9.9038%, 563 trades.

Best V42 return challenger was `v42_cp_fast5_slow20_switch15m`:

- ending USD 106.387574;
- geometric/month 8.493214%;
- DD 9.6614%;
- 507 trades;
- AvgR 0.243553R;
- PF 1.534444;
- turnover -3.01% vs control;
- only 6/12 months beat control;
- ending equity -$1.045071 vs control;
- geometric return -0.08842pp/month vs control.

It passes risk/quality checks but fails the preregistered material-return checks, so `eligible_to_freeze_for_fresh_holdout=[]`.

The most risk-efficient V42 arm was `v42_hl8_thr0p05_switch15m`: $103.358584, 8.232381%/month, DD 7.9188%, 465 trades, AvgR 0.266639R, PF 1.538075, return/DD 20.0026. This is a useful efficiency signal but not a return upgrade and must not replace the control under the current objective.

Historical exact router comparators remain informative:

- `adaptive_ewma_hl8_thr0p05`: $111.285257, 8.900900%/month, DD 10.4368%, 531 trades, PF 1.521009;
- `adaptive_ewma_hl10_thr0p05`: $110.025682, 8.797648%/month, DD 9.8587%, 537 trades, PF 1.530107;
- `adaptive_ewma_hl12_thr0p05`: $107.797276, 8.612293%/month, DD 9.9432%;
- `adaptive_cp_fast5_slow20_thr0p30`: $102.206843, 8.131360%/month, DD 11.3766%.

These historical variants do not satisfy the V42 preregistered >=5% ending-equity and >=+0.50pp/month uplift gate either. They are hypotheses for future baseline work, not promoted policies.

## V42 research contract

V42 exact-MT5 appends six challengers to accepted V38: five 15-minute direction-switch hysteresis arms covering frozen adaptive routers, plus one HL8 30-minute sensitivity arm. Builder clones exact `SetupAdaptiveRouter` arguments from the accepted V38 source.
No expert signal, entry/exit geometry, sizing or risk changes. Expensive V38 M1/M15 telemetry is disabled; monthly summary, trade ledger and manifest remain mandatory.
Analyzer hard-reproduces accepted V38 control before any challenger comparison. A preregistered material-uplift gate can only freeze a challenger for fresh chronological confirmation; no same-sample retuning.

## V42 provenance / runtime recovery history

### Immutable V38 parent

The first V42 attempt exposed historical source-builder byte drift: current V34 reconstruction emitted `228b3ec7...` while an old runner expected `8bae2c56...`. Do not bless the new historical hash.

V42 uses only accepted V38 exact bundle `runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`, outer SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`, CRC-tests it, extracts the unique accepted `V38FastHarvestLab.base.a.mq5`, then builds V42 from those bytes. V34 tape/state hashes remain mandatory runtime dependencies.

### Windows UTF-8

One retry stopped in static tests because Windows Python decoded a generated UTF-8 shell file with CP1252. All V42 test text reads are explicit UTF-8 and bootstrap exports `PYTHONUTF8=1` plus `PYTHONIOENCODING=utf-8`.

### Bash ERR trap

One retry stopped because `set +e` does not suppress a global Bash `ERR` trap. V42 no longer uses `set +e`; Windows process return codes are captured only in `if command; then rc=0; else rc=$?; fi` contexts.

### MetaEditor artifact race

A later retry showed MetaEditor rc=1 while `.mq5`, `.log`, and `.ex5` had all been created. The runner was changed to artifact-driven compile acceptance and a compiled-EA resume path. The successful exact run reused V42 source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e` with compiler `Result: 0 errors, 0 warnings` and did not launch MetaEditor again.

### Final packaging failure after successful MT5

The exact MT5 run and analyzer completed, but final ZIP creation failed because Git Bash/MSYS `sha256sum` wrote manifest lines as `<hash> *filename`, while an inline Python packager incorrectly assumed Linux text-mode form `<hash><two spaces>filename` and called `line.split('  ',1)`. This was a packaging-only defect. The completed bundle contained all 18 required evidence files and all 18 hashes verify.

A portable Python packager now generates its own canonical manifest using Python SHA256 and therefore does not depend on platform-specific `sha256sum` text/binary markers. Package-only recovery is `runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh`; it never launches MetaEditor or MT5.

## Canonical runtime architecture

Do not dynamically patch shell scripts at runtime.

Clean future execution shape:

`bootstrap -> direct runner -> accepted V38 provenance -> V42 source -> compile artifact checkpoint -> MT5 -> analyzer -> portable Python packager -> one ZIP`.

Bootstrap may invoke package-only recovery only when the exact MT5 evidence and analyzer outputs already exist; it must not mask earlier research/runtime failures.

Plan: `docs/research/v42_baseline_router_exact_mt5_plan.md`. ADR: `docs/adr/ADR-042-exact-mt5-baseline-router-upgrade.md`.

## One run -> one ZIP

V42 research is closed HOLD; do not rerun MT5 to repair packaging.

For completed-output packaging only: `runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh`.

The next research cycle should use the exact V42 evidence above and retain `adaptive_ewma_hl8_thr0` as the return control unless a new preregistered challenger proves material uplift.
