# Windows MT5 / Exness — V49 One-Shot DEMO Production Rehearsal

Updated: 2026-08-22

Environment: Exness Technologies Ltd.; Exness DEMO account; observed server `Exness-MT5Trial6`; symbol `XAUUSDm`; timeframe M15.

## Project target

The project explicitly targets production/live trading with real capital on Exness.

Authoritative project-wide flags:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The current V49 runtime remains the broker-DEMO rehearsal build. Its DEMO-only account guard is phase-specific and must not be interpreted as a permanent prohibition on live-account research or later real-capital deployment engineering.

Current evidence label:
`LIVE_READINESS=PENDING_V49_FINAL`.

## Frozen strategy

Primary: `v46_hl10_thr0p05_breadth4`.
Frozen V48 parent SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not retune breadth/HL/threshold during V49. V49 adds an execution adapter around the frozen virtual intent.

## Accepted V49 startup

The one-shot V49 startup on 2026-08-22 already passed:
- static tests 9/9;
- secret scan;
- deterministic V46 -> V47 -> V48 parent chain;
- V49 source generation SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- MetaEditor `0 errors, 0 warnings`;
- EX5 SHA256 `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- state transition;
- startup config verification;
- `V49_DEMO_REHEARSAL_READY=1`;
- detached supervisor start.

Accepted run id:
`v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`.

Initial counters were `MARKET_DAYS=0` and `ROUND_TRIPS=0` because XAUUSD was closed at startup.

Do not run the V49 START command again while this accepted session is active.

## V49 branch / canonical command

Branch:
`agent/v49-one-shot-demo-rehearsal`

Canonical entrypoint used for startup:
`runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

The starter performs Python/static tests, secret scan, exact parent rebuild, V49 generation, MetaEditor compilation, state transition, startup config creation, MT5 launch, DEMO READY verification and detached supervisor launch.

After `V49_ONE_SHOT_STARTED=1`, Git Bash may be closed. Keep the PC, Internet and MT5 running.

Do not fetch/reset the active Windows checkout merely to obtain docs-only commits while the current V49 runtime is active.

## V49 native broker execution contract

Startup config enables MT5 automated trading for the V49 broker-DEMO rehearsal:
- `AllowLiveTrading=1`;
- `Enabled=1`;
- `AllowDllImport=0`.

The V49 MQL build independently checks the account/symbol/timeframe/permission contract before execution and owns only positions carrying its dedicated magic `490049`.

These account-mode checks describe V49 v1 only. ADR-049 explicitly allows follow-on research and engineering for the production/live real-capital deployment milestone after V49 final readiness evidence.

## Automatic entry / exit

Frozen primary virtual book remains strategy intent owner.

Reconciliation loop:
- virtual FLAT + owned broker FLAT -> no action;
- virtual OPEN + owned broker FLAT -> native DEMO Buy/Sell;
- virtual OPEN + matching owned broker OPEN -> maintain;
- virtual FLAT + owned broker OPEN -> close owned broker position;
- duplicate owned positions or direction mismatch -> HALT new entries and notify.

SL/TP from the frozen virtual intent is supplied on native entry when the broker/symbol accepts it.

A `CTrade` method returning `true` is not accepted as proof of fill. V49 records server `ResultRetcode()` and uses `OnTradeTransaction` deal events for confirmation/reconciliation.

## Phone notifications

V49 uses `SendNotification()` if push notifications are configured in MT5.

Messages:
- START;
- DEMO OPEN confirmed;
- DEMO CLOSE confirmed;
- HALT;
- FINAL.

MetaQuotes ID remains local terminal configuration and must not be committed to Git. Notification failure is logged but must not trigger another trade request.

## One-shot finite run

Minimum useful sample:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

A clean run may write `LIVE_CANDIDATE_READY`. Critical execution/reconciliation failure writes `HOLD`; insufficient activity at hard stop writes `INSUFFICIENT_EXECUTION_SAMPLE`.

Historical campaigns are not rerun as part of V49.

## Detached supervisor / final ZIP

Supervisor:
`runtime/v49_demo_rehearsal/SUPERVISE_V49_ONE_SHOT.py`

It waits for EA FINAL or timeout and produces one ZIP under:
`runtime/v49_demo_rehearsal/OUTPUT_V49/`

The ZIP includes V49 status/final/event/transaction evidence, transitioned state/run outputs when available, and `bundle_manifest_sha256.txt`. ZIP CRC is checked before it is declared complete.

## Production/live follow-on

If V49 final is `LIVE_CANDIDATE_READY`, proceed to production/live deployment engineering based on the final bundle. That milestone may cover:
- live-account deployment architecture;
- real-capital sizing and capital-at-risk policy;
- production risk/kill-switch controls;
- VPS/always-on operation;
- monitoring/reconciliation/recovery;
- staged rollout and operational checklist.

## Runtime limitation

V49 v1 is designed as one continuous rehearsal. PC sleep/shutdown or Windows reboot stops MT5 and therefore stops native execution. Automatic reboot recovery is not part of this V49 one-shot version; keep the machine awake for the campaign.
