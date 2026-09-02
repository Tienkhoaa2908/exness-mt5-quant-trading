# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 (+07)

## User input

Operator supplied the complete corrected real-readiness terminal run from code checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca`.

This supersedes the previous state where probe completion was unknown.

## Mandatory state inspection

This turn re-resolved the active remote branch and re-read:

- `OPERATING_PROTOCOL.md`;
- `CURRENT_STATE.md`;
- `KNOWN_FAILURES.md`;
- prior `TURN_SYNC.md`;
- current signal-path analyzer;
- V67/V69 upstream event architecture;
- active CI/runtime contracts.

## Strongest new evidence

### Signal funnel before probe

The already-collected live V69 telemetry reported:

- `V69_PRE_PROBE_SIGNAL_PATH_CLASSIFICATION=NO_V69_RECLAIM_CONFIRM_OBSERVED`;
- `POST_ZONE_REVERSAL_CONFIRM=0`;
- `POST_CONFIRM_SEPARATION=0`;
- `POST_CONFIRM_RETEST_READY=0`;
- `POST_CONFIRM_ENTRY_READY=0`;
- natural closed deals `0`.

Conclusion: during the observed no-trade window, V69 never reached reclaim confirmation. Therefore V69 separation/retest/entry-ready/order-send code was not exercised by a natural setup.

### Actual DEMO transport probe

`V69DemoExecutionProbe` compiled with `0 errors, 0 warnings`.

Identity:

- source SHA256 `150131300630fdf23d14c273494a9190a340bf05e1ffea8376d0a56fc160b278`;
- EX5 SHA256 `25bbde5a813e7e5fa6c046a1dc1374a728253e127709079594c10daf44fad3be`;
- magic `699901`;
- XAUUSDm;
- 0.01 lot;
- DEMO only.

Execution:

- actual BUY open PASS;
- open retcode `10009`, comment `done`, price `4377.736`;
- immediate close of the probe-owned position PASS;
- close retcode `10009`, comment `done`, price `4377.476`;
- free margin `$39.74`;
- probe terminal closed gracefully `rc=0`;
- `V69_ACTUAL_DEMO_EXECUTION_VERIFIED=1`.

Conclusion: MT5 <-> broker actual market transport for `0.01 XAUUSDm` is proven. Generic deployment/lot/broker-fill capability is not the current no-trade blocker.

### Frozen V69 relaunch after probe

Automatic relaunch succeeded:

- broker health READY twice;
- `V69_SYSTEM_HEALTH=READY`;
- `V69_BROKER_PREFLIGHT_READY=1`;
- `V69_RUNTIME_SMOKE_VERIFIED=1`;
- background console disabled;
- dashboard pinned;
- strategy unchanged;
- LONG only;
- SHORT disabled;
- REAL authorization false.

Pre-probe forward telemetry was archived to:

`Common\Files\mt5_quant\_v69_forward_previous_20260902_182142_999701Z`

This archive is now the preferred source for deeper upstream diagnosis because it contains the older no-trade observation window.

## Diagnostic conclusion

Do **not** wait for the dashboard's obsolete `2 trades / 48h` gate.

Do **not** rerun the forced execution probe; its transport purpose is complete.

Current blocker classification:

`UPSTREAM_SIGNAL_OR_STATE_GATING_BEFORE_POST_ZONE_REVERSAL_CONFIRM`

The next question is not whether MT5 can send an order. The next question is which earlier gate rejected the market opportunities the operator visually expected to qualify.

## Code added this turn

A read-only upstream signal diagnostic was added:

- `scripts/analyze_v69_upstream_signal_funnel.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG.py`;
- `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh`;
- `tests/test_v69_upstream_signal_diag.py`;
- `.github/workflows/v69_upstream_diag_quality.yml`.

It auto-discovers current and `_v69_forward_previous_*` telemetry roots and selects the richest event stream.

It counts the upstream funnel:

`PENDING_ARM -> MICRO_ENTRY_ARM -> MICRO_ENTRY_ZONE_TOUCH -> MICRO_ENTRY_PENETRATION -> POST_ZONE_CONFIRM_WAIT -> POST_ZONE_REVERSAL_CONFIRM -> POST_CONFIRM_SEPARATION -> POST_CONFIRM_RETEST_READY -> POST_CONFIRM_ENTRY_READY`

It also reports:

- invalidation/expiry events;
- confirm-wait reason counts;
- dominant blocker;
- next diagnostic/action;
- top raw event counts.

Safety contract:

- strictly read-only;
- MT5 may remain running;
- no MetaEditor;
- no terminal restart;
- no order functions;
- no REAL authorization.

## Documentation changes

`CURRENT_STATE.md` now records actual execution PASS and moves the blocker upstream.

`KNOWN_FAILURES.md` now records:

- actual transport PASS + zero reclaim-confirm as the decisive localization lesson;
- expected-HEAD bridge incident as resolved;
- do not rerun forced transport probes without new contradictory evidence.

## Strategy status

Frozen V69 has not been changed.

Historical V69 replay remains development-only, regime-concentrated evidence.

Session-volatility/New York research remains a separate successor research track; it must not be used as a hard-coded session-open trade rule.

## Safety status

- current live runtime DEMO only;
- LONG only;
- SHORT disabled;
- REAL authorization false;
- actual probe PASS does not authorize REAL.

## Next operator action

After the final code/documentation HEAD passes exact-head CI:

1. leave MT5 running;
2. fast-forward only to the exact final HEAD;
3. run one Git Bash launcher: `runtime/v69_real_readiness_probe/RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh`;
4. return the markers from `V69_UPSTREAM_SOURCE_ROOT=` through `V69_UPSTREAM_DIAGNOSTIC=PASS` or the first `FATAL`;
5. do not wait for another natural trade before interpreting the result.
