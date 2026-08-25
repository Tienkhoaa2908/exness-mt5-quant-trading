# V50 fast DEMO execution qualification

## Objective

Qualify native MT5/Exness DEMO order plumbing quickly without relaxing or re-optimizing the frozen breadth4 strategy.

## Integrated test

V50 runs the frozen V49/breadth4 logic and a separate min-volume execution probe in the same EA. The probe never overlaps a strategy broker or pending position.

Target: three broker-confirmed probe round trips. Default timing is 45 seconds open plus at least 60 seconds between probe actions. Under normal market conditions this should exercise the broker lifecycle in minutes rather than days.

## Evidence collected

- probe OPEN/CLOSE requests;
- requested and result price;
- required margin;
- CTrade retcodes;
- broker order/deal IDs;
- `OnTradeTransaction` deal evidence;
- probe round trips and rejects;
- concurrent breadth4 health count and breadth4 round-trip count;
- push events for probe OPEN/CLOSE/HALT/FINAL;
- final status and one SHA-manifested ZIP.

## Final classification

- `EXECUTION_PIPELINE_PASS`: three clean DEMO probe round trips, no duplicate probe position, acceptable reject ratio;
- `HOLD`: execution, permission, reconciliation or margin guard failure;
- `EXECUTION_PROBE_INCOMPLETE`: four-hour probe timeout without a clean sample.

This classification is intentionally separate from alpha-frequency research.
