# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 00:xx (+07)

## User request

User no longer accepts passive waiting after approximately one day with zero natural V69 trades. User believes visible market opportunities existed and wants a different, immediate way to determine whether real-time deployment/order execution is defective. User also requested research into session-dependent volatility, especially XAU around New York/London-New York overlap and MarketMilk-style per-hour statistics, with the project moving immediately **toward** REAL deployment.

## Mandatory pre-work state read

Resolved remote branch and read:

- active remote HEAD;
- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- previous `docs/handover/TURN_SYNC.md`;
- exact-HEAD CI;
- frozen forward builder/order lineage;
- broker-ready dashboard/runner;
- current telemetry/event naming.

## Key reasoning

Healthy `SYSTEM HEALTH: READY`, live ticks and dry-run `OrderCheck` prove runtime attachment and request readiness, but they do not prove the integrated V69 natural `g_trade.Buy()` path.

Zero trades over a day is also not enough to call the order path broken, because frozen V69 may simply never have reached `POST_CONFIRM_ENTRY_READY`.

Waiting longer is therefore an inefficient diagnostic. The correct immediate decomposition is:

1. inspect the already-collected live telemetry as a state funnel;
2. separately prove actual MT5<->broker open/close capability with an isolated DEMO-only execution probe;
3. combine those results to locate the fault.

## Code added this turn

### Live signal funnel

`scripts/analyze_v69_live_signal_path.py`

Counts:

- `POST_ZONE_REVERSAL_CONFIRM`;
- `POST_CONFIRM_SEPARATION`;
- `POST_CONFIRM_RETEST_READY`;
- `POST_CONFIRM_ENTRY_READY`;
- closed deals.

It classifies whether no trade is upstream confirmation/separation/retest gating, entry-ready without execution, or already executed.

### Actual DEMO execution probe

`scripts/build_v69_demo_execution_probe_source.py`

Generates `V69DemoExecutionProbe` with:

- DEMO-only account guard;
- exact `XAUUSDm`;
- fixed lot `0.01`;
- unique magic `699901`;
- `OrderCheck` before send;
- one actual DEMO BUY;
- immediate close of only the probe-owned position;
- open/close retcode, comment, price and free-margin telemetry;
- graceful terminal shutdown via `TerminalClose()`;
- no REAL authorization and no SHORT probe.

### One-shot diagnostic runner

`runtime/v69_real_readiness_probe/RUN_V69_REAL_READINESS_PROBE.py`

Sequence:

- requires MT5/MetaEditor closed once;
- snapshots existing frozen V69 telemetry before changing runtime;
- generates the live signal funnel JSON;
- deterministically builds/installs/compiles the probe;
- runs actual DEMO open+close probe;
- writes `V69_REAL_READINESS_PROBE_RESULT.json`;
- waits for graceful probe-terminal close;
- automatically relaunches frozen V69 using the existing broker-ready runner.

Launcher:

`runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`

Tests:

`tests/test_v69_real_readiness_probe_static.py`

CI workflow `v69-forward-quality` now compiles/tests the new analyzer/builder/runner/launcher and checks DEMO-only/no-force-kill/no-REAL safety contracts.

## Research added this turn

`docs/research/SESSION_VOLATILITY_RESEARCH.md`

External research supports using session/time-of-day as a research variable:

- MarketMilk exposes XAU/USD volatility per hour and identifies most/least volatile hours;
- London-New York overlap is generally a high-liquidity/high-activity FX window;
- New York morning is typically more active than later New York hours;
- LBMA describes London bullion trading as a central 24-hour OTC market and specifies normal London market-making hours;
- gold therefore should use a liquidity/volatility-regime model rather than a simple market-open flag.

The successor research will reproduce the useful statistics from our own MT5 data instead of depending on MarketMilk at runtime. It will use DST-aware session labels, rolling past-only volatility percentiles, spread/range efficiency, directional persistence, breakout follow-through, MFE/MAE and expectancy by symbol/session.

This research does not change frozen V69.

## CI evidence

Code checkpoint:

`89370fcd37493f478d3fb50b218dabeea9544320`

Passed:

- `v69-forward-quality` run `33662678974`;
- `v69-quality`;
- `v68-quality`;
- full `quality` run `33662678989`.

The final post-documentation branch HEAD must be rechecked before operator execution because project protocol requires exact-HEAD validation.

## Safety status

Unchanged:

- current execution probe is DEMO only;
- XAUUSDm;
- lot 0.01;
- unique diagnostic magic;
- no SHORT probe;
- frozen V69 strategy thresholds unchanged;
- REAL authorization remains false.

## Current unresolved evidence

The new probe has **not yet been compiled/run on the operator's Windows MetaEditor/MT5**. GitHub Linux CI validates Python/static contracts only; the Windows run will be the first actual MQL5 compile and broker fill for this new probe.

The existing day's live telemetry has also not yet been read by the new signal-funnel analyzer because it resides on the operator's Windows FILE_COMMON directory.

## Next operator action

After exact final HEAD CI is green:

1. close MT5 and MetaEditor once;
2. fetch/fast-forward the active branch to the exact final HEAD;
3. run only `runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`;
4. return the output beginning with `V69_PRE_PROBE_SIGNAL_PATH_CLASSIFICATION=` through `V69_REAL_READINESS_EXECUTION_LAYER=` or the first `FATAL`;
5. do not wait another day for a natural signal before diagnosing execution.

If actual probe passes, use the signal funnel to decide whether V69 gating or V69 order-path integration is the remaining issue. REAL deployment work can then proceed as a separate fail-closed package; do not auto-authorize REAL from probe PASS alone.
