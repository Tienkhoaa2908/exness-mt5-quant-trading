# V45 Multi-year Single-run Validation Plan

## Policy note

V45 was a historical robustness milestone. Current project-wide policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The V45 tester-only and paper/demo progression rules describe V45 itself. They are not a permanent prohibition on real-money research or future production/live deployment engineering.

## Objective

Test whether the V44 baseline family remains profitable and stable across older market regimes without parameter retuning. V45 uses one exact MT5 Strategy Tester invocation and retains monthly outputs for offline month/year/rolling analysis.

## Frozen candidates

1. `adaptive_ewma_hl10_thr0p05` — primary deployment-validation candidate.
2. `adaptive_ewma_hl8_thr0p05` — annual-return shadow.
3. `adaptive_ewma_hl8_thr0` — accepted control.

No parameter changes are permitted after seeing V45 results.

## Historical protocol

- Symbol: XAUUSDm.
- Timeframe: M15.
- Model: 0, exact MT5 Strategy Tester path used by accepted V38/V44.
- Deposit: $40 USD.
- Leverage: 1:200.
- From: 2022-01-01.
- To: 2026-08-01.
- Exactly one tester invocation.
- Full monthly/trade/manfiest outputs retained.

## State protocol

V44's accepted 2025-08 state must not be injected backward into 2022. V45 starts cold, restores the pre-V45 state after tester exit, and excludes the first six observed months as warm-up.

## Frozen source

Accepted V38 parent source SHA256:
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

Generated V45 source SHA256:
`36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.

V45 changes release/output/validation markers and disables expensive telemetry only. Candidate catalog, signals, entry/exit geometry, sizing and risk are unchanged.

## Evaluation

Analyzer reports monthly returns/trades, calendar years, rolling windows, positive-month ratio, worst periods, max MTM DD, AvgR/SumR/PF, winner concentration and 0.02R/0.05R per-trade friction stress.

Primary HL10 threshold0.05 passes only if the preregistered multiyear gates hold, including sufficient evaluation months, full-year/rolling stability, DD/PF floors and positive stressed SumR.

## Runtime/recovery

`MT5_DONE.json` and `DONE.txt` prevent unnecessary reruns. Packaging failure never justifies rerunning the multi-year tester.

## Historical V45 execution scope

V45 itself is Strategy Tester only, with native/external broker orders disabled and `LIVE_AUTHORIZED=0` as a V45 evidence marker.

A V45 pass advanced the historical workflow toward paper/demo deployment validation. Current production/live research and deployment intent is governed by ADR-049 and later V49 readiness evidence.
