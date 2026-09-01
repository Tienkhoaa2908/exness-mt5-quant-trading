# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-01 (+07)

## Authority

Repository:

`Tienkhoaa2908/exness-mt5-quant-trading`

Authoritative active branch:

`agent/v69-one-shot-prospective-demo`

Do not recover from stale `main` or the old V54/V55 production-readiness branch.
Always fetch the current remote HEAD of this branch rather than relying on a SHA copied
from an older conversation.

Mandatory read order:

1. `docs/handover/OPERATING_PROTOCOL.md`
2. `docs/handover/CURRENT_STATE.md`
3. `docs/handover/KNOWN_FAILURES.md`
4. `docs/handover/TURN_SYNC.md`
5. `docs/handover/RECOVERY_PROMPT.md`
6. current branch commits + exact-HEAD CI

## Current objective

Finish a short live-market **DEMO smoke validation** of frozen V69 LONG on Exness MT5,
prove runtime/broker order-path readiness, collect a small amount of natural forward
trade evidence, then review before any later real-money deployment decision.

This is not another long backtest campaign. Historical research has already done most of
the economic evaluation.

Current safety boundary:

- symbol/timeframe: `XAUUSDm M15`;
- direction: LONG only;
- fixed lot: `0.01`;
- DEMO only;
- SHORT rejected/disabled;
- REAL authorization false;
- no automatic REAL promotion.

## Frozen V69 research identity

Accepted research branch:

`agent/v69-confirm-separation-retest-research`

Frozen V69 research HEAD:

`0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted V69 evidence ZIP SHA256:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256:

`0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Frozen V69 LONG contract:

- XAUUSDm M15;
- fixed lot `0.01`;
- structural planned cash risk `$0.85-$1.10`;
- emergency cash loss guard about `$1.20`;
- primary target `+$3.50`;
- risk/spread ratio `>=4`;
- post-zone closed-M1 reclaim cannot order immediately;
- post-confirm favorable separation must reach at least `$1.30` from the fixed stop;
- the separation tick itself cannot order;
- a later retest into the unchanged cash-risk zone is required;
- reclaim confirmation age at least 30 seconds;
- fixed structural stop, no widening/clamp;
- entry ordering: `POST_ZONE_REVERSAL_CONFIRM -> return -> POST_CONFIRM_SEPARATION -> POST_CONFIRM_RETEST_READY -> POST_CONFIRM_ENTRY_READY -> V64OrderPreflight`.

The `$1.30` and 30-second values are development choices, not proven global optima.

## Accepted V68 -> V69 development evidence

V68 LONG replay:

- 28 trades;
- 10 wins / 18 losses;
- net `+$2.87`;
- PF about `1.146`;
- gross profit about `$22.57`;
- gross loss `$19.70`;
- max realized DD `$6.04`;
- 11/18 losers closed within 60 seconds.

V69 LONG development replay:

- 24 trades;
- 10 wins / 14 losses;
- net `+$7.14`;
- gross profit `$22.58`;
- gross loss `$15.44`;
- PF `1.462`;
- max realized DD `$3.34`;
- 10/14 losers closed within 60 seconds (71.4%).

V69 retained all 10 V68 winners while removing four losers. This supports the
separation/retest architecture as a selectivity improvement, but the surviving loser set
is still dominated by very fast failures.

V69 monthly LONG development replay:

- Sep 2025 `-$1.84`;
- Oct `+$9.15`;
- Nov `+$1.24`;
- Dec `-$2.28`;
- Jan 2026 `+$0.87`;
- Feb-May `$0`;
- total `+$7.14`;
- excluding October: `-$2.01`.

Therefore regime concentration remains a major concern.

Methodology boundary: V69 was designed after V68 was inspected. The Sep 2025-May 2026
V69 replay is development evidence, not an independent holdout. Do not retune on the
same period and call it independent validation.

## Current failure-mode priority

Verified priority from existing evidence:

1. entry-state / regime quality;
2. same-setup re-entry suppression if cluster diagnostics confirm it;
3. exit/harvest quality if MFE/capture diagnostics show material positive-MFE
   round-trips.

Do not lower the profit-ratchet threshold blindly. Current lineage only protects after
about +$2, which creates a theoretical sub-$2 harvest gap, but many fast losers may have
near-zero MFE and cannot be rescued by earlier exits.

## Current V69 forward implementation

Active branch contains a one-shot Windows/MT5 flow that:

