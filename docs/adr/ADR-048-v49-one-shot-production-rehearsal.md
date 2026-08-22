# ADR-048 — V49 one-shot production rehearsal

Date: 2026-08-22
Status: Accepted

## Context

V45–V48 already spent substantial time validating historical robustness, frozen strategy identity, deterministic builds, state provenance, DEMO-account safety, startup semantics and real-time observer operation. Re-running those investigations as separate promotion gates would add latency without proportionate information.

The project objective remains eventual production/live use after a readiness decision. The current engineering need is narrower: prove that the frozen breadth4 strategy can drive an automated broker execution loop cleanly — entry, exit, SL/TP lifecycle, reconciliation, notifications and evidence capture — under Exness DEMO conditions.

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
- DEMO account classification and real-account refusal pattern;
- no-Martingale/no-grid/no-doubling rule;
- research risk ceiling <=1% per strategy trade.

These are checked by identity/invariant assertions, not rerun as full experiments.

## V49 scope

V49 is native broker **DEMO-order** rehearsal. It may use MT5 trading APIs only while `ACCOUNT_TRADE_MODE_DEMO` is true. Any REAL or non-DEMO account is a hard initialization refusal.

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

## Simplified acceptance rule

This is an execution/operations rehearsal, not another alpha-discovery test. Therefore acceptance is intentionally lighter than the previous promotion ladder.

Minimum useful sample:
- >=3 actual XAUUSD market-active dates; and
- >=3 completed native broker-DEMO round trips;
- or hard stop at 14 calendar days.

A run may finish `LIVE_CANDIDATE_READY` only if the minimum useful sample is met and there are:
- zero real-account guard violations;
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

The user should perform one deliberate transition from V48 to V49 while flat, then run one canonical Git Bash starter. The starter builds/compiles/launches V49 and starts a detached supervisor. Git Bash may then be closed; MT5 and the supervisor continue on the PC.

The supervisor watches status until FINAL or 14 calendar days, then packages one ZIP. It does not retune strategy parameters.

## Safety / non-decisions

- V49 is DEMO broker execution only.
- REAL/non-DEMO account remains hard-refused in V49.
- This ADR does not implement or authorize real-money broker execution.
- No Martingale, uncontrolled grid or doubling after loss.
- Existing V48 active session is not modified merely by creating the V49 branch.
