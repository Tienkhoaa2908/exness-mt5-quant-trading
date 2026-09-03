# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 07:20 (+07)

## Authority / safety

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active research branch: `agent/v70-exit-harvest-research`.

Always resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI before acting.

SHORT remains disabled/rejected. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Contract: XAUUSDm M15, LONG only, lot 0.01, planned risk about $0.85-$1.10, emergency guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready, fixed stop, inherited +$2 -> about +$1 profit ratchet.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Gross profit `$22.58`, gross loss `$15.44`. Sep 2025-May 2026 is development-only. Month PnL: Sep -$1.84, Oct +$9.15, Nov +$1.24, Dec -$2.28, Jan +$0.87, Feb-May flat.

## Settled upstream questions

- DEMO execution transport PASS: actual 0.01 XAUUSDm BUY+close returned server `10009 / done` both ways.
- Live no-trade window: 83/83 preserved directional evals were `short_edge` / bearish and rejected by LONG-only isolation. Not broker/order-send failure.
- All-bar selector coverage: 23,526 M15 bars; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.
- Downstream LONG funnel: `460 pending -> 404 micro-arm -> 167 touch -> 95 penetration -> 51 reversal-confirm -> 49 separation -> 24 retest/entry -> 24 deals`. Separation is not the dominant contraction.
- Cycle economics: HARD_STRUCTURAL 235, TTL 120, CONTEXT_QUALITY 80, SENT 24, UNTERMINATED 1. BREAKOUT_RETEST_BOS produced 22/24 trades; PULLBACK_SWEEP_BOS only 2.
- Old `V64_NOISE_SHADOW` MFE/MAE is rejected as actual-trade excursion because it can continue after the real position exits.

## V70 objective

V70 preserves the V69 entry/actual-exit contract and adds observation-only true position-lifetime telemetry plus four exit shadows:

1. `BASELINE_200_100`: +$2 arm / +$1 floor.
2. `EARLY_100_025`: +$1 / +$0.25.
3. `MID_150_050`: +$1.50 / +$0.50.
4. `TIERED_100_025_200_100`: +$1/+0.25 then upgrade to +$1 after +$2.

The shadow code adds no orders and does not call position close/modify.

## V70 Windows evidence

The full nine-month Sep 2025-May 2026 real-tick campaign completed once. Generated source SHA256: `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`; EX5 SHA256: `af321cdfe2f91b672443ad57aa7f33606d8e41d5660607cc3f74f6bf3f6a3f5f`; compile `0 errors, 0 warnings`. Raw evidence is retained.

Post-processing defects already fixed:

- real event fields are `value1/value2/value3`, not `v1/v2/v3`;
- zero-trade months legitimately have zero position-lifetime START/END blocks; integrity is trade/shadow parity per month, not unconditional lifecycle presence.

At checkpoint `f984f259f122f691b31e8aee3ed5bf639b516dfe`, the corrected fast reanalysis proved:

- exact V70 source identity PASS;
- month trade counts: Sep 6, Oct 8, Nov 3, Dec 4, Jan 3, Feb-May 0;
- lifecycle parity PASS with 24 matched trades, 5 traded months, 4 zero-trade months;
- true position-lifetime excursion is nonzero: median MFE all $0.625, winners $2.525, losers $0; 10 trades reached >=$1, 9 reached >=$2, and no realized loser reached >=$2.

However the same run produced V70 actual baseline `24 / 10W / 14L / +$6.44 / PF 1.417098`, not frozen accepted V69 `+$7.14`, and the fail-closed identity gate correctly stopped the run.

## Critical correction — the $0.70 difference is NOT explained by accounting

The earlier handover explanation that `+$6.44` was full round-trip accounting while `+$7.14` was exit-row accounting was wrong.

The exact frozen V69 analyzer at HEAD `0569701...` uses exit rows and computes `profit + commission + swap + fee`. The current V70 `legacy_accepted_summary()` uses the same formula, yet still returns `+$6.44`.

Therefore the remaining `$0.70` is genuine baseline/evidence drift that must be localized before any V70 exit policy can be promoted. Do not change the 7.14 guard or widen tolerance to hide it.

The V69 and V68 builder files themselves are byte-identical between frozen V69 and the current branch, and the Git compare shows the inherited builder chain was not modified after the frozen V69 checkpoint. The remaining candidates are therefore actual replay/deal-value drift or perturbation introduced by the V70 observation hook, not a known strategy-threshold change.

The current V70 policy lines are **provisional and not promotable** until baseline drift is explained. On the contemporaneous 6.44 V70 cohort they were:

- BASELINE: +$6.48, delta +$0.04;
- EARLY: +$7.08, delta +$0.64;
- MID: +$6.44, delta $0.00;
- TIERED: +$7.12, delta +$0.68.

## New focused gate — accepted V69 raw-deal audit

A read-only script now compares the exact hash-pinned accepted V69 ZIP against the already generated V70 `V64_DEALS.csv` files trade-by-trade:

`scripts/audit_v70_baseline_drift_against_accepted_v69.py`

It validates accepted ZIP SHA256 `e35306d...`, then reports per month and per differing exit:

- trade count;
- exit timestamp;
- exit price;
- profit;
- commission/swap/fee;
- exit reason;
- exact PnL delta.

It classifies cohort drift, exit-timing drift, same-time price/profit/cost drift, or mixed drift. It does not launch MT5/MetaEditor/tester and sends no orders.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_RAW_NINE_MONTH_EVIDENCE=RETAINED`
`V70_EVENT_SCHEMA=CORRECTED`
`V70_TRADE_SHADOW_PARITY=PASS_24`
`V70_TRUE_LIFETIME_TELEMETRY=NONZERO`
`V70_BASELINE_CURRENT_NET_USD=6.44`
`V70_ACCEPTED_V69_NET_USD=7.14`
`V70_BASELINE_DRIFT_USD=-0.70`
`V70_ACCOUNTING_EXPLANATION_FOR_DRIFT=REJECTED`
`V70_POLICY_PROMOTION=BLOCKED_PENDING_RAW_DEAL_AUDIT`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Do not rerun Strategy Tester.
2. Run only the accepted-V69-vs-V70 raw-deal audit against the local accepted V69 ZIP.
3. If accepted ZIP is not present locally with exact SHA, stop and report that fact; do not substitute an unverified artifact.
4. If exit timestamps are identical and only exit value/price differs, treat this as contemporaneous tester/feed/fill drift and decide whether policy deltas can be evaluated against the same-run 6.44 baseline.
5. If exit timing differs, inspect/move the V70 observation hook so it cannot precede actual exit management, then a fresh replay may be required because instrumentation perturbed the baseline.
6. Do not promote EARLY or TIERED before this classification.
7. Do not enable SHORT. Do not authorize REAL money.
