# V49 One-Shot Exness DEMO Production Rehearsal

Date: 2026-08-22
Branch: `agent/v49-one-shot-demo-rehearsal`

## Project target

This project explicitly targets production/live trading with real capital on Exness.

Authoritative semantics from ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- V49 is a phase-specific broker-DEMO rehearsal, not a project-wide restriction against live research;
- current `LIVE_READINESS=PENDING_V49_FINAL` until broker-DEMO execution evidence is complete.

## Objective

Run one integrated, finite broker-DEMO campaign that proves the frozen breadth4 system can operate as an automated trading application: detect a signal, open a native Exness DEMO position, maintain SL/TP and ownership, close when the virtual strategy exits, reconcile broker transactions, notify the phone, survive ordinary disconnect/reconnect behavior, and produce one final evidence bundle.

This plan intentionally reuses prior historical/strategy evidence rather than repeating separate gates. A successful final is intended to transition directly into the dedicated production/live deployment engineering milestone.

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

## V49 account-mode contract

V49 v1 is deliberately compiled and launched as the broker-DEMO rehearsal version. It initializes only under the account/symbol/timeframe/permission checks implemented for this campaign.

The DEMO-only guard belongs to V49 v1. It does not prohibit research or engineering of the later real-capital production deployment.

## Volume

Virtual volume remains the reference intent. Broker volume is normalized to symbol min/max/step and both values are logged. If normalization materially changes size, the event is marked in the parity ledger rather than hidden.

No loss-based size increase is allowed.

## Broker ownership

Use a dedicated magic number and comment prefix. Only owned positions/orders are eligible for V49 actions.

Any duplicate owned position is a critical reconciliation failure. Foreign/manual positions are logged and ignored, except an ambiguous foreign XAUUSDm state may cause startup refusal for the rehearsal.

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

## Campaign duration / simplified final rule

The integrated campaign runs until either:
- >=3 distinct market-active XAUUSD dates AND >=3 completed native broker-DEMO round trips; or
- 14 calendar days.

After the minimum sample is reached, the EA stops creating new broker entries once flat and writes FINAL.

`LIVE_CANDIDATE_READY` requires:
- minimum sample reached;
- zero account-mode guard violation during V49;
- zero duplicate owned entries;
- zero unresolved direction/reconciliation mismatch;
- reject ratio <=20%;
- frozen parent identity intact;
- no catastrophic execution-loop failure.

Otherwise emit a specific HOLD/FAIL reason. At 14 days without enough trades emit `INSUFFICIENT_EXECUTION_SAMPLE`.

Historical alpha robustness is inherited from previous accepted evidence.

## Accepted startup status

The Windows V49 startup on 2026-08-22 already proved:
- static tests 9/9 PASS;
- secret scan PASS;
- deterministic parent chain PASS;
- V49 generated source SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- MetaEditor `0 errors, 0 warnings`;
- EX5 SHA256 `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- DEMO READY PASS;
- run id `v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`;
- detached supervisor started.

The campaign began while XAUUSD was closed, so the initial counters `MARKET_DAYS=0` and `ROUND_TRIPS=0` are expected.

## Evidence files

Minimum Common Files evidence:
- `V49_DEMO_REHEARSAL_STATUS.txt`;
- `V49_DEMO_REHEARSAL_FINAL.txt`;
- `V49_DEMO_REHEARSAL_EVENTS.csv`;
- `V49_DEMO_REHEARSAL_TRANSACTIONS.csv`;
- current adaptive state;
- run manifest / latest metadata.

The detached supervisor packages these plus relevant run outputs into one ZIP with SHA256 manifest after FINAL/hard stop.

## Production/live follow-on

If V49 finishes `LIVE_CANDIDATE_READY`, the next milestone is production/live deployment engineering. Valid research topics include:
- live-account architecture;
- capital sizing and capital-at-risk policy;
- production risk/kill-switch controls;
- VPS/always-on operation;
- monitoring, reconciliation and recovery;
- staged rollout/checklist based on the V49 evidence bundle.

No repeated Strategy Tester campaign is required solely because the project is moving from V49 readiness into production/live engineering.
