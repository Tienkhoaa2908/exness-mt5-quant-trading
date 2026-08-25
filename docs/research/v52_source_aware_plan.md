# V52 Source-Aware Higher-Frequency Plan

Date: 2026-08-26

## Objective

Increase trade frequency modestly without reproducing the drawdown/stability failure seen in V51.

V52 is not another average-score sweep. It uses the V51 post-run diagnostic only to preregister source identity as the single new discriminator for the exactly-three-healthy-expert lane.

## Baseline

`v46_hl10_thr0p05_breadth4`

## Challengers

1. `v52_b4_or_b3_trend`
   - breadth >=4: baseline path;
   - breadth ==3: only selected source `TREND20_H1` may enter.

2. `v52_b4_or_b3_bos`
   - breadth >=4: baseline path;
   - breadth ==3: only selected source `BOS_FVG_H1` may enter.

3. `v52_b4_or_b3_trend_bos`
   - breadth >=4: baseline path;
   - breadth ==3: selected source must be `TREND20_H1` or `BOS_FVG_H1`.

No average-health floor is applied to the V52 lane. No risk increase or execution code is introduced.

## Historical protocol

One exact MT5 tester run:
- XAUUSDm M15;
- 2021-01-03 -> 2026-08-01;
- cold start;
- first 6 months warm-up;
- USD40 continuous 1% book;
- leverage 1:200;
- all candidates in the same run;
- one final ZIP.

## Selection guardrails

A challenger is eligible only if:
- trade count >=1.05x breadth4 baseline;
- max MTM DD <=20%;
- DD increase <=3 percentage points;
- PF >=1.20 and >=95% of baseline;
- AvgR >=0.10R and >=75% of baseline;
- annualized return >=10%;
- SumR - 0.05R per trade > 0;
- worst full year >=-10%;
- worst rolling12 >=-10%.

If multiple challengers pass, select the highest friction-stressed SumR per unit DD. If none passes, keep breadth4.

## Interpretation

This is still same-sample challenger research. A selected V52 candidate is not production/live evidence by itself. Because V50 already qualified broker-DEMO order plumbing, a selected V52 candidate needs only a short broker-DEMO signal/execution confirmation rather than another plumbing qualification campaign.
