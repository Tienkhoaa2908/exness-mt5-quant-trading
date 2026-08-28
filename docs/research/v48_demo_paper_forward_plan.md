# V48 Demo-Paper Forward Campaign

Date: 2026-08-22

## Historical policy note

This document records the V48 phase-specific paper contract. Project-wide policy has since been updated by `docs/adr/ADR-049-live-trading-research-and-readiness-semantics.md`:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Therefore statements below about DEMO-only execution apply to V48 itself and must not be interpreted as a permanent prohibition on researching or preparing later production/live trading with real capital.

## Purpose

Stop the historical-research loop and move the accepted V46 breadth4 mechanism into a finite forward paper campaign on the user's MT5 demo terminal.

V48 is operational validation, not another alpha search.

The frozen primary remains `v46_hl10_thr0p05_breadth4`:
- HL10 realized-R EWMA router;
- selected expert threshold 0.05;
- breadth health threshold 0.05;
- require >=4 of 5 shadow experts healthy before opening paper risk;
- existing entry/exit/stop/risk geometry unchanged;
- virtual USD40 r1.00% continuous paper book;
- no ADX/DI gate is active.

ADX/DI may continue to be logged/analyzed as shadow diagnostics only. They cannot change a V48 decision.

## What "paper" means in V48

The observer runs on the real-time XAUUSDm M15 feed of an MT5 DEMO account and uses the existing internal virtual-book engine. It never submits a broker order.

V48 conditions:
- `ACCOUNT_TRADE_MODE_DEMO` is mandatory;
- REAL accounts are rejected in `OnInit` for V48;
- Strategy Tester mode is rejected by the V48 observer;
- terminal-level automated trading permission must be OFF (`AllowLiveTrading=0`, `TERMINAL_TRADE_ALLOWED=0`);
- terminal-level DLL permission must be OFF;
- generated V48 source forbids native broker-order APIs;
- no native/external broker-order path may be added to the frozen V48 source.

These are V48 runtime semantics only. Historical V48 wording was: Real-money order execution remains outside the authorized scope of this V48 campaign.

## V48 v1 startup incident

The first V48 live-paper launch passed static tests, secret scan, source provenance, deterministic build, MetaEditor `0 errors, 0 warnings`, and exact V46 state seeding, then failed before an accepted session.

V48 v2 improved startup observability and permission diagnostics without changing strategy decisions.

Frozen V48 v2 source SHA:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Realtime chart dashboard

V48 v2 displays RUNNING state, healthy breadth, virtual balance/equity, max MTM DD, current virtual position, entry/current/SL/TP, open R/PnL, heartbeat, and explicit V48 broker-order/live-authorization markers.

Dashboard refreshes on ticks and every 30 seconds.

## State continuity

Accepted V46 end-state SHA256:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`.

V48 seeds its paper state from accepted V46 evidence when necessary and does not alter accepted V46 artifacts.

V48 deliberately does not run an automatic mid-month historical catch-up that could contaminate adaptive state with artificial closes.

V48 paper state path:
`mt5_quant\\paper\\v48_demo_paper_state.csv`.

## Finite campaign stop rule

The original V48 preregistration was intentionally finite:
- at least 10 XAUUSD trading days;
- at least 20 primary breadth4 paper trades have closed;
- Hard maximum observation horizon: 30 calendar days.

Do not automatically extend the campaign.

The operational success label for that historical gate was `PAPER_OPERATIONAL_PASS`.

V48 was later operationally superseded by the V49 one-shot production rehearsal, which inherited the frozen strategy evidence and moved to native broker-DEMO execution.

## Historical V48 pass criteria

V48 operational checks covered account/permission safety, source identity, heartbeat/status coherence, duplicate prevention, state continuity, virtual-ledger reconciliation and bounded paper drawdown.

These criteria remain useful historical evidence but are not current project-wide restrictions on live research.

## Decision evolution

At the end of V48, paper evidence was intended to promote the project toward native broker execution testing. That promotion has now occurred in V49.

Current project-wide policy explicitly allows live-trading research and targets real-capital production deployment after readiness evidence. V48 contains no broker-order route because it was a paper observer; that fact does not define the permanent scope of the project.
