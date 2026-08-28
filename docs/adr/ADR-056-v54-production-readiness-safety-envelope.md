# ADR-056 — V54 production-readiness safety envelope

Date: 2026-08-28  
Status: Accepted for implementation

## Context

V50 proved the generic native broker-DEMO execution pipeline. V52R selected
`v52_b4_or_b3_trend_bos` on clean real-tick evidence. V53 then attempted natural
selected-candidate broker-DEMO mapping but reached its timebox without a qualifying
signal, so the accepted classification is:

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`  
`V53_NATURAL_MAPPING=NOT_OBSERVED`

The project must not reopen alpha tuning merely because the natural mapping event was
rare. The next engineering problem is production-readiness: capital protection,
deterministic ownership/reconciliation, failure handling, observability, restart
behavior and evidence capture.

The V49/V53 adapter already provides a proven base for owned-magic filtering,
open/close pending confirmation, broker retcode logging, `OnTradeTransaction`,
duplicate-direction checks and optional MetaQuotes push notifications. Rewriting that
adapter would add unnecessary execution risk.

## Decision

Create V54 by wrapping the exact V53 selected-candidate build and inherited V49 broker
adapter with a narrow production-readiness safety envelope.

Frozen identity:

`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`

Fallback/reference remains breadth4. V54 does not sweep breadth/source thresholds,
rerun V50 probes or open a new tournament.

### Runtime topology

- symbol: `XAUUSDm`;
- timeframe: `M15`;
- owned magic: `540054`;
- maximum owned strategy positions: one;
- no Martingale;
- no grid;
- no doubling after loss;
- DLL imports disabled;
- foreign same-symbol positions are fail-closed because ownership is ambiguous;
- strategy intent remains the selected V52R router;
- broker execution remains synchronized from the inherited virtual intent rather than
  creating a second alpha path.

### Capital protection

V54 adds a volume risk cap based on `OrderCalcProfit` from intended entry to the
strategy stop. The broker volume may be reduced below the inherited virtual volume but
must never be increased above it.

Default hardening inputs:

- maximum stop-risk cap: 0.50% of current equity;
- runtime input ceiling: 1.00% of equity;
- daily/session equity-loss stop: 2.00%;
- peak-equity drawdown stop: 6.00%;
- maximum spread: 150 points;
- maximum broker tick age: 15 seconds;
- maximum strategy-state age: 30 seconds;
- maximum consecutive broker rejects: 3.

The 0.50% value is a production protection default, not a new alpha parameter. V54
fails initialization if the configured risk cap exceeds the existing project ceiling
of 1.00%.

If the minimum broker lot would exceed the risk budget, V54 refuses the entry instead
of rounding up to `SYMBOL_VOLUME_MIN`.

### Hard-loss behavior

Daily-loss or drawdown breach sets a persistent halt and `force_flatten` state. New
entries are disabled and any owned position is closed through the same owned-ticket
adapter when connectivity permits.

Daily start equity and peak equity use terminal Global Variables keyed by V54 magic,
symbol and server day, so a terminal restart does not silently reset the protection
within that day.

### Connectivity and stale-state behavior

New entries require:

- terminal connected;
- a recently processed strategy tick;
- a fresh broker tick;
- spread inside the configured guard;
- unambiguous position ownership.

A disconnect or transient stale/spread condition blocks new entry without inventing a
new strategy decision. An existing server-side SL/TP remains the first protection
during disconnect. On reconnect the runtime reconciles broker state before resuming.

V54 also refuses to trust seeded state for a new order until an actual fresh strategy
tick has been processed after startup.

### Position protection and reconciliation

The inherited adapter continues to own only its magic/symbol positions and to use
open/close pending confirmation. V54 additionally:

- halts on more than one owned position;
- halts if an owned position lacks both SL and TP;
- halts on foreign same-symbol ownership ambiguity;
- counts consecutive broker rejects and halts at the configured limit;
- retains full request/result retcode, order/deal and transaction logging.

### Observability

Status telemetry adds:

- connection state;
- entry-block reason;
- force-flatten state;
- consecutive rejects;
- day-start equity;
- peak equity;
- daily loss percentage;
- drawdown percentage;
- frozen candidate identity;
- explicit activation boundary.

MetaQuotes push notification remains the phone channel for START/OPEN/CLOSE/HALT and
other inherited lifecycle events. Notification delivery failure is logged but does not
alter strategy intent or trigger a duplicate order.

### Immutable evidence

V54 packages evidence by:

1. copying selected runtime/build/docs files to a temporary snapshot;
2. ceasing reads from live mutable runtime files;
3. creating `PROVENANCE.json` and `SHA256SUMS.txt` from the snapshot;
4. creating the ZIP only from the snapshot;
5. running ZIP CRC verification;
6. rereading every archived file and verifying it against the manifest;
7. writing a sidecar ZIP SHA-256.

This implements ADR-055 and prevents the V53 mutable-status packaging race.

### CI repair

Historical ADR/research documents are immutable evidence and can legitimately contain
superseded policy wording. The live-policy wording scanner therefore checks active
operator-facing documents rather than treating historical quotations as current
policy.

The old V29 corrupt-recovery migration exercise is also removed as an unconditional
global CI failure. The historical payload stays tracked as quarantined migration input
and V54 asserts that no active production-readiness source references it.

## Activation boundary

`PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE`

V54 deliberately retains the `ACCOUNT_TRADE_MODE_DEMO` runtime guard and
`real_money_authorized=0`. This branch proves and hardens the production architecture;
it does not manufacture evidence that a real-money cutover has been authorized or
executed.

This boundary does not change ADR-049:

`LIVE_RESEARCH_ALLOWED=1`  
`LIVE_DEPLOYMENT_TARGET=1`

It only separates technical readiness from actual financial execution.

## Evidence semantics

The following remain inherited facts and must not be relabeled:

`V50_EXECUTION_PIPELINE=PASS`  
`V52R_REAL_TICK_REPRO=PASS`  
`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`  
`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`  
`V53_NATURAL_MAPPING=NOT_OBSERVED`

A V54 static/CI/Windows compile result may establish production-readiness engineering
evidence, but it cannot retroactively convert V53 into `DEMO_CONFIRMATION_PASS`.
