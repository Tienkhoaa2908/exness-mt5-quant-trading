# Monthly H1 Native V1 workflow

## Objective

Measure the two H1 finalists month by month using native MT5 orders, with the practical USD 40 holding horizon set to one full calendar month.

The 15–20% monthly figure is an aspiration to measure, not a promised outcome and not a parameter-fitting objective.

## Candidates

- `trend_h1_2atr_2r`
- `ema_h1_2atr_2r`

No strategy parameter changes are allowed in this gate.

## Windows

18 full calendar months from 2025-02 through 2026-07. January 2025 and August 2026 are partial coverage and are excluded from canonical monthly statistics.

## Native tester contract

- XAUUSDm / M15
- Model=0 generated Every Tick
- ExecutionMode=0
- Deposit=USD 10,000
- native risk-at-stop=0.50%
- tester leverage=1:200
- dynamic broker-session preflight
- tester-only CTrade
- external broker orders=0

## Capital translation

Each native monthly ledger is replayed at USD 40 under strict-target sizing at 0.50%, 0.75%, and 1.00% stop-risk. No volume round-up.

## Required report

For each month and finalist: start/end capital, USD PnL, return, signals/executed/participation, win rate, PF, MTM DD, USD40 closed-equity DD, costs and rejection counters. Distribution summary reports positive months, >=15% and >=20% hit rates, median/mean/worst/best and median USD profit.

## Reliability

Completed month/candidate artifacts are stored in a persistent LocalAppData checkpoint and reused after interruption. Diagnostic packaging includes the checkpoint.

Risk above 1.00% remains outside the current research phase. LIVE remains forbidden.