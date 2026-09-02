# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 02:xx (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

## Current objective

Do not wait for natural V69 fills or the obsolete `2 trades / 48h` dashboard gate.

Actual DEMO execution transport has been proven. The immediate task is to localize why the frozen V69 LONG pipeline did not arm a pending candidate during the observed live window. The current diagnostic now reads both pending-state events and the earlier directional-evaluation telemetry.

REAL money remains unauthorized.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Contract:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only for current live diagnosis;
- SHORT disabled/rejected;
- REAL authorization false;
- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- reclaim -> favorable separation `>= $1.30` -> later retest -> confirmation age `>=30s` -> `POST_CONFIRM_ENTRY_READY` -> `V64OrderPreflight`;
- fixed structural stop, no widening/clamp.

The `$1.30` and `30s` values are development choices, not proven universal optima.

## Development evidence

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all ten V68 winners while removing four losers, but `10/14` surviving V69 losers closed within 60 seconds. Monthly replay is regime-concentrated: Sep `-$1.84`, Oct `+$9.15`, Nov `+$1.24`, Dec `-$2.28`, Jan `+$0.87`, Feb-May flat; excluding October `-$2.01`.

Sep 2025-May 2026 V69 replay is development evidence, not an independent holdout.

## Actual DEMO execution transport — PASS

Corrected real-readiness execution probe checkpoint:

`614d68eca2fd30dbfe98adad02f82d61a0302aca`

Probe identity:

- source SHA256 `150131300630fdf23d14c273494a9190a340bf05e1ffea8376d0a56fc160b278`;
- EX5 SHA256 `25bbde5a813e7e5fa6c046a1dc1374a728253e127709079594c10daf44fad3be`;
- unique diagnostic magic `699901`;
- DEMO `XAUUSDm`, fixed `0.01` lot.

Actual broker execution:

- `V69_ACTUAL_DEMO_EXECUTION_VERIFIED=1`;
- BUY open retcode `10009`, comment `done`, price `4377.736`;
- immediate probe-owned close retcode `10009`, comment `done`, price `4377.476`;
- free margin reported `$39.74`;
- probe terminal closed gracefully `rc=0`.

This proves MT5 <-> broker market-order transport can open and close `0.01 XAUUSDm` on the current DEMO account. Do not return to generic lot/broker/transport suspicion without contradictory evidence.

The probe proves transport only; it does not prove strategy edge or authorize REAL.

## Live signal evidence — latest result

The pre-probe snapshot had zero post-confirm stages:

- `POST_ZONE_REVERSAL_CONFIRM=0`;
- `POST_CONFIRM_SEPARATION=0`;
- `POST_CONFIRM_RETEST_READY=0`;
- `POST_CONFIRM_ENTRY_READY=0`;
- natural closed V69 deals `0`.

The operator then ran the corrected read-only upstream diagnostic at local checkpoint `5f427b7b584539f0bb8dc1652a13c713460cac63`.

Across 8 preserved sources it reported:

- `V69_UPSTREAM_TOTAL_EVENT_ROWS=0`;
- `V69_UPSTREAM_SOURCES_WITH_EVENT_ROWS=0`;
- `PENDING_ARM=0`;
- `MICRO_ENTRY_ARM=0`;
- `MICRO_ENTRY_ZONE_TOUCH=0`;
- `MICRO_ENTRY_PENETRATION=0`;
- `POST_ZONE_CONFIRM_WAIT=0`;
- `POST_ZONE_REVERSAL_CONFIRM=0`;
- all later V69 stages `0`;
- classification `INITIAL_SETUP_OR_PENDING_ARM_BLOCK`;
- diagnostic and launcher PASS.

This is valid evidence that **no instrumented pending-state event occurred**. It is not sufficient evidence that there was no market signal or selector candidate.

## Critical telemetry interpretation before `PENDING_ARM`

The inherited V64/V69 lineage does not write every pre-pending rejection to `V64_EVENTS.csv`.

Before `PENDING_ARM`:

