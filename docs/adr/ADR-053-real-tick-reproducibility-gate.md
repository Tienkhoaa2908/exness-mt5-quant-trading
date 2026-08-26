# ADR-053 — Real-tick reproducibility gate after V52 data contamination

Date: 2026-08-26

## Context

The first V52 source-aware tournament compiled and completed, but its generated-tick historical stream contained three impossible XAUUSDm price excursions around 30,000 while surrounding prices were around 1,900. These excursions generated losses above 10,000R in several control experts, contaminated adaptive health and changed the supposedly invariant breadth4 baseline from 825 to 795 evaluation trades.

The raw `V52_CHALLENGER_SELECTED` output is therefore invalid.

MetaTrader 5 configuration uses `Model=0` for simulated Every Tick and `Model=4` for Every tick based on real ticks. V52R changes only the tester data model; it does not change candidate logic, thresholds, risk, exit rules or the V52 source SHA.

## Decision

Run one V52R reproducibility tournament using the exact V52 source with `Model=4`.

V52R must fail closed on data-integrity anomalies before any candidate can be selected.

Data-integrity requirements over `trades.csv`:
- entry and exit prices finite and positive;
- maximum entry/exit price ratio <= 1.25;
- maximum absolute trade R <= 10R;
- zero rows violating either bound.

The thresholds are integrity sentinels, not alpha tuning. Accepted V51 had maximum price ratio about 1.08 and maximum absolute R below 5R, while contaminated V52 reached about 16x and more than 13,000R.

The analyzer must report the real-tick breadth4 baseline separately from accepted V51. V52R selection is relative to the baseline produced inside the same clean real-tick run. The prior V52 guardrails remain unchanged.

## Outcomes

Possible final statuses:
- `V52R_CHALLENGER_SELECTED` — data integrity passes and one V52 candidate passes all source-aware guardrails;
- `V52R_KEEP_BREADTH4` — data integrity passes but no challenger qualifies;
- `V52R_DATA_INTEGRITY_FAIL` — any pathological trade-price/R observation is found.

A `V52R_DATA_INTEGRITY_FAIL` is not an alpha failure and must not trigger parameter tuning. It requires historical-data repair/diagnosis.

## Consequences

- No V50 execution probe is rerun.
- No V51/V52 threshold is changed.
- No Martingale, grid or risk increase is introduced.
- The V52 source-aware hypothesis remains frozen during V52R.
- Any source-aware selection still requires short broker-DEMO confirmation before becoming the production candidate.