- verifies exact Git state;
- probes a working Python runtime instead of trusting `py.exe`;
- runs static/regression/secret gates;
- deterministically builds the V69 DEMO dashboard source;
- MetaEditor-compiles and verifies exact MQ5/EX5 identity;
- archives previous forward Common Files state;
- generates an MT5 startup config;
- launches the exact EA automatically on `XAUUSDm M15`;
- waits for live tick heartbeat;
- performs broker/order-path dry-run preflight;
- starts a silent `pythonw.exe` supervisor with no console-window flashing;
- updates the chart dashboard and rolling/final evidence packages.

Canonical launcher:

`bash runtime/v69_one_shot_prospective_demo/START_V69_ONE_SHOT_PROSPECTIVE_DEMO_GIT_BASH.sh`

The chart EA remains named:

`V69FrozenForwardSmokeDashboardLong`

## Forward smoke review horizon

This live DEMO step is intentionally short:

- runtime/broker health can pass immediately after stable startup checks;
- quick economic review target: 2 naturally closed strategy trades;
- hard review cap: 48 hours even if two trades do not occur;
- output is then packaged as `v69_forward_smoke_final.zip`.

Two trades are not statistical proof of profitability. They are a small operational /
forward sanity sample on top of the historical research.

## Latest live DEMO evidence — 2026-09-01

The earlier dashboard successfully proved:

- Exness DEMO account loaded;
- `XAUUSDm M15` chart correct;
- EA initialization occurred;
- live ticks were arriving;
- telemetry/dashboard updates were functioning;
- REAL remained disabled.

The broker-ready overlay then exposed a previously hidden order-path issue before a
strategy signal occurred.

Observed broker fields:

- fixed lot `0.01`;
- broker min lot `0.0100`;
- broker volume step `0.0100`;
- broker max lot `200.0000`;
- symbol trade mode `4` (full trading);
- filling flags `3` (FOK + IOC available);
- first `OrderCheck()` returned false with local error `4756`.

Conclusion: the failure is **not lot size**. `0.01` is valid under the broker's current
volume contract.

The first broker-ready harness had a logic defect: EA broker refresh interval was 30
seconds while the runner permanently failed after 12 seconds on the same detail. It
could therefore classify one startup `OrderCheck` result as a permanent block without a
second independent check. It also discarded `MqlTradeCheckResult.retcode/comment` when
the function returned false.

## Latest fix now on the active branch

Broker/system-health overlay has been hardened to:

- refresh every 5 seconds;
- publish `broker_check_seq`;
- check `TERMINAL_CONNECTED`;
- check `ACCOUNT_TRADE_ALLOWED`;
- check `ACCOUNT_TRADE_EXPERT`;
- check terminal + MQL trade permissions;
- check symbol synchronization;
- check symbol trade mode and min/max/step volume;
- capture execution mode via `SYMBOL_TRADE_EXEMODE`;
- build dry-run request according to execution mode;
- capture both local `_LastError` and server `retcode/comment`;
- initially classify bare 4756 with no server retcode as transient;
- require two independent consecutive READY checks before startup PASS;
- require repeated independent confirmation before fatal classification;
- allow transient broker transport up to 90 seconds to stabilize;
- display `SYSTEM HEALTH: STARTING / READY / BLOCKED` directly on the chart;
- show whether execution is merely preflight-ready or has actually been observed via a
  natural open/closed V69 trade.

This changes observability/execution preflight only. Frozen V69 signal state ordering and
actual strategy order-send token count remain protected by regression tests.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_FORWARD_DIRECTION=LONG_ONLY`

`V69_FORWARD_DEMO_ONLY=1`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`V69_FORWARD_SHORT_ENABLED=0`

`V69_RUNTIME_HEARTBEAT=OBSERVED`

`V69_LOT_0_01_BROKER_SPEC=VALID`

`V69_BROKER_HEALTH_FIX=IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_WINDOWS_RERUN`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. require current exact remote HEAD CI to be green after the latest broker-health and
   documentation changes;
2. close MT5/MetaEditor once and rerun only the canonical V69 one-shot;
3. require Windows MetaEditor `0 errors, 0 warnings`;
4. require two consecutive independent broker checks to produce `SYSTEM HEALTH: READY`;
5. if not READY, use the newly captured account flags + `_LastError` + server
   `retcode/comment` to diagnose the exact blocker rather than guessing;
6. after READY, leave the system running for the short smoke target (2 closed strategy
   trades or 48-hour cap);
7. review the final ZIP before any later real-money implementation decision.

Do not reopen a long historical backtest campaign merely because the forward harness had
a broker/observability defect.
