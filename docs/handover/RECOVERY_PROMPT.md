# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Authoritative objective

The project explicitly targets production/live trading with real capital on Exness.

Project-wide policy:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- live-account architecture, capital sizing, risk controls, deployment workflow, VPS/always-on operation, monitoring, reconciliation and recovery are valid research/engineering topics;
- phase-specific DEMO guards are runtime-version constraints, not permanent project prohibitions.

Current readiness:
`LIVE_READINESS=PENDING_V49_FINAL`

Do not claim `LIVE_READY=1` before V49 completes its broker-DEMO execution sample.

Read `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md` for the authoritative semantics.

## Frozen strategy / inherited evidence

Frozen primary: `v46_hl10_thr0p05_breadth4`.
Accepted V46 evidence commit: `655bf2f77503d91d0749d2f5c99cc0ad8678c388`.
Accepted V46 ZIP SHA256: `ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.
Accepted V46 state SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.
Frozen V48 source SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

Do not reopen same-sample optimization. No Martingale, uncontrolled grid or doubling after loss.

## Active V49 session — do not start a second run

Accepted V49 Windows startup occurred on 2026-08-22 from local HEAD:
`2a12498d8b054127dcff766cd91e4a6b37aeef5a`

Run id:
`v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`

Accepted startup evidence:
- static tests 9/9 PASS;
- secret scan PASS;
- deterministic V46 -> V47 -> V48 chain PASS;
- V49 source SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- MetaEditor `0 errors, 0 warnings`;
- EX5 SHA256 `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- transitioned state SHA256 `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`;
- startup config PASS SHA256 `a104bb2d22dac785cedb0f9753cc62976f887ffbede532cf8cff2d8a1467691b`;
- `V49_DEMO_REHEARSAL_READY=1`;
- `V49_ONE_SHOT_STARTED=1`;
- `DEMO_BROKER_EXECUTION=1`;
- detached supervisor PID reported `4452`.

Initial counters were `MARKET_DAYS=0` and `ROUND_TRIPS=0` because the market was closed at startup.

Do not restart V49 merely because XAUUSDm is closed. Keep the PC, Internet and MT5 running; Git Bash is not required after START PASS.

## V49 authoritative branch

`agent/v49-one-shot-demo-rehearsal`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`
3. `docs/adr/ADR-048-v49-one-shot-production-rehearsal.md`
4. `docs/research/v49_one_shot_demo_rehearsal_plan.md`
5. `docs/windows_mt5_exness_setup.md`
6. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`

Do not fetch/reset the active Windows checkout solely to obtain docs-only commits while the V49 session is running.

## V49 one-shot model

`frozen breadth4 virtual intent -> native Exness DEMO order -> automatic broker close -> OnTradeTransaction reconciliation -> phone push -> execution logging -> finite final verdict -> one ZIP`

Historical robustness is inherited rather than rerun.

The V49 account-mode guard is specific to this rehearsal build. It is not a project-wide restriction on real-capital research or the later production/live deployment milestone.

## V49 simplified acceptance

Minimum useful execution sample:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

Clean result:
`LIVE_CANDIDATE_READY`

Critical execution/reconciliation failure:
`HOLD`

Hard stop without minimum sample:
`INSUFFICIENT_EXECUTION_SAMPLE`

Current readiness before FINAL:
`LIVE_READINESS=PENDING_V49_FINAL`

## Notifications

V49 uses `SendNotification()` when MetaTrader push notifications are configured. MetaQuotes ID stays in terminal settings and is not committed.

Expected phone events: START, DEMO OPEN, DEMO CLOSE, HALT, FINAL.

## Final evidence

Supervisor:
`runtime/v49_demo_rehearsal/SUPERVISE_V49_ONE_SHOT.py`

Final evidence directory:
`runtime/v49_demo_rehearsal/OUTPUT_V49/`

The supervisor creates one final ZIP containing `bundle_manifest_sha256.txt` after EA FINAL or timeout.

## Next milestone after V49 PASS

If FINAL is `LIVE_CANDIDATE_READY`, proceed directly to a dedicated production/live deployment engineering milestone. Do not rerun V45/V46 historical campaigns unless new evidence specifically invalidates the inherited assumptions.

That next milestone may research and design:
- live-account deployment architecture;
- real-capital sizing/capital-at-risk policy;
- production risk and kill-switch controls;
- VPS/always-on operation;
- monitoring/reconciliation/recovery;
- production rollout/checklist based on the V49 evidence bundle.
