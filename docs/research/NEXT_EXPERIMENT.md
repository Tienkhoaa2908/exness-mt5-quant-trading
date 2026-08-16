# NEXT EXPERIMENT — Churn Control Lab V1

## Why

Opportunity Fusion Lab V1 is complete. Adding more signal sources increased turnover and rapid re-entry materially without improving robust monthly return over the standalone EMA H1 + peak-lock control.

On the USD40 / 1.00% EMA control, 607 trades produced 161 winner -> next-trade loser pairs. 102 of those losing re-entries occurred within four hours, all in the same direction; 94/102 followed a profitable `PROTECT_STOP`. Median gap in that subset was about 83 minutes.

The target failure mode is therefore re-entry churn: after a profitable protective exit, the signal condition can remain active and the strategy re-enters too quickly into the same local move, often paying spread/turnover and then taking the next loss.

## Goal

Test bounded re-entry hysteresis and turnover controls without changing the accepted entry logic, profit-protection exit, or stop-risk ceiling.

## Candidate catalog

Two entry families are retained as controls:
- EMA H1 pullback/reclaim;
- Trend H1 breakout.

All candidates use initial stop = 2 ATR, TP = 4R, and after MFE reaches +1R protect 50% of peak R.

Ten churn policies per family:
1. control;
2. cooldown after any exit: 4 M15 bars;
3. cooldown after any exit: 8 M15 bars;
4. cooldown after any exit: 16 M15 bars;
5. cooldown after profitable exit: 8 bars;
6. cooldown after profitable exit: 16 bars;
7. after profitable exit, same-direction re-entry requires a 0.25 ATR adverse reset from the prior exit;
8. same, 0.50 ATR reset;
9. 8-bar profitable-exit cooldown + 0.25 ATR re-arm;
10. maximum two entries per day + 8-bar profitable-exit cooldown.

## Books / monthly evidence

Each candidate runs four independent books:
- normalized USD10k @0.50%;
- USD40 @0.50%;
- USD40 @0.75%;
- USD40 @1.00%.

Three six-month MT5 generated-tick chunks cover 18 independent calendar months, 2025-02 through 2026-07. USD40 min/step is modeled at 0.0001 standard-lot equivalent; margin stress is 1:200; no upward volume rounding.

## Decision metrics

A churn rule is not promoted merely because it trades less. It must improve the joint return / turnover / drawdown profile.

Report:
- median/mean monthly return and USD profit;
- positive-month and >=10/15/20% hit rates;
- PF / AvgR / win rate / MTM DD;
- trades per month;
- gross-notional turnover / initial capital;
- rapid re-entries within four hours;
- post-profit rapid re-entries and subsequent losses;
- cooldown/re-arm/daily-cap rejects;
- volume and margin rejects;
- 2025 vs 2026 stability.

Any virtual finalist must return to native MT5 validation before promotion. Stop-risk above 1.00% is outside this gate.

## Reliability

Run `scripts/run_churn_control_lab_v1.cmd` from V20. The runner uses three starts, 30-second heartbeat, bounded watchdog, broker-unavailable detection, one retry, LocalAppData checkpoint reuse, Common Files recovery and diagnostic ZIP packaging.

REAL-MONEY LIVE TRADING remains forbidden.