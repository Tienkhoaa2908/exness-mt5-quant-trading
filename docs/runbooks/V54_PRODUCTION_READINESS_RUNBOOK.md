# V54 Production-Readiness Runbook

## Purpose

V54 hardens the frozen `v52_b4_or_b3_trend_bos` candidate for unattended MT5
operation while preserving the V50/V49 execution stack and ADR-055 immutable evidence
semantics.

This runbook is operational, not alpha research.

## Fixed identity

- repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- branch: `agent/v54-production-readiness-hardening`
- symbol: `XAUUSDm`
- timeframe: `M15`
- magic: `540054`
- maximum owned positions: 1
- candidate: `v52_b4_or_b3_trend_bos`
- production activation: `DISABLED_DEMO_SAFE`
- real-money authorization in this build: `0`

## Preflight

The starter and runner fail closed unless:

- branch is exactly V54;
- working tree is clean;
- Python static test passes;
- secret scan passes;
- the canonical V48 parent hash matches;
- V54 source builds deterministically from V53;
- MetaEditor produces `0 errors, 0 warnings` and a non-empty EX5;
- MT5 is not already open during controlled startup;
- runtime account is DEMO;
- AutoTrading/MQL trading are enabled for the DEMO adapter;
- DLL imports are disabled;
- chart is `XAUUSDm M15`;
- no foreign same-symbol position exists;
- there is at most one position owned by magic `540054`.

Do not bypass a failed preflight.

## Order lifecycle

`selected virtual intent -> risk-cap sizing -> health gate -> owned broker request ->
retcode/result log -> OnTradeTransaction reconciliation -> owned position state`

No second alpha route exists in V54.

New entry is blocked on:

- disconnect;
- stale broker tick;
- stale strategy state after startup/restart;
- excessive spread;
- ambiguous same-symbol ownership;
- invalid stop geometry;
- minimum lot exceeding the configured risk budget;
- permanent halt/force-flatten state.

## Risk protection

Defaults:

- risk cap: 0.50% equity, never above inherited virtual volume;
- hard allowed input ceiling: 1.00%;
- daily/session loss stop: 2.00%;
- peak-equity drawdown stop: 6.00%;
- spread guard: 150 points;
- stale tick: 15 s;
- stale strategy state: 30 s;
- consecutive reject halt: 3.

Daily and peak equity are persisted in terminal Global Variables by server day so a
restart cannot reset that day's protection.

On a hard risk breach:

1. `halted=1`;
2. `accept_new=0`;
3. `force_flatten=1`;
4. owned position is closed by ticket when connectivity allows;
5. no new strategy entry is allowed in that runtime.

## Restart/recovery

The runner seeds V54 from the newest available prior strategy state, but V54 will not
open from that seeded state until a fresh strategy tick has been processed.

On restart:

1. inspect actual broker positions for symbol + magic;
2. fail closed if ownership is ambiguous or count exceeds one;
3. require SL and TP on an existing owned position;
4. refresh persistent daily/peak-equity protection;
5. wait for a fresh strategy tick;
6. reconcile virtual intent against actual owned position;
7. resume only if all guards are healthy.

Do not delete terminal Global Variables to clear a loss halt during the same server
day. That would defeat the risk control.

## Disconnect handling

A disconnect blocks new entries. The EA does not invent a close or duplicate request
while the terminal is offline. Existing broker SL/TP remains server-side protection.
After reconnect, reconciliation runs before any new order is eligible.

## Broker rejection handling

Every request records call result, broker retcode, description, order ID and deal ID.
Repeated rejects increment a consecutive counter. At the configured threshold V54
halts new entries. Successful broker requests clear the streak.

## Monitoring and phone notification

Primary machine-readable files are under MT5 Common Files:

`mt5_quant/v54/V54_PRODUCTION_READINESS_STATUS.txt`  
`mt5_quant/v54/V54_PRODUCTION_READINESS_EVENTS.csv`  
`mt5_quant/v54/V54_PRODUCTION_READINESS_TRANSACTIONS.csv`

Status includes ownership/pending state plus connection, risk and halt fields.

MetaQuotes push notifications are inherited for lifecycle events. Configure the
MetaQuotes ID in the terminal itself; never commit it to Git.

## Evidence packaging

The runner automatically creates a startup evidence bundle under:

`runtime/v54_production_readiness/OUTPUT_V54/`

The packager may also be invoked for later snapshots. It copies runtime evidence into
an immutable staging directory before hashing and zipping. A bundle is accepted only
when ZIP CRC and every manifest entry verify.

## Rollback

Rollback is fail closed:

1. stop accepting new entries by stopping V54 only after checking status;
2. if `owned_positions=1`, do not kill the terminal as a substitute for closing the
   position; leave MT5 connected so the owned close/SL/TP path remains active;
3. require `owned_positions=0`, `open_pending=0`, `close_pending=0`;
4. package a final V54 evidence snapshot;
5. only then stop MT5 or check out the prior branch.

Never run V53 and V54 simultaneously on the same terminal/symbol.

## Evidence gap retained

`V53_NATURAL_MAPPING=NOT_OBSERVED`

Normal V54 DEMO operation may eventually observe a natural selected-candidate broker
mapping. If that happens it is new evidence; until then the gap remains explicit. Do
not force a signal and do not rerun V50 probes.
