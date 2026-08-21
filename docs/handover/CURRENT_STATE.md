# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Do not remove tester/live guards or add native/external broker-order paths.
- Exact-MT5 research is Strategy Tester only and never authorizes live trading.

## Source of truth

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

Current research branch:

`agent/v43-confidence-aware-router-exact-mt5`

V43 branches from the accepted V42 HOLD + runtime/package recovery state, not from an earlier V42 evidence-only commit.

Do not use `git clean`. Accepted ZIPs, `.venv`, checkpoints, state, compiled EA artifacts and completed run outputs may be untracked recovery assets.

Read together:

- `docs/handover/RECOVERY_PROMPT.md`
- `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
- `docs/research/v43_confidence_aware_router_exact_mt5_plan.md`
- `docs/adr/ADR-043-confidence-aware-credit-routing.md`

## Exact baseline / target

Accepted return control:

`adaptive_ewma_hl8_thr0` / `usd40_r1p0_cent_continuous`

Exact 12-month control:

- start `$40.00`;
- end `$107.432645`;
- total return `+168.5816%`;
- geometric/month `8.58163%`;
- max DD `9.9038%`;
- 563 trades;
- AvgR `0.214608R`;
- PF `1.500756`;
- 11/12 positive months.

15% geometric/month would imply about `$214.01` after 12 months from `$40`. The gap remains about `6.41837pp/month`. This target is aspirational and never overrides safety, reproducibility or promotion gates.

## Baseline architecture

The control is not neural. It is a causal realized-R EWMA performance router across five rule-based experts:

- EMA skip20;
- MACD gap10;
- BOS/FVG gap8;
- Trend20 gap5;
- Slow Momentum 16h+24h.

The accepted baseline uses half-life 8 and threshold 0. The router's selected expert owns direction. Router changes are path-dependent because realized-R feedback changes later expert scores, entries and flat time; exact MT5 is therefore the primary economic judge.

## Accepted evidence before V43

- V32 DeepMLP keep60: frozen risk-efficiency evidence, not a return winner.
- V36 Transformer: predictive state signal accepted/reproducible; V39-V41 did not monetize it robustly.
- V38 accepted exact ZIP SHA256: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
- Accepted V38 parent source SHA256: `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
- V39 = HOLD.
- V40 = HOLD.
- V41 = HOLD.

## V42 = HOLD

V42 exact MT5 completed successfully on 2026-08-21 from verified compiled source SHA:

`142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`

Compiler evidence: `Result: 0 errors, 0 warnings`.

User-supplied completed-output RAR SHA256:

`3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`

Internal completed bundle: 18/18 hashes verified. Recovered canonical ZIP created from those exact outputs:

`3176850e89e1c36ac87be7ff827d34209646da10aaeacfe0d0a013ebeeaa6066`

Control reproduced exactly: `$107.432645`, `8.58163%/month`, DD `9.9038%`, 563 trades.

Best V42 challenger, `v42_cp_fast5_slow20_switch15m`, ended `$106.387574`, `8.493214%/month`, DD `9.6614%`, 507 trades. It remained below control and only beat control in 6/12 months. `eligible_to_freeze_for_fresh_holdout=[]`.

V42 global direction-switch hysteresis generally improved trade quality/efficiency but reduced participation and right-tail compounding too much. Do not sweep switch durations on the same sample.

Historical exact threshold routers remain the most useful V42 observation:

- `adaptive_ewma_hl8_thr0p05`: `$111.285257`, `8.900900%/month`, DD `10.4368%`, 531 trades, PF `1.521009`;
- `adaptive_ewma_hl10_thr0p05`: `$110.025682`, `8.797648%/month`, DD `9.8587%`, 537 trades, PF `1.530107`.

They are hypotheses, not promoted policies, because they did not meet the preregistered material-uplift gate.

## V43 current contract

V43 tests confidence-aware cross-direction credit allocation, not global time hysteresis.

