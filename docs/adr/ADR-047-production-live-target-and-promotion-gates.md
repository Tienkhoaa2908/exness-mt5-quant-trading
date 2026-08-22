# ADR-047 — Production/Live target and promotion gates

Date: 2026-08-22
Status: Accepted

## Context

Project documentation previously used the blanket statement `REAL-MONEY LIVE TRADING = FORBIDDEN` as a research-stage safety guard. That wording is no longer the intended long-term product objective.

The project owner has clarified that paper and DEMO validation are intermediate stages. The long-term objective is to build a system that can be evaluated for production/live trading with real capital on Exness.

At the same time, the currently active V48 campaign is already running under a frozen DEMO-paper safety contract. Changing its account/execution semantics mid-session would invalidate the forward evidence and create continuity risk.

## Decision

1. The long-term project objective is **production/live trading with real capital**, conditional on explicit validation and readiness gates.
2. Current V48 remains unchanged: DEMO feed + virtual USD40 paper execution, no broker-order path, terminal trading permission OFF, DLL permission OFF.
3. Paper/DEMO is not the final destination. It is a required promotion layer.
4. A positive few days or one profitable week is not sufficient promotion evidence.
5. Promotion toward production must proceed through distinct evidence layers before a final readiness decision.

## Required promotion sequence

The target sequence is:

`historical validation -> forward virtual paper -> native Exness DEMO-order parity -> measured execution-friction stress -> restart/reconciliation/fault tests -> independent risk/kill-switch review -> LIVE_CANDIDATE_READY / NOT_READY`

### Gate A — forward paper

At minimum use the preregistered V48 rule:
- >=10 actual XAUUSD trading days; and
- >=20 closed primary paper trades;
- no continuity/safety violation;
- risk gates remain satisfied.

### Gate B — native Exness DEMO parity

Use the same frozen decision logic and compare virtual decisions with actual broker DEMO execution. Measure at least:
- direction/order intent parity;
- entry/exit price difference;
- spread at decision/execution;
- slippage;
- fill delay;
- rejected or missing orders;
- duplicate-order prevention;
- SL/TP/order lifecycle integrity.

### Gate C — friction and delay stress

Evaluate the strategy under measured execution costs and adverse variants, including higher spread/slippage and execution delay. Promotion must not depend on zero-friction assumptions.

### Gate D — operational resilience

Test at least:
- disconnect/reconnect;
- terminal restart while flat;
- explicit handling of restart with open strategy exposure;
- stale-feed detection;
- duplicate-process/session prevention;
- state reconciliation;
- evidence/log integrity.

### Gate E — independent risk controls

Production readiness must include controls that are independent of alpha decisions, including bounded risk, drawdown/health halts, account/symbol identity checks, reconciliation and kill-switch semantics. No Martingale, uncontrolled grid or doubling after loss is allowed.

### Final decision

The research/engineering process may conclude only one of:
- `LIVE_CANDIDATE_READY`; or
- `NOT_READY` / `HOLD` with failed gates identified.

`LIVE_CANDIDATE_READY` is a readiness classification. It does not mean that an active paper/DEMO session should automatically change account or execution mode.

## Consequences

- Documentation must stop describing real-money trading as permanently forbidden for the entire project.
- Documentation must continue to state clearly when a specific active milestone, such as V48, forbids real-account/broker execution.
- Future research plans must distinguish project objective from current-phase execution permissions.
- Native broker-DEMO parity is a mandatory bridge between virtual paper evidence and any live-readiness conclusion.
- Current V48 runtime/source/state must not be changed solely to reflect this long-term objective.

## Non-decisions

This ADR does not change:
- frozen V46/V48 strategy logic;
- the currently active V48 run id;
- V48 source SHA;
- V48 DEMO-only account guard;
- V48 `TERMINAL_TRADE_ALLOWED=0` requirement;
- current paper state or evidence;
- current stop-risk research ceiling.
