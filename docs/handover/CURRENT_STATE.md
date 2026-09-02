# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 02:25 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

## Current objective

Do not wait for natural V69 fills or the obsolete `2 trades / 48h` dashboard gate.

Actual DEMO execution transport is already proven. The live no-trade path has now been localized one layer earlier: preserved `V64_ENTRY_EVAL.csv` shows the richest observed pre-pending source selected the opposite direction on every recorded evaluation, and frozen LONG-only direction isolation rejected those candidates before `PENDING_ARM`.

The immediate gate is to aggregate and deduplicate all preserved ENTRY_EVAL roots so archived copies are not double-counted, then determine whether any preserved LONG selector candidate exists outside the richest 46-row source.

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

- `V69_ACTUAL_DEMO_EXECUTION_VERIFIED=1`;
- BUY `0.01 XAUUSDm` open retcode `10009`, comment `done`, price `4377.736`;
- immediate probe-owned close retcode `10009`, comment `done`, price `4377.476`;
- free margin `$39.74`;
- terminal exited gracefully.

This proves MT5 <-> broker market-order transport can open and close `0.01 XAUUSDm` on the current DEMO account. Do not return to generic lot/broker/transport suspicion without contradictory evidence. The probe proves transport only; it does not prove strategy edge or authorize REAL.

## Latest operator evidence — direction isolation before pending arm

Operator ran the enhanced read-only upstream diagnostic at exact checkpoint:

`931caf8949564ecaad65a524a9f55f16f044593d`

The run passed repository/Python/tests/secret scan and finished with:

- `V69_UPSTREAM_TOTAL_EVENT_ROWS=0`;
- `V69_UPSTREAM_SOURCES_WITH_EVENT_ROWS=0`;
- `PENDING_ARM=0` and every later pending/reclaim stage `0`;
- `V69_UPSTREAM_DIAGNOSTIC=PASS`;
- MT5 remained running;
- orders sent `0`;
- REAL authorization `0`.

Pre-pending ENTRY_EVAL evidence:

- richest source: `_v69_forward_previous_20260901_140447_333776Z`;
- richest-source rows `46`;
- raw rows summed across four roots `83`;
- roots with rows `4`;
- classification `DIRECTION_ISOLATION_BLOCK_BEFORE_PENDING_ARM`;
- dominant blocker `direction_isolated_out`;
- decision reasons on richest source: `{"short_edge": 46}`;
- reject reasons: `{"direction_isolated_out": 46}`;
- selected directions: `{"-1": 46}`.

Therefore the observed live no-trade path is no longer ambiguous at the richest source: the selector produced opposite-direction candidates and frozen LONG-only isolation rejected them before pending-arm creation. Broker transport, reclaim, separation and retest were not the active blockers for those 46 evaluations.

Do **not** enable SHORT from this result.

## Meaning of `short_edge`

Inherited V59 selector logic requires the short side to satisfy all of the following before returning `short_edge` / direction `-1`:

- short HTF regime: `h1_trend == -1 && h4_trend != 1`;
- at least one short trigger: BOS/CHOCH, FVG, liquidity sweep, order-block retest, or aligned pullback/M15 trend;
- short score meets the configured minimum;
- short-minus-long score edge meets the configured minimum.

So `short_edge` is not an arbitrary label. It means the code's SHORT eligibility predicate passed on those rows. It does not independently prove objective future market direction or profitable SHORT expectancy.

## Why raw `83` rows are not yet an economic sample size

`V64_ENTRY_EVAL.csv` exists in current and rotated FILE_COMMON roots. Archive rotation can copy the same historical rows into more than one preserved root. Summing root row counts can therefore double-count the same evaluation.

Use exact-row deduplication before interpreting aggregate selector frequencies. The raw `83` is a storage count across four roots, not yet a count of unique market evaluations.

## Read-only diagnostic v4

Current branch code checkpoint `56787feaf6370da4cd766d917ad602bdb40f01fa` passed all five CI workflows and adds diagnostic-only aggregation. Strategy semantics are unchanged.

