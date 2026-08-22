# NEXT EXPERIMENT — Active V49 One-Shot Production Rehearsal

Updated: 2026-08-22

The old V29.3 instructions in this file are obsolete.

Authoritative project direction is defined by `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- historical DEMO-only restrictions are phase-specific, not permanent project policy.

Current active run:
`v49_one_shot_demo_rehearsal_v1__XAUUSDm__PERIOD_M15__2026-08-22_12-33-42__536750`.

Accepted startup evidence already includes static 9/9 PASS, secret scan PASS, deterministic parent rebuild, MetaEditor `0 errors, 0 warnings`, V49 DEMO READY and detached supervisor startup.

Initial `MARKET_DAYS=0` and `ROUND_TRIPS=0` were expected because XAUUSD was closed at startup.

Do not start a second V49 session while the accepted run is active. Keep PC + Internet + MT5 running and wait for the one-shot campaign to produce its final evidence ZIP.

Current readiness:
`LIVE_READINESS=PENDING_V49_FINAL`.

V49 final rule:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips;
- clean final -> `LIVE_CANDIDATE_READY`;
- critical execution/reconciliation failure -> `HOLD`;
- insufficient activity at hard stop -> `INSUFFICIENT_EXECUTION_SAMPLE`.

After a clean V49 final, the next milestone is the project’s production/live engineering phase as defined by ADR-049.
