# V48 startup acceptance — 2026-08-22

## Policy note

This note records historical V48 startup evidence. Project-wide live policy is now governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V48 itself was DEMO/paper-only. That fact does not prohibit research or preparation for later production/live trading with real capital.

## Scope

This note records the first verified successful startup of the frozen V48 DEMO-paper observer. It is startup/operational evidence only, not profitability evidence and not authorization for V48 to place real-money orders.

## Runtime code identity

Windows checkout at accepted startup:
- branch: `agent/v48-demo-paper-forward`;
- runtime code HEAD: `3e5f126772c9c2d378f9b3e09720cc9789d76330`;
- frozen primary: `v46_hl10_thr0p05_breadth4`;
- frozen V48 generated MQL SHA256: `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`;
- accepted V46 state seed SHA256: `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

## Pre-start gates observed PASS

User-supplied Windows output showed:
- secret scan PASS;
- original V48 static tests PASS 10/10;
- hardened v1 static tests PASS 6/6;
- hardened v2 static tests PASS 5/5;
- V34 causal tape PASS;
- exact V46/V47/V48 source provenance PASS;
- V48 compile reused with `0 errors, 0 warnings`;
- prior failed-init debris SHA `f415050b...` was classified by exact reason-8 evidence and quarantined;
- exact accepted V46 state was re-seeded;
- root startup alias source/EX5 verification PASS;
- hardened-v2 startup INI self-check PASS;
- terminal AutoTrading was requested OFF before launch.

## Accepted startup

Terminal launch PID reported: `1968`.

Accepted V48 run id:
`v48_demo_paper_forward_v2__XAUUSDm__PERIOD_M15__2026-08-22_10-52-37__471937`

Session start reported by MT5:
`2026.08.22 10:52:37`

READY evidence:
- account mode `DEMO`;
- `TERMINAL_TRADE_ALLOWED=0`;
- `MQL_TRADE_ALLOWED=0`;
- `TERMINAL_DLLS_ALLOWED=0`;
- `MQL_DLLS_ALLOWED=0`;
- candidate `v46_hl10_thr0p05_breadth4`;
- book `usd40_r1p0_cent_continuous`;
- balance `$40.000000`;
- equity `$40.000000`;
- healthy HL10 count `3/5`;
- position `FLAT`;
- broker orders `0`;
- V48 real-money authorization marker `0`.

The hardened launcher also observed `STATUS_TIMER_REFRESH_PASS=1` and `CHART_DASHBOARD=ENABLED`, proving OnTimer/status/dashboard operation while XAU was closed.

## Interpretation

This was the first accepted V48 operational session. Market closure did not invalidate the observer, timer or dashboard.

`HEALTHY_HL10_COUNT=3` was below the frozen breadth4 entry gate, so `Waiting for breadth4 opportunity` was expected.

`CURRENT_PRICE=0.000` while flat was an observability semantic of the V48 source and not evidence of a broken market connection.

## Known finite-gate issue

`STATUS_V48_DEMO_PAPER.py` reported `ELAPSED_WEEKDAYS_APPROX` rather than actual XAUUSD trading days. This was an observability limitation of V48 and is historical context only now that V49 has superseded V48 as the active execution rehearsal.

## Historical V48 operating rule

While V48 was active:
- MT5 stayed on DEMO;
- Algo Trading stayed OFF;
- a second V48 session was not started;
- active paper state was not reset/reseeded;
- status checks were read-only.

Those restrictions were specific to V48. They are not the project-wide live policy. Current project direction is defined by ADR-049 and the active V49/production-readiness workflow.
