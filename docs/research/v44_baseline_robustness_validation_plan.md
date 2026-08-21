# V44 Baseline Robustness & Deployment-Readiness Campaign

Date: 2026-08-21

## Goal

Stop adding overlays and validate the strongest baseline family broadly before any deployment escalation.

Frozen candidates:

1. `adaptive_ewma_hl8_thr0` — accepted return control.
2. `adaptive_ewma_hl8_thr0p05` — strongest historical exact ending equity.
3. `adaptive_ewma_hl10_thr0p05` — strongest historical exact PF/DD balance.

No parameter retuning is allowed on the V44 validation windows.

## Exact window protocol

All windows use XAUUSDm / M15 / Model=0 / Deposit=$40 / leverage 1:200 / tester only.

- 12 independent monthly restart windows from 2025-08 through 2026-07.
- 4 sequential 3-month quarter blocks.
- 2 sequential 6-month half-year blocks.
- 1 annual window 2025-08-01 through 2026-08-01.

Total exact MT5 windows: 19.

Every independent window restarts from accepted state SHA
`5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`.
This intentionally measures deployment/restart robustness. The annual run also supplies the normal continuous monthly path, allowing restart-vs-continuous comparison.

## Immutable source rule

V44 is built only from accepted V38 ZIP SHA
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`
and accepted V38 source SHA
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

V44 changes no strategy logic. It only changes release/output tags, disables expensive intra-trade telemetry, and adds validation/safety manifest markers.

Frozen V44 generated source SHA:
`cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3`.

## Annual preflight

The annual run executes first. Before the other 18 windows are allowed to run, the analyzer must reproduce:

- end `$107.432645`;
- 563 control trades;
- exact 12 monthly control trade-count vector;
- exact 12 monthly final-balance vector.

Failure invalidates V44 and stops the campaign.

## Readiness gate

The campaign is robustness validation, not same-window optimization.

A candidate is `PAPER_DEMO_READY` only if all hold:

- annual total return >=100%;
- annual max MTM DD <=12.5%;
- annual PF >=1.30;
- positive restart months >=8/12;
- positive restart quarter blocks >=3/4;
- both half-year restart windows positive;
- worst independent restart month >=-10%;
- monthly restart vs annual-continuous sign agreement >=9/12;
- annual turnover <=110% control;
- annual trade breadth >=85% control.

Additional friction diagnostics report annual total R after subtracting 0.02R and 0.05R per trade.

A PASS authorizes paper/demo research only. Real-money live trading remains forbidden.

## Recovery

Use the recovery ladder in `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`.

Checkpoint semantics:

- valid compile artifact => do not recompile;
- `MT5_DONE.txt` + run folder => collection-only recovery;
- `DONE.txt` => MT5 must not rerun;
- completed 19 checkpoints + aggregate analysis => package-only recovery;
- packaging failure never justifies rerunning MT5.

One run -> one ZIP:
`runtime/v44_baseline_validation/OUTPUT_V44/v44_baseline_robustness_validation.zip`.
