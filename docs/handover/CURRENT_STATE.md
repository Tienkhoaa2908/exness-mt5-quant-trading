# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 02:55 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

## Current objective

The observed V69 live no-trade window has been localized. Do not keep diagnosing broker execution, reclaim, separation or retest for this window.

The next question is economic/coverage-oriented: **how often does the unchanged V69 direction selector produce LONG, SHORT or neutral outcomes across all closed M15 bars?** The 83 preserved live `V64_ENTRY_EVAL.csv` rows are candidate/evaluation rows, not an all-bar coverage sample.

Use the read-only selector-coverage recovery tool. It reuses the existing V64 all-bar screen only after proving its feature/scoring/selector functions and score thresholds are identical to frozen V69. This is development observability only, not independent edge evidence.

REAL money remains unauthorized. SHORT remains disabled/rejected.

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

Actual broker execution:

- one BUY `0.01 XAUUSDm` opened successfully, retcode `10009 / done`;
- the probe-owned position closed immediately, retcode `10009 / done`;
- free margin `$39.74`;
- terminal exited gracefully.

This proves MT5 <-> broker market-order transport for the current DEMO account. Do not rerun the forced transport probe unless contradictory evidence appears. Transport PASS does not prove strategy edge or authorize REAL.

## Decisive live selector evidence — PASS

Operator ran the aggregate read-only upstream diagnostic at exact checkpoint:

`9ca2ac66b4c82f5b2f5c51184259d7147486c5a9`

The diagnostic passed with MT5 left running, no MetaEditor, no orders and REAL authorization false.

Across preserved ENTRY_EVAL roots:

- raw rows `83`;
- unique rows `83`;
- duplicate rows removed `0`;
- decision reason `short_edge`: `83/83`;
- reject reason `direction_isolated_out`: `83/83`;
- selected direction `-1`: `83/83`;
- selector-defined `SHORT_HTF_REGIME`: `83/83`;
- H1 trend `-1`: `83/83`;
- H4 trend `-1`: `83/83`;
- score relation `SHORT_SCORE_HIGHER`: `83/83`;
- triggers: `SHORT_TRIGGER_ONLY=59`, `BOTH_TRIGGERS=24`;
- long score min/mean/max `-11 / -7.6265 / -1`;
- short score min/mean/max `8 / 10.2892 / 15`;
- long-minus-short margin min/mean/max `-25 / -17.9157 / -9`.

Aggregate context:

`ALL_UNIQUE_EVALS_SHORT_EDGE_IN_SHORT_HTF_REGIME`

This locks the no-trade interpretation for the observed evaluated candidates: **frozen V69 LONG-only abstained consistently with its unchanged direction selector.** There was no preserved LONG selector candidate among these 83 evaluations. Broker transport, reclaim, separation and retest were not the active blockers for these rows.

Do not loosen LONG merely to manufacture turnover. Do not enable the rejected historical SHORT path.

## Important nuance: 83 evaluations are not all closed M15 bars

The inherited V62/V69 `EvaluateBar` path returns before writing `V64_ENTRY_EVAL.csv` when:

- `V64BuildFeatures()` fails; or
- `V64SelectDirection()` returns `d==0`.

Therefore `83/83 SHORT` means **83/83 recorded directional evaluations were SHORT**, not that 100% of all M15 bars in the calendar window were bearish/SHORT-eligible.

All-bar coverage must include feature-not-ready and neutral/`d==0` bars before estimating LONG opportunity frequency.

## Selector coverage recovery — read-only development tool

Current branch now contains:

- `scripts/analyze_v69_selector_coverage_recovery.py`;
- `runtime/v69_selector_coverage_recovery/RUN_V69_SELECTOR_COVERAGE_RECOVERY.py`;
- `runtime/v69_selector_coverage_recovery/RUN_V69_SELECTOR_COVERAGE_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_selector_coverage_recovery.py`;
- CI coverage in `.github/workflows/v69_upstream_diag_quality.yml`.

The tool:

1. reads the existing V64 all-bar directional-screen source and `screen/V64_ENTRY_EVAL.csv`, or recovers them read-only from the accepted local V64 evidence ZIP;
2. generates the current frozen V69 source;
3. compares the exact normalized directional core functions `V64EMA`, `V64ATR`, `V64RSI`, pivots/swings, FVG, DI/ADX, order-block retest, score, feature builder and selector;
4. compares `InpV64MinDirectionalScore` and `InpV64MinScoreEdge` defaults;
5. fails closed on any mismatch;
6. only on exact identity, counts every unique M15 screen row including neutral and feature-not-ready rows;
7. reports LONG/SHORT/neutral percentages, HTF regimes, decision reasons, score statistics and monthly coverage.

Repository-level CI additionally generates the V64 all-bar screen and frozen V69 source and confirms their directional core + score thresholds match exactly.

This recovery does not restart MT5, does not invoke MetaEditor, sends no orders, changes no strategy semantics and does not authorize REAL or SHORT.

Coverage recovered from reused historical screen output is **development coverage**, not independent V69 edge evidence.

## Legacy dashboard warning

The dashboard may still display `Closed 0/2` and `wait until 48h cap`. That UI is obsolete as a project gate. Do not wait for it and do not restart healthy MT5 just to change the text.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_PENDING_STATE_EVENTS_ACROSS_PRESERVED_SOURCES=0`

`V69_PRE_PENDING_UNIQUE_EVAL_ROWS=83`

`V69_PRE_PENDING_SHORT_EDGE=83_OF_83`

`V69_PRE_PENDING_DIRECTION_ISOLATED_OUT=83_OF_83`

`V69_PRE_PENDING_SHORT_HTF_REGIME=83_OF_83`

`V69_PRE_PENDING_H1_SHORT=83_OF_83`

`V69_PRE_PENDING_H4_SHORT=83_OF_83`

`V69_PRE_PENDING_SHORT_SCORE_HIGHER=83_OF_83`

`V69_LIVE_NO_TRADE_PRIMARY_CAUSE=LONG_ONLY_REGIME_ABSTENTION_IN_OBSERVED_DIRECTIONAL_EVALUATIONS`

`V69_NO_LONG_DIRECTIONAL_CANDIDATES_IN_83_EVALS=1`

`V69_83_EVALS_DO_NOT_EQUAL_ALL_M15_BARS=1`

`V69_NEXT_GATE=ALL_BAR_SELECTOR_COVERAGE_RECOVERY`

`V69_SHORT_ENABLED=0`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Do not rerun the DEMO execution probe.
2. Do not rerun the upstream event/pre-pending diagnostic; its observed-window blocker is settled.
3. Do not wait for natural trades or 48 hours.
4. Keep MT5 running.
5. Run the read-only selector-coverage recovery on the final exact CI-green branch HEAD.
6. If existing V64 all-bar evidence is missing locally, do not stop MT5 just to regenerate it; return the fail-closed message and choose a non-disruptive fallback.
7. If directional-core identity fails, do not override it and do not reuse incompatible historical screen evidence.
8. If identity passes, use all-bar LONG/SHORT/neutral coverage and monthly distribution to decide whether LONG-only opportunity is intrinsically sparse and whether a **separate** bearish-regime challenger deserves research.
9. Any bearish-regime challenger must be a new research line; it is not permission to reactivate rejected V69 SHORT.
10. REAL remains a separate explicit fail-closed deployment/risk decision.
