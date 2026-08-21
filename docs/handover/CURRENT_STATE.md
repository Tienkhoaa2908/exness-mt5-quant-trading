# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-21

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Do not remove tester/live guards or add native/external broker-order paths.
- V44 PASS can authorize PAPER/DEMO research only.

## Source of truth

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

Current campaign branch:

`agent/v44-baseline-robustness-validation`

V43 confidence-aware router research remains on its separate branch and is
paused while V44 validates the existing baseline family. V44 branches from
accepted V42 HOLD/runtime-packaging fix commit
`e96262f4600e57cd956a9a78f3e717dca8b24ccb`.

Do not use `git clean`. Accepted ZIPs, `.venv`, state, compiled artifacts,
checkpoints and completed MT5 outputs may be untracked recovery assets.

Read together:

- `docs/handover/RECOVERY_PROMPT.md`
- `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
- `docs/research/v44_baseline_robustness_validation_plan.md`
- `docs/adr/ADR-044-baseline-robustness-before-deployment.md`

## Accepted exact baseline

Return control:

`adaptive_ewma_hl8_thr0` / `usd40_r1p0_cent_continuous`

Accepted exact 2025-08-01 -> 2026-08-01:

- start $40.00;
- end $107.432645;
- total return +168.5816%;
- geometric/month 8.58163%;
- max DD 9.9038%;
- 563 trades;
- AvgR 0.214608R;
- PF 1.500756;
- 11/12 positive months.

This is strong research evidence but not proof of future return or live
readiness.

Historical exact threshold comparators:

- `adaptive_ewma_hl8_thr0p05`: $111.285257, 8.900900%/month, DD 10.4368%,
  531 trades, PF 1.521009.
- `adaptive_ewma_hl10_thr0p05`: $110.025682, 8.797648%/month, DD 9.8587%,
  537 trades, PF 1.530107.

These are hypotheses, not promoted policies.

## Recent research decisions

- V39 = HOLD.
- V40 = HOLD.
- V41 = HOLD.
- V42 exact = HOLD. Best V42 challenger ended $106.387574 / 8.493214% month,
  below the control. Global direction-switch hysteresis improved quality/DD
  but cut participation/right-tail compounding.
- V43 confidence-aware routing is paused, not rejected. V44 takes priority
  because broad baseline validation is now more valuable than another
  development-window optimization cycle.

Accepted V42 completed-output RAR SHA:
`3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`.

Recovered canonical V42 ZIP SHA:
`3176850e89e1c36ac87be7ff827d34209646da10aaeacfe0d0a013ebeeaa6066`.

## V44 campaign

Goal: validate the frozen baseline family broadly and harden the deployment
pipeline before any escalation.

Frozen candidates:

1. `adaptive_ewma_hl8_thr0`
2. `adaptive_ewma_hl8_thr0p05`
3. `adaptive_ewma_hl10_thr0p05`

No V44 window may be used to retune these parameters.

Exact protocol:

- 12 monthly restart windows;
- 4 sequential 3-month quarter blocks;
- 2 half-year restart windows;
- 1 annual window;
- total 19 exact MT5 windows.

All use XAUUSDm / M15 / Model=0 / Deposit=$40 / leverage 1:200 / Strategy
Tester only.

Every independent window starts from accepted state SHA
`5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`.
This deliberately measures restart/deployment-date robustness. The annual run
also provides the continuous monthly path for restart-vs-continuous comparison.

## V44 source/provenance

Immutable V38 ZIP SHA:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.

Immutable V38 parent source SHA:
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

V44 changes release/output markers and disables expensive telemetry only.
Candidate catalog/strategy logic/risk remain unchanged.

Frozen generated V44 source SHA:
`cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3`.

The annual exact window runs first and must reproduce the accepted control:
$107.432645, 563 trades, exact monthly trade-count vector and exact monthly
final-balance vector. Only then may the remaining 18 windows run.

## V44 readiness gate

`PAPER_DEMO_READY` requires all:

- annual total return >=100%;
- annual DD <=12.5%;
- annual PF >=1.30;
- positive monthly restart windows >=8/12;
- positive quarter blocks >=3/4;
- both half-year windows positive;
- worst restart month >=-10%;
- restart-vs-continuous monthly sign agreement >=9/12;
- annual turnover <=110% control;
- annual trade breadth >=85% control.

Additional friction diagnostics subtract 0.02R and 0.05R per annual trade.

`LIVE_AUTHORIZED=0` regardless of V44 result.

## Windows runtime recovery invariants

Mandatory details are in `WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`.

Key rules:

- immutable V38 parent; never bless historical builder drift;
- explicit UTF-8 / avoid CP1252;
- no `set +e` under global ERR trap;
- no runtime shell patcher/generated runner;
- compile success = frozen source SHA + 0 errors/0 warnings + EX5;
- MT5 completion = new LATEST + complete manifested artifacts;
- portable Python bundle manifest; never parse MSYS `sha256sum` text markers;
- package-only recovery after completed exact evidence;
- **do not rerun MT5** when a later stage alone failed;
- recovery ladder: provenance -> source -> compile -> MT5 -> collection ->
  analysis -> packaging.

## V44 entrypoints

One-shot:

`runtime/v44_baseline_validation/BOOTSTRAP_V44_BASELINE_VALIDATION_ONE_SHOT_GIT_BASH.sh`

Direct runner:

`runtime/v44_baseline_validation/RUN_V44_BASELINE_VALIDATION_EXACT_MT5_GIT_BASH.sh`

Package-only:

`runtime/v44_baseline_validation/PACKAGE_V44_EXISTING_OUTPUT_GIT_BASH.sh`

Expected ZIP:

`runtime/v44_baseline_validation/OUTPUT_V44/v44_baseline_robustness_validation.zip`
