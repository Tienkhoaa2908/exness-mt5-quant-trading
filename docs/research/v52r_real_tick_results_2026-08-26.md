# V52R Real-Tick Reproducibility Results

Date: 2026-08-26

## Accepted bundle

Uploaded ZIP SHA256:
`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Integrity:
- ZIP CRC PASS;
- internal SHA256 manifest 20/20 PASS;
- run HEAD `718eb8c11dc801108695c73a58c692f55a108772`;
- branch `agent/v52r-real-tick-repro`;
- exact V52 source SHA256 `676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09`;
- MetaEditor compile `Result: 0 errors, 0 warnings`;
- tester model `4` (`Every tick based on real ticks`);
- cold start, six warm-up months, XAUUSDm M15, 2021-01-03 -> 2026-08-01, USD40 1% continuous book.

## Data integrity

`data_integrity_pass=1`

- rows checked: 263,052;
- anomaly rows: 0;
- max entry/exit price ratio: 1.079739;
- max absolute R: 4.98223R;
- configured limits: price ratio <=1.25, absolute R <=10R.

The generated-tick contamination seen in the invalid V52 run is absent.

## Reproducibility check

Breadth4 accepted V51 reference: 825 evaluation trades.

V52R real-tick breadth4: 819 evaluation trades (`-6`, about `-0.73%`). Risk/return statistics remain very close to V51:
- AvgR +0.1480R;
- PF 1.2894;
- annualized +21.47%;
- max MTM DD 16.60%;
- worst rolling12 -1.95%.

This supports that the V52R run is a clean and materially reproducible baseline, unlike the contaminated generated-tick V52 run.

## Formal result

`STATUS=V52R_CHALLENGER_SELECTED`

Selected candidate:
`v52_b4_or_b3_trend_bos`

Candidate comparison on the clean real-tick run:

| Candidate | Trades | Gain | AvgR | PF | Annualized | Max MTM DD | Stress SumR (-0.05R/trade) | Worst full year | Worst rolling12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breadth4 baseline | 819 | 0.0% | 0.1480R | 1.2894 | 21.47% | 16.60% | +80.28R | -0.81% | -1.95% |
| b4-or-b3 TREND | 932 | +13.80% | 0.1319R | 1.2587 | 21.47% | 16.96% | +76.30R | -1.17% | -2.20% |
| b4-or-b3 BOS | 851 | +3.91% | 0.1528R | 1.3012 | 23.11% | 14.97% | +87.44R | -0.11% | -3.16% |
| b4-or-b3 TREND+BOS | 951 | +16.12% | 0.1344R | 1.2649 | 22.17% | 16.10% | +80.30R | -3.09% | -4.68% |

`TREND+BOS` passes all preregistered ADR-052 challenger guardrails and is selected by the frozen utility rule. `TREND` also passes but has lower friction-stressed utility per DD. `BOS` has the strongest quality/risk statistics but misses the preregistered >=5% frequency-gain hurdle.

## Interpretation

The selected candidate solves the specific frequency bottleneck more cleanly than the V51 broad breadth3 expansion:
- +16.1% evaluation trade count;
- slightly lower max DD than breadth4 (16.10% vs 16.60%);
- PF remains >1.26;
- annualized return improves modestly to 22.17%;
- rolling12 tail weakens versus breadth4 but remains inside the preregistered -10% guardrail.

The economic edge is not large after friction stress: TREND+BOS stress SumR is almost equal to breadth4 (+80.30R vs +80.28R). Therefore the promotion claim is specifically **higher frequency without giving back DD**, not a large friction-adjusted return improvement.

## Decision

- Accept V52R real-tick evidence.
- Promote `v52_b4_or_b3_trend_bos` as the research candidate for short broker-DEMO confirmation.
- Do not promote the invalid generated-tick V52 run.
- Do not rerun V50 plumbing probes; execution plumbing remains inherited PASS.
- Do not retune thresholds after V52R.
- A short DEMO confirmation should verify that the new candidate's natural virtual intent can be mapped through the already-qualified broker execution adapter, while preserving fail-closed DEMO-only guards.

This remains same-sample historical selection plus reproducibility evidence; it is not by itself production authorization.