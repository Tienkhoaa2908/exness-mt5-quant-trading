# Opportunity Fusion Lab V1 — turnover/churn analysis

Uploaded bundle SHA-256: `1cf1dd45bfe5ee93658f65dec59e72229942a9494f3519a70ace9698b8a7445c`.

Integrity: 22/22 internal SHA-256 entries PASS.

## Main ranking — USD 40 at 1.00% stop-risk research ceiling

The opportunity-fusion hypothesis did **not** improve the robust monthly profile. The standalone EMA H1 peak-lock control remained the strongest median-return candidate.

- `ema_h1_peaklock`: median +6.32%/month; positive 13/18; worst -4.59%; best +14.74%; max MTM DD 9.02%; median trades/month 34.5.
- `fusion_all_h1_peaklock`: median +1.41%/month; positive 10/18; worst -16.16%; max MTM DD 17.41%; median trades/month 65.5.

Adding more signal sources increased trade frequency substantially while reducing median return and worsening drawdown. The bottleneck is therefore not simply “more opportunities”.

## Adjacent winner -> loser / churn evidence

For `ema_h1_peaklock` on the USD 40 @1% book:

- 607 trades across 18 independent monthly resets.
- 589 within-month consecutive-trade pairs.
- 161 winner -> next-trade loser pairs.
- 102 winner -> loser pairs occurred with the next entry within 4 hours of the prior exit.
- 40 winner -> loser pairs occurred within 1 hour.
- all 102 rapid winner -> loser pairs were same-direction re-entries.
- 94 of those 102 rapid winner -> loser pairs followed a `PROTECT_STOP` profitable exit.
- median time from that profitable protected exit to the following losing re-entry was about 83 minutes.

This supports the user's visual observation as a real sequence-level issue, while not implying that every winner is followed by a loss.

For `fusion_all_h1_peaklock`, 1002/1180 (84.9%) consecutive entries occurred within four hours of the prior exit. Its median trade count was 65.5/month versus 34.5/month for EMA control, while median monthly return fell to +1.41% from +6.32%.

## Turnover proxy

Using entry/exit notional (standard-lot-equivalent volume × 100 oz contract × price) divided by the USD 40 starting balance:

- EMA H1 peak-lock median monthly gross notional turnover proxy: about 149.3x initial capital.
- Fusion-all H1: about 293.5x.

This is a turnover-intensity diagnostic, not a fee estimate. The virtual engine already pays the tick Bid/Ask spread path; it does not reproduce all native swap/commission/fee behavior.

## Decision

Do not promote any fusion candidate. Keep EMA H1 peak-lock and Trend H1 peak-lock as controls.

The next experiment targets **re-entry hysteresis and turnover control**:
- post-exit cooldowns;
- post-profit cooldowns;
- same-direction re-arm bands after a profitable exit;
- daily trade caps;
- combined cooldown + re-arm rules.

Risk ceiling remains 1.00%/trade. No leverage escalation. Real-money live trading remains forbidden.