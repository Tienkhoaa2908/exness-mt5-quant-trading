# Exness / MetaTrader 5 Quant Trading System

**MỤC TIÊU CHÍNH: XÂY HỆ THỐNG PRODUCTION/LIVE TRADING TRÊN EXNESS BẰNG VỐN THẬT SAU KHI HOÀN TẤT READINESS EVIDENCE.**

Kho nghiên cứu/engineering quant cho MT5/Exness. `LIVE_RESEARCH_ALLOWED=1` và `LIVE_DEPLOYMENT_TARGET=1`. Không Martingale, uncontrolled grid hoặc doubling after loss.

## Frozen strategy

Primary: `v46_hl10_thr0p05_breadth4`.

Historical/alpha evidence từ V45/V46 và deterministic V48 parent được kế thừa; không mở lại cùng sample để tối ưu breadth/HL/threshold.

Frozen V48 parent SHA256:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Current runtime — V49 One-Shot DEMO Production Rehearsal

Branch:
`agent/v49-one-shot-demo-rehearsal`

Accepted Windows startup evidence on 2026-08-22:
- V49 static tests: 9/9 PASS;
- secret scan PASS;
- deterministic V46 -> V47 -> V48 parent chain PASS;
- V49 source SHA256: `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- MetaEditor: `0 errors, 0 warnings`;
- EX5 SHA256: `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- V49 DEMO READY PASS;
- run id: `v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`;
- detached supervisor started;
- initial `MARKET_DAYS=0`, `ROUND_TRIPS=0` because the market was closed at startup.

V49 performs one integrated campaign:

`frozen virtual intent -> native Exness DEMO entry/exit -> OnTradeTransaction reconciliation -> push notification -> execution logging -> finite final verdict -> one ZIP`

V49 is deliberately a broker-DEMO rehearsal build. Its DEMO-only account guard is **phase-specific**, not a project-wide ban on live research or real-capital deployment engineering.

## Live-trading policy

Authoritative semantics:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- real-capital production/live trading is the intended project end state;
- research may cover live-account architecture, capital sizing, risk controls, deployment workflow, VPS/always-on operations, monitoring, reconciliation and recovery;
- historical DEMO-only restrictions remain historical/runtime facts only.

Current evidence label:

`LIVE_READINESS=PENDING_V49_FINAL`

This is not yet `LIVE_READY=1` because V49 has not completed the broker-DEMO execution sample. A clean V49 final may promote the project to `LIVE_CANDIDATE_READY` and trigger the dedicated production/live deployment engineering milestone.

## V49 simplified acceptance

Minimum useful sample:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

A clean rehearsal may conclude `LIVE_CANDIDATE_READY`; insufficient activity at hard stop -> `INSUFFICIENT_EXECUTION_SAMPLE`; critical execution/reconciliation failure -> `HOLD`.

Historical V45/V46 campaigns are inherited and are not rerun as part of V49.

## One user action

Canonical V49 starter:

`bash runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

The current V49 session is already running. Do not start a second V49 session while the accepted one is active.

After START PASS, Git Bash may be closed. Keep PC + Internet + MT5 running. Detached supervisor creates one final ZIP at:

`runtime/v49_demo_rehearsal/OUTPUT_V49/`

Bundle contains `bundle_manifest_sha256.txt`.

## Authority

Read in this order:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/RECOVERY_PROMPT.md`
3. `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`
4. `docs/adr/ADR-048-v49-one-shot-production-rehearsal.md`
5. `docs/research/v49_one_shot_demo_rehearsal_plan.md`
6. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`
7. `docs/windows_mt5_exness_setup.md`
