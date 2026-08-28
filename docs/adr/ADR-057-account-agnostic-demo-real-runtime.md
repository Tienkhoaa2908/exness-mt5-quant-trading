# ADR-057 — Account-agnostic DEMO/REAL production runtime

Date: 2026-08-28  
Status: Accepted

## Context

V52R selected `v52_b4_or_b3_trend_bos` on clean real-tick evidence. V50 proved the
native execution plumbing and V54 added production risk/recovery/observability guards.
The V54 generated EA still inherited a phase-specific DEMO-only account guard from
V49/V53.

The operational target is to run the same strategy/execution implementation on the
current trial/DEMO account and, later, on the user's REAL account without maintaining a
second strategy fork.

## Decision

V55 is a thin account-mode envelope on top of V54. It does not change candidate
selection, strategy thresholds, direction logic or the proven reconciliation model.

The same generated EA binary supports `ACCOUNT_TRADE_MODE_DEMO` and
`ACCOUNT_TRADE_MODE_REAL`.

### DEMO semantics

DEMO is active by default. No additional arming input is required.

### REAL semantics

A REAL account can load the same EA without automatically opening new risk. The default
REAL state is `REAL_OBSERVE_ONLY`.

Opening new REAL risk requires both:

- `InpV55AllowRealAccount=true`;
- `InpV55RealArmCode=V55_REAL_ARMED`.

The arming string is not a credential. It is a deliberate startup interlock. Broker
login/password/server credentials remain terminal-local and are not stored in Git or in
the V55 runner.

### Account identity stability

V55 records the account login and account mode at initialization. If the account is
changed while the EA remains loaded, V55 halts and requires a clean restart before new
activity. This prevents an already-running DEMO session from silently becoming a REAL
session after an account switch.

### First-REAL-entry flat epoch

A newly armed REAL startup must observe `virtual FLAT + owned broker FLAT` at least once
before it may create its first new broker position. Until that epoch is observed, a
virtual position inherited from prior DEMO/trial state is logged as
`real_activation_waiting_for_flat` and cannot be materialized late as new real-money
exposure.

This latch applies only when there is no owned broker position. If V55 is restarted while
an already-owned REAL position exists, normal ownership/reconciliation and exit handling
continue immediately. After that owned position and the virtual book both become flat,
the REAL entry epoch becomes ready for subsequent fresh signals.

### Account-scoped protection state

Daily-loss and peak-equity risk globals include the current account login in their key,
so DEMO and REAL account risk state cannot contaminate one another.

The daily-loss baseline is keyed by broker/server date and therefore resets on a new
trading day. The max-drawdown peak is deliberately keyed with day component `0`, making
it one persistent account+magic+symbol high-water mark across days and terminal
restarts. A new trading day therefore cannot erase an accumulated production drawdown.

### Broker-aware constraints

The code derives broker/account constraints at runtime instead of assuming DEMO values:

- volume min/max/step;
- stop-distance level;
- freeze level telemetry;
- account leverage telemetry;
- stop-loss risk via `OrderCalcProfit`;
- margin requirement via `OrderCalcMargin`;
- free margin via `ACCOUNT_MARGIN_FREE`;
- symbol filling mode through the inherited `SetTypeFillingBySymbol` path.

The EA never rounds a volume upward above the risk-constrained cap. If broker minimum
volume, stop geometry or margin constraints make an entry invalid, the entry fails
closed.

## Runner contract

Canonical launcher:

`runtime/v55_account_agnostic/START_V55_ACCOUNT_AGNOSTIC_GIT_BASH.sh`

The runner defaults to `--execution-mode demo`. `--execution-mode real` writes an
explicit V55 preset containing the REAL arm inputs and then verifies that the logged MT5
account reports `REAL` plus `production_activation=REAL_ARMED` before declaring READY.

The runner emits MetaTrader-native `.set` scalar syntax (`value||start||step||stop||N`)
for numeric/bool inputs and plain assignment for the string arm input. The runner never
supplies account credentials; it operates on the account already logged into the
terminal.

## Inherited safety contract

V55 retains:

- XAUUSDm M15;
- one owned magic (`550055`);
- maximum one owned strategy position;
- no Martingale;
- no grid;
- no doubling after loss;
- stop-risk cap;
- daily loss limit;
- persistent max-drawdown high-water protection;
- spread/stale/disconnect guards;
- duplicate and ownership protection;
- SL/TP validation;
- broker retcode/deal audit;
- notifications;
- immutable evidence packaging.

## Evidence boundary

This ADR defines implementation semantics only. It does not claim a Windows MetaEditor
compile PASS, REAL-account runtime PASS or REAL-money performance result. Those labels
require actual runtime evidence.
