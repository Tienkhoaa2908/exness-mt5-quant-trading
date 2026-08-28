# Exness / MetaTrader 5 Quant Trading System

**Mục tiêu: production/live trading trên Exness sau khi technical và operational
readiness evidence được xác nhận.**

`LIVE_RESEARCH_ALLOWED=1`

`LIVE_DEPLOYMENT_TARGET=1`

No Martingale, uncontrolled grid or doubling after loss.

## Current candidate

Frozen candidate:

`v52_b4_or_b3_trend_bos`

Accepted V52R real-tick evidence:

- breadth4: 819 trades, PF 1.2894, annualized 21.47%, max DD 16.60%;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, max DD 16.10%.

Generated-tick V52 is invalidated by data contamination and is not promotion evidence.

## Current milestone — V54 Production Readiness

Branch:

`agent/v54-production-readiness-hardening`

V54 inherits the selected V53 candidate and proven V49/V50 broker adapter. It adds
production safety and operations hardening without retuning alpha:

- `XAUUSDm M15`;
- owned magic `540054`;
- max one owned strategy position;
- stop-based risk cap;
- daily/session loss and max-drawdown protection;
- spread, stale tick, stale strategy-state and disconnect guards;
- repeated broker-reject halt;
- ownership and SL/TP validation;
- deterministic restart/reconciliation;
- request/retcode/deal audit trail;
- MetaQuotes phone notifications;
- immutable snapshot evidence ZIP;
- fail-closed rollback runbook.

Current activation boundary:

`PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE`

`real_money_authorized=0`

V54 retains the DEMO account guard while technical readiness is verified. This is a
phase-specific build constraint; ADR-049 still defines live deployment as the project
target.

## Inherited evidence

`V50_EXECUTION_PIPELINE=PASS`

`V52R_REAL_TICK_REPRO=PASS`

`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

Accepted V52R ZIP SHA256:

`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Accepted V53 recovered ZIP SHA256:

`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

## Canonical operator entrypoint

`bash runtime/v54_production_readiness/START_V54_PRODUCTION_READINESS_GIT_BASH.sh`

The runner performs branch/working-tree checks, static test, secret scan, deterministic
source build, MetaEditor compile verification, controlled MT5 startup, DEMO READY
verification and automatic immutable startup evidence packaging.

Do not bypass failed preflight checks.

## Authority

Read in this order:

1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/RECOVERY_PROMPT.md`
3. `docs/adr/ADR-056-v54-production-readiness-safety-envelope.md`
4. `docs/runbooks/V54_PRODUCTION_READINESS_RUNBOOK.md`
5. `docs/adr/ADR-055-immutable-snapshot-evidence-packaging.md`
6. `docs/research/v52r_real_tick_results_2026-08-26.md`
7. `docs/research/v53_timebox_waiver_results_2026-08-28.md`
