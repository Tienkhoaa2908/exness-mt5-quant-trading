# ADR-052 — Source-aware breadth3 opportunity lane

Date: 2026-08-26

## Context

V51 proved that admitting broad exactly-three-healthy-expert opportunities increases trade frequency by roughly 27%-35%, but the average-health filters tested there raised drawdown and weakened rolling-12-month stability enough that all challengers failed the preregistered guardrails.

Post-run diagnostic decomposition showed a stable sign split across all three V51 quality thresholds: incremental TREND20_H1 and BOS_FVG_H1 trades were positive, while incremental EMA_H1, MACD_H1 and SLOW_MOM_16H24H trades were negative.

This is same-sample diagnostic evidence. It is not itself a promotion result and must not be converted into an unrestricted parameter search.

## Decision

Run one small source-aware V52 tournament.

Preserve the frozen breadth4 path when healthy breadth >=4.

When healthy breadth ==3, the extra lane may be admitted only according to one of three preregistered source masks:
1. TREND20_H1 only;
2. BOS_FVG_H1 only;
3. TREND20_H1 or BOS_FVG_H1.

No average-health threshold sweep is performed in V52. The V51 average-quality field is disabled for these candidates so source identity is the sole new discriminator.

## Guardrails

A source-aware challenger may be selected only if, relative to breadth4:
- trade count increases by at least 5%;
- max MTM DD <=20%;
- DD increase <=3 percentage points;
- PF >=1.20 and >=95% of baseline PF;
- AvgR >=0.10R and >=75% of baseline AvgR;
- annualized return >=10%;
- SumR minus 0.05R per trade remains positive;
- worst full year >=-10%;
- worst rolling12 >=-10%.

If more than one challenger passes, select the highest friction-stressed SumR per unit DD. If none passes, keep breadth4.

The lower 5% frequency hurdle is deliberate: V52 is a source-selective refinement, not another broad frequency expansion. A smaller but higher-quality gain is preferable to the unstable 27%-35% gain observed in V51.

## Consequences

V52 remains historical research and does not rerun broker plumbing. V50 execution qualification remains inherited.

A V52 selection requires a short broker-DEMO confirmation before changing the production candidate. No Martingale, grid, doubling-after-loss or risk increase is introduced.
