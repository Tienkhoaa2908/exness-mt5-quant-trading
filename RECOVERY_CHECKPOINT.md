# Recovery checkpoint — V49 One-Shot Production Rehearsal

Ngày: 2026-08-22.

## Project policy

`LIVE_RESEARCH_ALLOWED=1`

`LIVE_DEPLOYMENT_TARGET=1`

Mục tiêu chính thức của project là production/live trading trên Exness bằng vốn thật sau khi hoàn tất readiness evidence. Các guard DEMO-only của V48/V49 là phase-specific runtime constraints, không phải lệnh cấm nghiên cứu tiền thật cho toàn dự án.

Authoritative policy: `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`.

## Active runtime

V49 accepted Windows startup:
- local startup HEAD `2a12498d8b054127dcff766cd91e4a6b37aeef5a`;
- static tests 9/9 PASS;
- secret scan PASS;
- MetaEditor `0 errors, 0 warnings`;
- V49 source SHA256 `b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599`;
- EX5 SHA256 `72c339b37e39efd54e664ce2fb1d9d7736d94d46615849d8887f88347d674175`;
- `V49_DEMO_REHEARSAL_READY=1`;
- `V49_ONE_SHOT_STARTED=1`;
- run id `v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`;
- detached supervisor reported PID `4452`.

Initial `MARKET_DAYS=0` and `ROUND_TRIPS=0` because XAUUSD was closed at startup.

Do not start a second V49 run while the accepted session is active.

## Current readiness

`LIVE_READINESS=PENDING_V49_FINAL`

This is not yet `LIVE_READY=1` because the broker-DEMO execution sample has not completed.

V49 final rule:
- >=3 market-active XAUUSD dates;
- >=3 completed broker-DEMO round trips;
- clean execution/reconciliation -> `LIVE_CANDIDATE_READY`;
- critical failure -> `HOLD`;
- insufficient sample at hard stop -> `INSUFFICIENT_EXECUTION_SAMPLE`.

If V49 finishes `LIVE_CANDIDATE_READY`, next milestone is production/live deployment engineering: live-account architecture, real-capital sizing, risk controls, VPS/always-on operation, monitoring, reconciliation, recovery and rollout checklist.