1. `BuildFeatures` runs on a new M15 bar.
2. `SelectDirection` may return `d==0`; current code then returns without a pending event and without a directional-evaluation row.
3. An opposite selector may be logged to `V64_ENTRY_EVAL.csv` as `direction_isolated_out`.
4. A LONG selector can fail `V64ClassifyArchetype` and log `no_complete_archetype` to `V64_ENTRY_EVAL.csv` without creating `PENDING_ARM`.
5. Invalid raw M15 stop geometry can log `invalid_arm_structural_stop` to `V64_ENTRY_EVAL.csv` without creating `PENDING_ARM`.
6. Only a successful arm writes the `PENDING_ARM` event.

Therefore `V64_EVENTS=0` must not be translated into `no signal`. The next evidence source is `V64_ENTRY_EVAL.csv`.

## Enhanced read-only diagnostic

Current branch now includes:

- `scripts/analyze_v69_upstream_signal_funnel.py`;
- `scripts/analyze_v69_pre_pending_eval.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh`;
- `tests/test_v69_upstream_signal_diag.py`;
- `.github/workflows/v69_upstream_diag_quality.yml`.

The enhanced diagnostic reads current and archived `V64_ENTRY_EVAL.csv` in addition to `V64_EVENTS.csv` and reports:

- decision-reason counts;
- reject-reason counts;
- selected-direction counts;
- pre-pending evaluation rows;
- dominant pre-pending blocker.

Interpretation:

- dominant `no_complete_archetype` -> archetype completion/candidate construction is suppressing arms;
- dominant `invalid_arm_structural_stop` -> M15 structural stop geometry blocks arms;
- dominant `direction_isolated_out` -> selected candidates were opposite direction and LONG-only isolation suppressed them; SHORT remains disabled;
- `pending_*` eval rows with no `PENDING_ARM` -> telemetry/state integration review;
- zero `V64_ENTRY_EVAL` rows as well -> current observability ends before selector return; next step is an observability-only `EvaluateBar` tracer for feature readiness, H4/H1 regime, trigger, score and score-edge gates.

This diagnostic is strictly read-only. MT5 may remain running. It sends no orders and does not change V69 semantics.

## Preserved telemetry

Pre-probe forward telemetry was archived at:

`Common\Files\mt5_quant\_v69_forward_previous_20260902_182142_999701Z`

The current `v69_frozen_forward_demo` root and all `_v69_forward_previous_*` roots are eligible read-only sources.

## Legacy dashboard warning

The pinned dashboard may still display `Closed 0/2` and `wait until 48h cap`. That is obsolete UI, not a project gate. Do not wait for it.

## Session-volatility successor research

`docs/research/SESSION_VOLATILITY_RESEARCH.md` defines a separate development track using DST-aware session labels, past-only volatility percentiles, spread/range efficiency, directional persistence, breakout follow-through, MFE/MAE and expectancy by symbol/session.

Session information is a conditioning feature, not a hard-coded `NEW_YORK = TRADE` rule. Do not mutate frozen V69 with this research during diagnosis.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_EXECUTION_PROBE_OPEN_RETCODE=10009`

`V69_EXECUTION_PROBE_CLOSE_RETCODE=10009`

`V69_PENDING_STATE_EVENTS_ACROSS_PRESERVED_SOURCES=0`

`V69_PENDING_ARM_OBSERVED=0`

`V69_EVENTS_ZERO_DOES_NOT_PROVE_NO_SELECTOR_SIGNAL=1`

`V69_NEXT_EVIDENCE_SOURCE=V64_ENTRY_EVAL.csv`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`SESSION_VOLATILITY_RESEARCH=DEVELOPMENT_ONLY`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Do not rerun the DEMO execution probe.
2. Do not wait for natural trades or 48 hours.
3. Keep MT5 running.
4. Run the enhanced read-only upstream diagnostic on the final exact CI-green branch HEAD.
5. Use `V69_PRE_PENDING_*` counts to localize selector/archetype/arm suppression.
6. If `V64_ENTRY_EVAL` is also empty across preserved roots, add an observability-only `EvaluateBar` gate tracer on a separate diagnostic build; do not alter strategy thresholds.
7. Only after the pre-pending blocker is quantified decide whether to revise candidate-generation architecture or advance a session-volatility successor.
8. REAL remains a separate explicit fail-closed deployment/risk decision.
