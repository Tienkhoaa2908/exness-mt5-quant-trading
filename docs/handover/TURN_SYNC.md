# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 19:25 (+07)

## User input

User requested a fresh GitHub-only restoration of the Exness / MetaTrader 5 Quant Trading System and a short status report covering active branch, exact HEAD, CI, current candidate, runtime state, current blocker and next gate.

The user explicitly required the canonical read order, strict separation of strategy/economic logic from broker/execution transport and harness/observability, no reliance on chat memory, one-shot operator ergonomics, no `git clean`, no `stash pop` during active runtime/evidence work, no manual EA attachment when automation can do it, silent background processes, SHORT disabled and REAL money fail-closed.

## State read before work

Repository authority was re-verified as:

`Tienkhoaa2908/exness-mt5-quant-trading`

`Tienkhoaa2908/vn-quant-system` was not modified.

Branch discovery showed that the frozen V69 lineage remains preserved but is no longer the newest active research branch. The canonical current research branch is:

`agent/v72-eurusd-independent-validation`

Remote HEAD before this documentation-only sync:

`8ae5b44fd1c90863c0d0ff3424f20b33ab675a14`

The required recovery sources were then read in order on that branch:

1. remote branch/HEAD;
2. `docs/handover/OPERATING_PROTOCOL.md`;
3. `docs/handover/CURRENT_STATE.md`;
4. `docs/handover/KNOWN_FAILURES.md`;
5. `docs/handover/TURN_SYNC.md`;
6. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`;
7. recent commits;
8. GitHub Actions on exact HEAD;
9. relevant runtime index/evidence state.

Exact pre-sync HEAD CI was fully green: `8/8` workflow runs associated with `8ae5b44fd1c90863c0d0ff3424f20b33ab675a14` were `completed/success`.

## Restored canonical state

### Frozen V69 baseline

The frozen V69 research identity remains intact and unchanged:

- branch `agent/v69-confirm-separation-retest-research`;
- frozen HEAD `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`;
- accepted V69 evidence ZIP SHA256 `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`;
- frozen forward parent source SHA256 `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`;
- XAUUSDm M15, LONG only, fixed lot `0.01`;
- SHORT disabled/rejected;
- REAL authorization false;
- accepted V69 development result `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`;
- Sep 2025-May 2026 replay remains development evidence, not an independent holdout.

Actual DEMO execution transport remains proven PASS. No new evidence justifies rerunning the forced transport probe.

### Research lineage after V69

V70 corrected actual position-lifetime excursion telemetry and did not promote the TIERED exit successor.

V71 tested direct no-retune FX portability with the frozen V69/V71 LONG semantics. EURUSD was the strongest FX screen but was based on only eight trades; AUDUSD ranked second with seven trades.

V72 then preregistered an untouched earlier EURUSD period using the exact V71 source and zero entry/exit retuning. Evidence collection and analysis passed, but the economic candidate failed the preregistered risk gate:

- `23 trades / 8W / 15L`;
- net `+$4.11`;
- PF `1.250457`;
- max realized DD `$10.23`;
- fixed preregistered DD ceiling `$5.00`.

Therefore `V72_ECONOMIC_CLASSIFICATION=FAIL` and unchanged EURUSD is rejected for promotion. The failed untouched period is consumed evidence and must not be used for post-hoc rescue tuning.

## Layer separation

### Strategy / economic logic

Current economic blocker is V72 EURUSD risk-path failure: max realized DD `$10.23` exceeded the preregistered `$5.00` ceiling. This is not a broker or harness diagnosis.

### Broker / execution transport

Generic DEMO execution transport is already proven PASS from the V69 execution probe. There is no current transport blocker and no reason to rerun a forced broker probe absent contradictory evidence.

### Harness / observability

The V72 collector telemetry-root mismatch was resolved. The corrected collector rejected stale/mixed evidence, reset the exact source root and produced valid fresh V72 evidence. The prior ZIP attachment-mount issue also has an established plain-text workaround. Neither is an active strategy blocker.

## Runtime state

No new MT5 tester or live-forward action is currently required from the operator.

`NEXT_MT5_TESTER_ACTION=PAUSED`

`SHORT_ENABLED=0`

`REAL_MONEY_AUTHORIZED=0`

Frozen V69 DEMO transport status remains PASS; no current runtime/execution fault is open.

## Current candidate / blocker / next gate

There is no newly promoted EURUSD candidate. Frozen V69 remains the preserved XAU LONG baseline/family; V72 EURUSD is rejected for promotion.

If FX research continues, the clean next research candidate is AUDUSD from the V71 no-retune screen (`7 trades / 3W / 4L / +$1.29 / PF 1.305687 / DD $2.10`). It is not promoted evidence because the sample is only seven trades.

Current blocker: no clean FX candidate has yet passed an untouched preregistered robustness gate. Specifically, EURUSD failed on drawdown; this is an economic/risk-path blocker, not broker/harness failure.

Next gate: preregister an earlier untouched AUDUSD temporal validation using the exact V71/V69 LONG source with zero symbol-specific retuning before seeing the result. Do not pool FX pairs, do not enable SHORT, and do not authorize REAL money.

## Changes made this turn

Only this canonical `TURN_SYNC.md` restoration record was changed. No strategy code, runtime contract, evidence artifact, broker setting, SHORT state or REAL authorization was modified.
