# V51 Higher-Frequency Challenger — one-shot plan

## Goal

Increase useful trade frequency without throwing away the V46 breadth4 robustness mechanism.

## Baseline

`v46_hl10_thr0p05_breadth4`

## Challengers

Each challenger behaves exactly like breadth4 whenever 4 or 5 experts are healthy. Only when exactly 3 experts are healthy does it permit an extra lane, and only if the average health score of those three experts exceeds a fixed threshold.

- `v51_b4_or_b3_avg0p075`
- `v51_b4_or_b3_avg0p10`
- `v51_b4_or_b3_avg0p15`

## Run protocol

Single exact MT5 tester run:
- XAUUSDm M15;
- 2021-01-03 -> 2026-08-01;
- cold-start state;
- first 6 months warm-up;
- $40 USD;
- leverage 1:200;
- no native/external broker orders;
- no risk increase;
- no same-run threshold retuning.

## Decision rule

The analyzer compares trade frequency, PF, AvgR, SumR, annualized return, max MTM DD, year stability, rolling-12m stability and 0.05R/trade friction stress.

A challenger must raise trade count by at least 20% and satisfy all ADR-051 risk/quality guardrails. If multiple pass, select the highest friction-stressed SumR per unit of DD. If none pass, retain breadth4.

Possible statuses:
- `V51_CHALLENGER_SELECTED`
- `V51_KEEP_BREADTH4`

## Next step

If a challenger is selected, run only a short broker-DEMO confirmation using the execution pipeline already proven by V50. Do not repeat the V50 plumbing probe.
