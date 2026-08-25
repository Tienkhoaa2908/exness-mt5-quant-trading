# ADR-051 — Higher-frequency hybrid challenger

Date: 2026-08-25
Status: Accepted for one-shot historical research

## Context

V50 proved the native Exness DEMO execution pipeline with three broker-confirmed open/close round trips and zero broker rejects. The remaining bottleneck is signal frequency: frozen `v46_hl10_thr0p05_breadth4` can remain flat for long periods because it requires at least 4/5 healthy experts.

Blindly lowering the frozen gate from breadth4 to breadth3 would discard the main robustness mechanism that reduced drawdown in V46. V46 already showed breadth3 traded more but had materially worse drawdown.

## Decision

Run one historical tournament with breadth4 as immutable baseline and three preregistered hybrid challengers:

- `v51_b4_or_b3_avg0p075`
- `v51_b4_or_b3_avg0p10`
- `v51_b4_or_b3_avg0p15`

All candidates preserve the breadth4 path. The only extra opportunity lane is when exactly three experts are healthy. That lane is accepted only when the average health score of those three experts clears the candidate's fixed quality floor.

No new indicator, no Martingale/grid, no risk increase, and no broker execution is introduced in the historical source.

## Promotion guardrails

A challenger is eligible only if, versus breadth4 baseline:

- evaluation trade count rises at least 20%;
- max MTM DD remains <=20%;
- max MTM DD rises no more than 3 percentage points versus baseline;
- PF remains >=1.15 and >=90% of baseline PF;
- AvgR remains >=0.08R and >=65% of baseline AvgR;
- annualized return remains >=8%;
- `SumR - 0.05R * trade_count` remains positive;
- worst full year and worst rolling-12m remain >=-10%.

Among eligible challengers, selection maximizes friction-stressed SumR per unit of drawdown. If none pass, `V51_KEEP_BREADTH4` is the correct result.

## Evidence semantics

This is a preregistered challenger tournament on historical data already seen by the project. It is not fresh out-of-sample evidence. A selected challenger must still receive a short broker-DEMO confirmation before any production-readiness conclusion.

## Operational rule

One exact MT5 historical run, cold-start, same 2021-01-03 -> 2026-08-01 window, same $40 / 1:200 tester setup, one ZIP.
