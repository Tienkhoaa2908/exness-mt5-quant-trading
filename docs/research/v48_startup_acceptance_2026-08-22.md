# V48 startup acceptance — 2026-08-22

## Scope

This note records the first verified successful startup of the frozen V48 DEMO-paper observer. It is startup/operational evidence only, not profitability evidence and not real-money authorization.

REAL-MONEY LIVE TRADING remains forbidden.

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
- real money authorized `0`.

The hardened launcher also observed `STATUS_TIMER_REFRESH_PASS=1` and `CHART_DASHBOARD=ENABLED`, proving OnTimer/status/dashboard operation while XAU was closed.

The user-provided screenshot visibly showed the V48 chart dashboard, `State: RUNNING`, `Breadth: 3/5`, `$40.00` balance/equity, `Position: FLAT`, a live heartbeat, and `REAL MONEY AUTHORIZED: NO`. The terminal Algo Trading button was OFF.

## Interpretation

This is the first accepted V48 operational session. Do not restart it merely because the market is closed. Market closure means no new XAU tick/trade opportunity; it does not invalidate the observer, timer or dashboard.

`HEALTHY_HL10_COUNT=3` is below the frozen breadth4 entry gate, so `Waiting for breadth4 opportunity` is expected and no new paper risk should be opened.

`CURRENT_PRICE=0.000` while flat is an observability semantic of the current V48 source: `V48PaperEquity()` only populates `px` when the virtual position is open. It is not evidence of a broken market connection. Do not change MQL during the active session merely to make this cosmetic field nonzero.

## Known finite-gate issue

`STATUS_V48_DEMO_PAPER.py` currently reports `ELAPSED_WEEKDAYS_APPROX` and uses that weekday count in `FINITE_GATE_READY`. This is not the preregistered requirement of >=10 actual XAUUSD trading days.

Therefore during this session:
- `FINITE_GATE_READY` must not be treated as authoritative for the 10-day criterion;
- the final review must count actual observed XAUUSD trading days from run evidence;
- a future observability-only milestone should replace the weekday approximation without restarting or changing the active strategy.

## Active-session operating rule

While this run is active:
- keep MT5 open on the DEMO account;
- keep Algo Trading OFF;
- do not start V48 a second time;
- do not reset/reseed the active paper state;
- use `STATUS_V48_DEMO_PAPER_GIT_BASH.sh` for read-only checks;
- package/analyze the run at an appropriate evidence checkpoint or final finite-gate review;
- LIVE remains forbidden.
