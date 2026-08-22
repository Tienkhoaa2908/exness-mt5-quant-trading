# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Project objective — authoritative

The project is explicitly targeting production/live trading with real capital on Exness.

Authoritative policy:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- research may cover live-account architecture, capital sizing, risk controls, deployment workflow, VPS/always-on operation, monitoring, reconciliation and recovery;
- phase-specific DEMO guards are runtime-version constraints, not permanent project prohibitions.

Current evidence classification:

`LIVE_READINESS=PENDING_V49_FINAL`

Do not write `LIVE_READY=1` yet because the accepted V49 session has not completed the required broker-DEMO round-trip sample.

See `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`.

## Frozen alpha / inherited evidence

Frozen primary: `v46_hl10_thr0p05_breadth4`.

Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 adaptive-state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
Frozen V48 source SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not reopen same-sample breadth/HL/threshold tuning. No Martingale, uncontrolled grid or doubling after loss. Research/strategy risk ceiling remains <=1% per trade.

Historical/alpha validation is inherited for V49 and is not rerun as a separate campaign.

## Accepted V49 Windows startup — authoritative active runtime

Branch used locally:
`agent/v49-one-shot-demo-rehearsal`

Local startup HEAD:
`2a12498d8b054127dcff766cd91e4a6b37aeef5a`

Accepted startup evidence from 2026-08-22:
- V49 static tests PASS count=9;
- `SECRET_SCAN_PASS files=102 mode=git-tracked`;
- V46 source PASS SHA256 `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- V47 source PASS SHA256 `7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44`;
- deterministic V48 source PASS SHA256 `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`;
- V49 generated source SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- MetaEditor compile PASS: `Result: 0 errors, 0 warnings`;
- V49 EX5 SHA256 `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- transitioned adaptive state SHA256 `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`;
- V49 startup config PASS SHA256 `a104bb2d22dac785cedb0f9753cc62976f887ffbede532cf8cff2d8a1467691b`;
- `V49_DEMO_REHEARSAL_READY=1`;
- `V49_ONE_SHOT_STARTED=1`;
- `DEMO_BROKER_EXECUTION=1`;
- startup output reported `REAL_MONEY_AUTHORIZED=0` because this specific V49 runtime remains the broker-DEMO rehearsal build.

Accepted run id:
`v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`

Detached supervisor PID reported at startup: `4452`.

Initial campaign counters at startup:
- `MARKET_DAYS=0`;
- `ROUND_TRIPS=0`.

The market was closed at startup, so zero market days/round trips is expected. Do not restart V49 merely because the market is closed.

## V49 one-shot model

V49 performs in one campaign:

`frozen virtual intent -> native Exness DEMO order -> automatic close -> OnTradeTransaction reconciliation -> push notification -> fill/request logging -> finite verdict -> one ZIP`

V49 uses a dedicated magic number `490049`, owns only its own XAUUSDm positions and uses pending-open/pending-close state plus confirmation timeouts to prevent repeated requests while broker state converges.

The V49 DEMO account guard is phase-specific. It exists to make the final broker-execution rehearsal clean; it is not a project-wide ban on real-capital research or later production deployment engineering.

## Simplified V49 acceptance

Minimum useful sample:
- >=3 distinct market-active XAUUSD dates; and
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

A clean final may classify:
`LIVE_CANDIDATE_READY`

Critical execution/reconciliation failure:
`HOLD`

Hard stop before minimum sample:
`INSUFFICIENT_EXECUTION_SAMPLE`

Current status remains:
`LIVE_READINESS=PENDING_V49_FINAL`

## Phone notifications

V49 uses MetaTrader `SendNotification()` when terminal push notifications are configured.

Expected events:
- START;
- DEMO OPEN confirmed;
- DEMO CLOSE confirmed;
- HALT;
- FINAL.

MetaQuotes ID remains terminal configuration and is not committed.

## Active-session operating rule

The accepted V49 session is already running. Do not run the V49 START command again while this session is active.

Keep:
- PC awake;
- Internet connected;
- MT5 open;
- the same Exness DEMO account/session active for this rehearsal.

Git Bash may be closed after startup. The detached supervisor waits for FINAL/timeout and creates one ZIP under:
`runtime/v49_demo_rehearsal/OUTPUT_V49/`

The ZIP contains `bundle_manifest_sha256.txt`.

## Next milestone after successful V49 final

If V49 finishes `LIVE_CANDIDATE_READY`, the next project milestone is dedicated **production/live deployment engineering**, not another historical-alpha campaign. That milestone may research and design:
- live-account deployment architecture;
- real-capital sizing and capital-at-risk policy;
- production risk/kill-switch controls;
- VPS/always-on operation;
- monitoring, reconciliation and recovery;
- production rollout/checklist and evidence.

The exact production deployment implementation must be based on the final V49 evidence bundle rather than assumed before the campaign finishes.
