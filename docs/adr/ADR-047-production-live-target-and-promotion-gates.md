# ADR-047 — Production/Live target and promotion gates

Date: 2026-08-22
Status: Superseded by ADR-049 for project-wide live-trading policy

## Context

Project documentation previously used the blanket statement `REAL-MONEY LIVE TRADING = FORBIDDEN` as a research-stage guard. That wording is no longer authoritative.

The project owner has set production/live trading with real capital on Exness as the intended end state. Paper and DEMO validation are intermediate engineering stages, not the permanent scope of the system.

## Decision retained from ADR-047

1. The project objective is production/live trading with real capital.
2. Historical and current validation builds may use phase-specific DEMO/paper guards without creating a project-wide live prohibition.
3. Historical alpha evidence should be inherited rather than repeatedly rerun when the strategy identity is frozen.
4. Native broker execution, reconciliation, observability and bounded risk must be demonstrated before a readiness classification.
5. No Martingale, uncontrolled grid or doubling after loss.

## Evolution after ADR-047

The original multi-gate sequence in this ADR was later intentionally collapsed by ADR-048 into the V49 one-shot broker-DEMO production rehearsal to reduce duplicated testing and time-to-readiness.

ADR-049 then made the live policy explicit:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- production/live architecture, capital sizing, risk controls, deployment workflow, monitoring, reconciliation, recovery and VPS/always-on engineering are legitimate project research topics;
- DEMO-only restrictions in V48/V49 describe those builds, not the permanent project boundary.

## Current readiness semantics

The project must distinguish target from evidence:

`LIVE_DEPLOYMENT_TARGET=1`

Current status after accepted V49 startup:

`LIVE_READINESS=PENDING_V49_FINAL`

A clean V49 final can promote the engineering classification to `LIVE_CANDIDATE_READY`. Until the V49 broker-DEMO execution sample exists, `LIVE_READY=1` would overstate the available evidence.

## Historical note

V48 was deliberately DEMO-feed + virtual-paper only and V49 is deliberately native broker-DEMO execution. Their account guards are preserved as historical/runtime facts. They are not statements that real-money research or future production/live deployment is prohibited.

See ADR-049 for the authoritative live-trading policy and ADR-048 for the current one-shot rehearsal design.
