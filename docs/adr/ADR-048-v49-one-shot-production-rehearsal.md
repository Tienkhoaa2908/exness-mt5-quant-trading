# ADR-048 — V49 one-shot production rehearsal

Date: 2026-08-22
Status: Accepted; live-policy interpretation governed by ADR-049

## Context

V45–V48 already spent substantial time validating historical robustness, frozen strategy identity, deterministic builds, state provenance, startup semantics and real-time observer operation. Re-running those investigations as separate promotion gates would add latency without proportionate information.

The project objective is production/live trading with real capital on Exness. The immediate engineering need of V49 is narrower: prove that the frozen breadth4 strategy can drive an automated broker execution loop cleanly — entry, exit, SL/TP lifecycle, reconciliation, notifications and evidence capture — under Exness DEMO conditions before the dedicated live-deployment engineering milestone.

## Decision

Replace the previous multi-stage post-V48 promotion sequence with one integrated V49 campaign named **one-shot production rehearsal**.

Historical/alpha evidence is inherited. V49 does not reopen same-sample optimization and does not rerun V45/V46 historical campaigns.

V49 performs in one campaign:

`frozen breadth4 signal -> virtual decision -> native Exness DEMO execution -> transaction reconciliation -> push notification -> measured fill/friction logging -> continuity/watchdog checks -> final automated verdict + one ZIP`

## What is inherited instead of rerun

Inherited evidence includes:
- accepted V45/V46 historical robustness work;
- frozen `v46_hl10_thr0p05_breadth4` identity;
- deterministic V48 source/provenance chain;
- startup/config/compile hardening from V48;
- account-mode classification and safety checks;
- no-Martingale/no-grid/no-doubling rule;
- research risk ceiling <=1% per strategy trade.

These are checked by identity/invariant assertions, not rerun as full experiments.

## V49 scope

V49 is the **broker-DEMO rehearsal build**. It uses MT5 native trade APIs under the account-mode contract implemented for this version and preserves the frozen strategy intent.

V49 must:
- preserve frozen breadth4 decision logic;
- use a dedicated magic number and own only its own XAUUSDm positions/orders;
- synchronize broker intent from the primary virtual book rather than creating a second alpha path;
- open/close broker DEMO positions automatically;
- attach SL/TP when supported by the symbol/trade request;
- verify server return codes and record requests/results;
- consume `OnTradeTransaction` for broker-event reconciliation;
- prevent duplicate orders;
- stop new broker entries on reconciliation/safety failure;
- send optional MetaQuotes push notifications for START, OPEN, CLOSE, HALT and FINAL;
- maintain a compact status/dashboard;
- produce one final verdict and one evidence ZIP.

The DEMO-only account guard in V49 is phase-specific. It is not a prohibition on researching or designing the later real-capital production deployment.

## Simplified acceptance rule

This is an execution/operations rehearsal, not another alpha-discovery test.

Minimum useful sample:
- >=3 actual XAUUSD market-active dates; and
- >=3 completed native broker-DEMO round trips;
- or hard stop at 14 calendar days.

A run may finish `LIVE_CANDIDATE_READY` only if the minimum useful sample is met and there are:
- zero account-mode guard violations during V49;
- zero duplicate broker entries;
- zero direction mismatches between virtual intent and owned broker position;
- zero unresolved owned-position reconciliation mismatches;
- no catastrophic trade-loop failure;
- broker request reject ratio <=20%;
- strategy source/identity unchanged from the frozen parent.

Spread/slippage/latency are measured and reported. They are diagnostic unless they produce repeated execution failure or materially break reconciliation; no new alpha threshold is tuned from them.

If the hard 14-day stop is reached without the minimum sample, verdict is `INSUFFICIENT_EXECUTION_SAMPLE`, not an automatic strategy rejection.

## Notifications

MetaTrader push notifications are the preferred phone channel. MetaQuotes ID is configured in terminal settings, not stored in Git. V49 treats notification delivery as observability: a notification failure is logged but does not create a duplicate trade or alter alpha.

## One-run operating model

The V49 starter builds/compiles/launches V49 and starts a detached supervisor. Git Bash may then be closed; MT5 and the supervisor continue on the PC.

The supervisor watches status until FINAL or timeout and packages one ZIP. It does not retune strategy parameters.

## Live transition semantics

ADR-049 is authoritative:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- V49 is the final integrated DEMO execution rehearsal before the production/live deployment engineering milestone;
- current readiness remains `LIVE_READINESS=PENDING_V49_FINAL` until the broker-DEMO sample is complete;
- a successful V49 final may promote the system to `LIVE_CANDIDATE_READY`.

No Martingale, uncontrolled grid or doubling after loss.
