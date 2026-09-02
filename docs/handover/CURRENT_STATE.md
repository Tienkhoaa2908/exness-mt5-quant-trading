# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve the current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, and relevant exact-HEAD CI before changing code or instructing the operator.

## Current objective

The project is no longer waiting for natural V69 fills. Actual DEMO transport has now been proven. The immediate blocker is upstream signal generation / state gating before reclaim confirmation.

Current diagnostic sequence:

1. keep frozen V69 strategy semantics unchanged;
2. use already-collected live telemetry, including archived forward roots;
3. locate the earliest upstream gate suppressing visible market opportunities;
4. only then decide whether to revise candidate-generation architecture or build the session-volatility successor;
5. progress toward a separate fail-closed REAL deployment package after the alpha/runtime diagnosis is complete.

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
- current live validation DEMO only;
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

## Actual Windows real-readiness result — execution transport PASS

Operator successfully ran corrected code checkpoint:

`614d68eca2fd30dbfe98adad02f82d61a0302aca`

The run passed repository/Python/static/secret gates and compiled `V69DemoExecutionProbe` with `0 errors, 0 warnings`.

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

This proves the MT5 <-> broker market-order transport can actually open and close `0.01 XAUUSDm` on the current DEMO account. Do not keep treating generic real-time deployment transport, lot size, or broker fill capability as the primary no-trade blocker unless new contradictory evidence appears.

The probe is transport evidence only; it does not prove strategy edge or authorize REAL.

## Live signal funnel before the successful probe

The same run snapshotted the already-collected live V69 telemetry before the probe and reported:

- `POST_ZONE_REVERSAL_CONFIRM=0`;
- `POST_CONFIRM_SEPARATION=0`;
- `POST_CONFIRM_RETEST_READY=0`;
- `POST_CONFIRM_ENTRY_READY=0`;
- natural closed V69 deals `0`;
- classification `NO_V69_RECLAIM_CONFIRM_OBSERVED`.

Therefore V69 never reached the point where its separation/retest/entry-ready/order-send logic could run during that observed window. The no-trade result cannot be attributed to the integrated `g_trade.Buy()` path from this window.

The current blocker is **upstream of `POST_ZONE_REVERSAL_CONFIRM`**.

## Preserved telemetry

When frozen V69 was automatically relaunched after the successful probe, the pre-probe root was archived as:

`Common\Files\mt5_quant\_v69_forward_previous_20260902_182142_999701Z`

That archive should contain the fuller event stream from the preceding live period and is the primary source for immediate upstream diagnosis. The current `v69_frozen_forward_demo` root is also analyzed read-only.

## New upstream diagnostic

Read-only components added after the successful execution probe:

- `scripts/analyze_v69_upstream_signal_funnel.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh`;
- `tests/test_v69_upstream_signal_diag.py`;
- `.github/workflows/v69_upstream_diag_quality.yml`.

The diagnostic automatically selects the richest current/archive telemetry root and counts:

`PENDING_ARM -> MICRO_ENTRY_ARM -> MICRO_ENTRY_ZONE_TOUCH -> MICRO_ENTRY_PENETRATION -> POST_ZONE_CONFIRM_WAIT -> POST_ZONE_REVERSAL_CONFIRM -> POST_CONFIRM_SEPARATION -> POST_CONFIRM_RETEST_READY -> POST_CONFIRM_ENTRY_READY`

It also counts post-zone invalidation/expiry events and closed-M1 confirm-wait reasons such as:

- `zone_penetration_not_ready`;
- `m1_history_not_ready`;
- `closed_bar_predates_zone_touch`;
- `m1_atr_not_ready`;
- `reclaim_body_too_small`;
- `reclaim_body_fraction_weak`;
- `reclaim_close_location_weak`;
- `reclaim_candle_wrong_direction`;
- `reclaim_no_close_progress`;
- `reclaim_distance_from_extreme_weak`.

The diagnostic is strictly read-only: MT5 may remain running, MetaEditor is not used, terminal is not restarted, and no order path exists.

## Legacy dashboard warning

The pinned dashboard may still display `Closed 0/2` and `wait until 48h cap`. That is obsolete legacy smoke UI, not the current project gate. Do not wait for it.

## Session-volatility successor research

`docs/research/SESSION_VOLATILITY_RESEARCH.md` defines a separate development track using DST-aware session labels, past-only volatility percentiles, spread/range efficiency, directional persistence, breakout follow-through, MFE/MAE and expectancy by symbol/session.

Session information is a conditioning feature, not a hard-coded `NEW_YORK = TRADE` rule. It may become part of a successor architecture after the current upstream suppression is quantified.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_EXECUTION_PROBE_OPEN_RETCODE=10009`

`V69_EXECUTION_PROBE_CLOSE_RETCODE=10009`

`V69_PRE_PROBE_RECLAIM_CONFIRM=0`

`V69_PRE_PROBE_ENTRY_READY=0`

`V69_NO_TRADE_BLOCKER=UPSTREAM_SIGNAL_OR_STATE_GATING`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`SESSION_VOLATILITY_RESEARCH=DEVELOPMENT_ONLY`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Do not rerun the DEMO execution probe; transport purpose is complete.
2. Do not wait for two natural trades or 48 hours.
3. Run the read-only upstream signal diagnostic on the exact CI-green branch HEAD while MT5 remains running.
4. Use its stage counts and dominant blocker to decide whether the live suppression comes from initial setup/BOS eligibility, micro-entry arm, zone return, penetration depth, or closed-M1 reclaim quality.
5. Only after that diagnosis design a successor or revise upstream candidate generation on a separate development branch.
6. REAL remains a separate explicit fail-closed deployment/risk decision.
