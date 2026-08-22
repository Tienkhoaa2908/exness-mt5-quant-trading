# Windows MT5 / Exness — V49 One-Shot DEMO Production Rehearsal

Updated: 2026-08-22

Environment: Exness Technologies Ltd.; Exness DEMO account; observed server `Exness-MT5Trial6`; symbol `XAUUSDm`; timeframe M15.

Long-term project objective is production/live readiness. V49 itself is **native broker DEMO execution only** and hard-refuses REAL/non-DEMO accounts before broker requests.

## Frozen strategy

Primary: `v46_hl10_thr0p05_breadth4`.
Frozen V48 parent SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not retune breadth/HL/threshold during V49. V49 adds an execution adapter around the frozen virtual intent.

## Current V48 to V49 transition

An accepted V48 observer may still be running. Transition only when V48 primary virtual position is `FLAT`.

Before the single V49 start:
1. Verify V48 is FLAT using its read-only status command.
2. Deliberately close MT5 once, which stops the V48 observer.
3. Keep the terminal account as Exness DEMO.
4. Close MetaEditor if open.
5. Optional phone push: configure MetaQuotes ID under MT5 Notifications and test it in the terminal UI.

Do not transition while a V48 virtual position is open.

## V49 branch / one command

Branch:
`agent/v49-one-shot-demo-rehearsal`

Canonical entrypoint:
`runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

The starter performs:
- Python/static tests;
- secret scan;
- exact V46 -> V47 -> frozen V48 parent rebuild;
- V49 execution-adapter generation;
- MetaEditor compilation and mandatory `0 errors, 0 warnings`;
- current V48 adaptive-state transition copy;
- V49 startup INI creation;
- MT5 launch;
- DEMO READY verification;
- detached supervisor launch.

After `V49_ONE_SHOT_STARTED=1`, Git Bash may be closed. Keep the PC, Internet and MT5 running.

## V49 native broker DEMO contract

Startup config enables AutoTrading because V49 must submit DEMO broker requests:
- `AllowLiveTrading=1`;
- `Enabled=1`;
- `AllowDllImport=0`.

The MQL EA independently hard-checks before execution:
- account trade mode is DEMO;
- `_Symbol == XAUUSDm`;
- `_Period == PERIOD_M15`;
- terminal/MQL trading permission is ON;
- DLL permission is OFF;
- no ambiguous foreign XAUUSDm position exists at startup;
- no duplicate owned V49 position exists.

Dedicated magic: `490049`.

V49 manages only positions carrying its own magic. It never closes or modifies manual/foreign positions.

## Automatic entry / exit

Frozen primary virtual book remains strategy intent owner.

Reconciliation loop:
- virtual FLAT + owned broker FLAT -> no action;
- virtual OPEN + owned broker FLAT -> native DEMO Buy/Sell;
- virtual OPEN + matching owned broker OPEN -> maintain;
- virtual FLAT + owned broker OPEN -> close owned broker position;
- duplicate owned positions or direction mismatch -> HALT new entries and notify.

SL/TP from the frozen virtual intent is supplied on native DEMO entry when the broker/symbol accepts it.

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

The ZIP includes the V49 status/final/event/transaction evidence, transitioned state/run outputs when available, and `bundle_manifest_sha256.txt`. ZIP CRC is checked before it is declared complete.

## Important limitation

V49 v1 is designed as one continuous rehearsal. PC sleep/shutdown or Windows reboot stops MT5 and therefore stops native execution. Automatic reboot recovery is not part of this one-shot version; keep the machine awake for the campaign.
