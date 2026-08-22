# V49 One-Shot Exness DEMO Production Rehearsal

Date: 2026-08-22
Branch: `agent/v49-one-shot-demo-rehearsal`

## Objective

Run one integrated, finite broker-DEMO campaign that proves the frozen breadth4 system can operate as an automated trading application: detect a signal, open a native Exness DEMO position, maintain SL/TP and ownership, close when the virtual strategy exits, reconcile broker transactions, notify the phone, survive ordinary disconnect/reconnect behavior, and produce one final evidence bundle.

This plan intentionally reuses prior historical/strategy evidence rather than repeating separate gates.

## Frozen strategy

Primary candidate: `v46_hl10_thr0p05_breadth4`.

Do not retune:
- HL10 EWMA;
- selected-expert threshold 0.05;
- breadth-health threshold 0.05;
- breadth requirement 4/5;
- primary entry/exit logic;
- stop-risk geometry.

V49 adds an execution adapter, not a second signal owner.

## Execution architecture

Primary virtual book remains the source of strategy intent.

At the end of each strategy tick:

1. Read the primary virtual book (`ci=23`, `bi=3`).
2. Inspect broker positions owned by the dedicated V49 magic number on `XAUUSDm`.
3. Reconcile:
   - virtual FLAT + broker FLAT -> no action;
   - virtual OPEN + broker FLAT -> submit matching DEMO market entry;
   - virtual OPEN + matching broker OPEN -> maintain/reconcile;
   - virtual FLAT + owned broker OPEN -> close owned broker position;
   - direction mismatch / duplicate owned positions -> HALT new entries and report.
4. Record every request and every `OnTradeTransaction` event.

The adapter must never manage manual/foreign positions.

## Account hard guard

V49 initializes only when:
- `ACCOUNT_TRADE_MODE_DEMO`;
- symbol is `XAUUSDm`;
- period is M15;
- terminal/MQL automated trading permission is enabled because DEMO broker orders are required;
- DLL imports remain disabled.

REAL/non-DEMO account -> `INIT_FAILED` before any broker request.

## Volume

Virtual volume remains the reference intent. Broker volume is normalized to symbol min/max/step and both values are logged. If normalization materially changes size, the event is marked in the parity ledger rather than hidden.

No loss-based size increase is allowed.

## Broker ownership

Use a dedicated magic number and comment prefix. Only owned positions/orders are eligible for V49 actions.

Any duplicate owned position is a critical reconciliation failure. Foreign/manual positions are logged and ignored, except a foreign XAUUSDm position may cause startup refusal if it makes account state ambiguous for the rehearsal.

## Trade result handling

Do not treat a successful API call as proof of execution. For every open/close request record:
- request timestamp;
- virtual decision price/direction/volume/SL/TP;
- normalized broker volume;
- API boolean return;
- server result/retcode;
- order/deal ticket when available.

`OnTradeTransaction` is the authoritative asynchronous event stream for order/deal/position changes.

## Phone notifications

Use `SendNotification()` when terminal push notifications are configured. Send compact messages for:
- V49 START;
- broker DEMO OPEN confirmed;
- broker DEMO CLOSE confirmed;
- reconciliation HALT;
- FINAL verdict.

Do not store MetaQuotes ID, email passwords or other secrets in repository files. The MetaQuotes ID remains terminal configuration.

Broker/server trade notifications may also be enabled in MT5 settings when the broker supports them.

## Campaign duration / simplified final rule

The integrated campaign runs until either:
- >=3 distinct market-active XAUUSD dates AND >=3 completed native broker-DEMO round trips; or
- 14 calendar days.

After the minimum sample is reached, the EA stops creating new broker entries once flat and writes FINAL.

`LIVE_CANDIDATE_READY` requires:
- minimum sample reached;
- DEMO account throughout;
- zero duplicate owned entries;
- zero unresolved direction/reconciliation mismatch;
- no real-account guard violation;
- reject ratio <=20%;
- frozen parent identity intact.

Otherwise emit a specific HOLD/FAIL reason. At 14 days without enough trades emit `INSUFFICIENT_EXECUTION_SAMPLE`.

This is deliberately an engineering readiness test. Historical alpha robustness is inherited from previous accepted evidence.

## Evidence files

Minimum Common Files evidence:
- `V49_DEMO_REHEARSAL_STATUS.txt`;
- `V49_DEMO_REHEARSAL_FINAL.txt`;
- `V49_DEMO_REHEARSAL_EVENTS.csv`;
- `V49_DEMO_REHEARSAL_TRANSACTIONS.csv`;
- current adaptive state;
- run manifest / latest metadata.

The detached supervisor packages these plus relevant run outputs into one ZIP with SHA256 manifest after FINAL/hard stop.

## One user action

After V49 implementation is accepted, the user performs only one canonical Git Bash start after intentionally ending the V48 observer while flat. The V49 starter handles build, compile, startup config, launch, status verification and detached supervision.

No repeated Strategy Tester campaign is part of V49.