Frozen generated V43 source SHA256:

`487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a`

Exactly four preregistered challengers:

- `v43_hl8_thr0p05_conf0p05`;
- `v43_hl10_thr0p05_conf0p05`;
- `v43_hl8_thr0p05_conf0p10`;
- `v43_hl10_thr0p05_conf0p10`.

Frozen parents are HL8 threshold0.05 and HL10 threshold0.05. Fixed directional score margins are 0.05R and 0.10R only. No same-window margin retuning.

### Confidence-aware mechanism

At each decision:

1. use the same causal parent EWMA expert scores/minimum score;
2. identify strongest currently active LONG and SHORT expert;
3. if only one direction is active, choose immediately;
4. if both are active and top-score gap >= fixed margin, choose the leader immediately;
5. if both are active and gap < margin, retain the candidate-specific incumbent direction only if it remains active;
6. exact tie with no incumbent abstains;
7. no fixed time delay is attached to a direction change.

Mandatory marker: `v43_global_time_hysteresis=0`.

No expert signal, stop/TP geometry, sizing or risk is changed.

## V43 exact promotion gates

The analyzer must first hard-reproduce the accepted control monthly trade-count and monthly balance vectors.

A V43 candidate must then pass **both**:

### Control material-uplift gate

- ending equity >=105% control;
- geometric/month uplift >=+0.50pp;
- DD <= control +1pp;
- return/DD improved;
- >=10 positive months;
- beats control >=7/12 months;
- worst month >=-5%;
- turnover <=110% control;
- trades >=75% control.

### Frozen-parent incremental gate

- ending equity > its HL8/HL10 threshold0.05 parent;
- geometric/month > parent;
- return/DD not worse than parent;
- DD <= parent +0.50pp;
- beats parent >=7/12 months;
- turnover <=105% parent;
- trades >=90% parent.

PASS only permits freezing a candidate for genuinely fresh chronological confirmation. It is not production/live authorization.

## Mandatory Windows recovery lessons

These are engineering invariants, not optional notes. Full details are in `WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`.

1. **immutable V38**: never bless historical builder-byte drift; exact router parent is the accepted V38 ZIP/source.
2. **CP1252**: repository text handling is explicit UTF-8; export `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.
3. **ERR trap**: never use `set +e` around MetaEditor/MT5 under the global ERR trap; capture rc in conditional context.
4. **runtime patcher**: do not reintroduce generated/self-modifying execution shell; use a direct tracked runner.
5. **compile artifact**: success is intended source SHA + final `Result: 0 errors, 0 warnings` + EX5; check valid artifacts before deleting them.
6. MT5 completion is new LATEST/run folder + complete manifested outputs, not process rc alone.
7. **MSYS**: never parse platform-specific `sha256sum` rendering for bundle manifests; use `scripts/package_research_bundle_portable.py`.
8. **package-only** recovery must exist for every expensive exact run.
9. **do not rerun MT5** when tester/analyzer completed and only collection/analysis/packaging needs recovery.
10. follow the **recovery ladder**: provenance -> compile -> MT5 -> collection -> analysis -> packaging; resume only the failed stage.

## V43 runtime entrypoints

Clean one-shot execution:

`runtime/v43_confidence_router_exact_mt5/BOOTSTRAP_V43_CONFIDENCE_ROUTER_ONE_SHOT_GIT_BASH.sh`

Direct tracked runner:

`runtime/v43_confidence_router_exact_mt5/RUN_V43_CONFIDENCE_ROUTER_EXACT_MT5_GIT_BASH.sh`

Package-only recovery after completed exact evidence:

`runtime/v43_confidence_router_exact_mt5/PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh`

Expected output ZIP:

`runtime/v43_confidence_router_exact_mt5/OUTPUT_V43/v43_confidence_router_exact_mt5.zip`

One run -> one ZIP. Upload only the ZIP when available.
