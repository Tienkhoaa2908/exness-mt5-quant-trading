# ADR-049 — Live trading research target and readiness semantics

Date: 2026-08-22
Status: Accepted

## Context

The project has completed substantial historical strategy research and is now running the V49 broker-DEMO production rehearsal. Earlier project phases used strong statements such as `REAL-MONEY LIVE TRADING = FORBIDDEN`, `real_money_authorized=0`, or real-account refusal as phase-specific safety guards while the execution stack was still being validated.

Those statements must not be interpreted as a permanent prohibition on researching, designing, evaluating or preparing production/live trading with real capital.

The project owner has explicitly set production/live trading on Exness with real capital as the intended end state.

## Decision

The authoritative project policy is now:

- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`;
- production/live trading with real capital is an explicit project objective;
- research may include live-account architecture, capital sizing, risk controls, deployment workflow, VPS/always-on operations, monitoring, reconciliation, recovery and production-readiness evaluation;
- phase-specific DEMO guards remain valid only for the build/campaign in which they were introduced;
- historical evidence describing a DEMO-only build is preserved as historical fact and is not a project-wide prohibition.

## Readiness semantics

Project intent and current evidence are separate fields.

Current intent:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Current evidence status after V49 startup:
- V49 static suite passed 9/9;
- secret scan passed;
- deterministic V46 -> V47 -> V48 parent chain passed;
- V49 generated source compiled in MetaEditor with `0 errors, 0 warnings`;
- V49 reached broker-DEMO READY and detached supervision started;
- the campaign is still waiting for market-active XAUUSD observations and broker-DEMO round trips.

Therefore the current readiness label is:

`LIVE_READINESS=PENDING_V49_FINAL`

It is not evidence-correct to write `LIVE_READY=1` before V49 produces its final execution/reconciliation evidence. When V49 finishes successfully, the project may promote the classification to `LIVE_CANDIDATE_READY` and begin the dedicated production/live deployment engineering milestone.

## Supersession

This ADR supersedes any blanket wording elsewhere that says real-money/live research is permanently forbidden.

It does not erase historical facts such as V48 or V49 being deliberately DEMO-only builds. Those restrictions describe the semantics of those specific runtime versions, not the permanent project objective.

ADR-047 and ADR-048 remain useful historical design records but must be read through this ADR when interpreting project-wide live-trading policy.

## Permanent engineering invariants

The live target does not relax core engineering constraints:
- no Martingale;
- no uncontrolled grid;
- no doubling after loss;
- bounded position risk;
- deterministic strategy identity during a validation campaign;
- broker/account/symbol ownership checks;
- duplicate-order prevention;
- reconciliation and evidence capture;
- no credentials or secrets committed to Git.