`analyze_v69_pre_pending_eval.py` now:

- aggregates every current/archive `V64_ENTRY_EVAL.csv` root;
- removes exact duplicate rows across rotated roots;
- reconstructs the selector's HTF regime predicates;
- reconstructs LONG/SHORT trigger state from logged feature columns;
- compares long/short scores;
- reports H1/H4 trend distributions;
- reports selected direction by HTF regime and trigger state;
- reports component-direction counts for structure, BOS/CHOCH, FVG, sweep, order-block retest, pullback, DI, MACD and location;
- reports score min/max/mean and long-minus-short margin;
- reports per-root summaries.

Key new runtime markers:

- `V69_PRE_PENDING_ALL_RAW_ROWS`;
- `V69_PRE_PENDING_ALL_UNIQUE_ROWS`;
- `V69_PRE_PENDING_ALL_DUPLICATE_ROWS_REMOVED`;
- `V69_PRE_PENDING_ALL_CONTEXT`;
- `V69_PRE_PENDING_ALL_SELECTED_DIRECTIONS`;
- `V69_PRE_PENDING_ALL_HTF_REGIMES`;
- `V69_PRE_PENDING_ALL_TRIGGER_STATES`;
- `V69_PRE_PENDING_ALL_SCORE_RELATIONS`;
- `V69_PRE_PENDING_ALL_SCORE_SUMMARY`;
- `V69_PRE_PENDING_ALL_SOURCE_SUMMARY`.

Context classification intentionally distinguishes:

- all unique rows are short-edge in selector-defined short HTF regime -> LONG-only abstention is internally consistent; keep SHORT disabled;
- any preserved LONG selector rows exist -> localize their downstream rejection/archetype/stop path;
- all rows selected SHORT but regime/trigger/score context is inconsistent -> review selector/telemetry consistency;
- mixed evidence -> compare context before strategy changes.

The diagnostic remains strictly read-only: no MetaEditor, no MT5 restart, no order path, no strategy threshold mutation.

## Legacy dashboard warning

The dashboard may still display `Closed 0/2` and `wait until 48h cap`. That UI is obsolete as a project gate. Do not wait for it.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_PENDING_STATE_EVENTS_ACROSS_PRESERVED_SOURCES=0`

`V69_RICHEST_PRE_PENDING_ROWS=46`

`V69_RICHEST_PRE_PENDING_DECISION=SHORT_EDGE_46_OF_46`

`V69_RICHEST_PRE_PENDING_REJECTION=DIRECTION_ISOLATED_OUT_46_OF_46`

`V69_RICHEST_PRE_PENDING_SELECTED_DIRECTION=SHORT_46_OF_46`

`V69_RAW_ENTRY_EVAL_ROWS_ACROSS_ROOTS=83_NEEDS_DEDUP`

`V69_LIVE_NO_TRADE_BLOCKER=DIRECTION_SELECTION_OR_REGIME_ABSTENTION_BEFORE_PENDING_ARM`

`V69_SHORT_ENABLED=0`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Do not rerun the DEMO execution probe.
2. Do not wait for natural trades or 48 hours.
3. Keep MT5 running.
4. Fast-forward to the final exact CI-green branch HEAD and run the same read-only upstream launcher once.
5. Interpret only the deduplicated `V69_PRE_PENDING_ALL_*` markers for cross-root selector frequency.
6. If all unique rows are `short_edge` in selector-defined short HTF regime, treat frozen LONG inactivity as regime abstention, not a runtime bug; do not loosen LONG merely to force trades and do not activate historical SHORT.
7. If any unique LONG selector rows exist, localize their reject reasons and earliest downstream gate before designing strategy changes.
8. Only after this aggregate diagnosis decide the separate economic research direction: improve LONG regime/candidate quality or start a separately validated SHORT/successor research line.
9. REAL remains a separate explicit fail-closed deployment/risk decision.
