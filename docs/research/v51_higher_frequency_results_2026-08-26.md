# V51 Higher-Frequency Challenger Results

Date: 2026-08-26

## Accepted bundle

Uploaded ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Integrity:
- ZIP CRC PASS;
- internal SHA256 manifest 17/17 PASS;
- run HEAD `8c211b27e6676f3176e089a619679e6af263e3fd`;
- branch `agent/v51-higher-frequency-challenger`;
- V46 canonical parent SHA256 `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- generated V51 source SHA256 `927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6`;
- MetaEditor compile `Result: 0 errors, 0 warnings`;
- exact run id `v51_higher_frequency_challenger_v1__XAUUSDm__PERIOD_M15__2021-01-03_00-00-00__812031`.

Protocol: one exact MT5 historical run, XAUUSDm M15, 2021-01-03 -> 2026-08-01, cold start, six warm-up months, USD40 continuous 1% risk book, leverage 1:200.

## Formal result

`STATUS=V51_KEEP_BREADTH4`

Selected candidate:
`v46_hl10_thr0p05_breadth4`

No V51 challenger passed the preregistered drawdown/stability guardrails.

## Candidate comparison

| Candidate | Trades | Gain vs breadth4 | AvgR | PF | Annualized | Max MTM DD | Stress SumR (-0.05R/trade) | Worst full year | Worst rolling12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breadth4 baseline | 825 | 0.0% | 0.1443R | 1.2817 | 21.34% | 16.60% | +77.81R | -0.81% | -1.95% |
| b4-or-b3 avg >=0.075 | 1110 | +34.55% | 0.1057R | 1.2026 | 19.08% | 28.62% | +61.87R | -9.38% | -13.39% |
| b4-or-b3 avg >=0.10 | 1101 | +33.45% | 0.1114R | 1.2140 | 22.21% | 25.04% | +67.61R | -9.63% | -11.09% |
| b4-or-b3 avg >=0.15 | 1050 | +27.27% | 0.1101R | 1.2118 | 18.82% | 28.56% | +63.14R | -10.52% | -14.39% |

All three challengers increased frequency materially, but each raised max MTM drawdown beyond 20% and beyond the allowed +3 percentage-point increase over breadth4. All also breached the -10% worst rolling-12-month guardrail; the 0.15 candidate additionally breached the -10% worst-full-year guardrail.

## Diagnostic finding

The average-health threshold is not the right discriminator for the extra breadth3 lane.

Post-run diagnostic decomposition of the incremental trades in the best numerical challenger (`v51_b4_or_b3_avg0p10`) shows:
- `TREND20_H1`: 76 incremental trades, AvgR about +0.149R, SumR about +11.36R;
- `BOS_FVG_H1`: 16 incremental trades, AvgR about +0.331R, SumR about +5.30R;
- `EMA_H1`: 114 incremental trades, AvgR about -0.085R, SumR about -9.67R;
- `MACD_H1`: 25 incremental trades, AvgR about -0.194R, SumR about -4.84R;
- `SLOW_MOM_16H24H`: 72 incremental trades, AvgR about -0.073R, SumR about -5.26R.

The same sign pattern is stable across the 0.075 / 0.10 / 0.15 V51 quality thresholds: TREND20_H1 and BOS_FVG_H1 are positive; EMA_H1, MACD_H1 and SLOW_MOM_16H24H are negative on the incremental lane.

This diagnostic is same-sample evidence and is not itself a promotable result. It is sufficient to motivate one preregistered source-aware challenger experiment rather than another threshold sweep.

## Decision

- Keep breadth4 as the current baseline.
- Do not promote any V51 average-health challenger.
- Do not rerun V50 execution plumbing.
- Next research should test a source-aware exactly-three-healthy-expert lane that admits only the historically positive incremental sources (TREND20_H1 / BOS_FVG_H1), while preserving the breadth>=4 path.
- Avoid broad parameter sweeps; use one small preregistered V52 tournament and accept `KEEP_BREADTH4` if source-aware variants still fail risk/stability controls.
