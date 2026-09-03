# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 16:48 (+07)

## Authority / safety

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active research branch: `agent/v72-eurusd-independent-validation`.

Always resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI before acting.

SHORT disabled. SHORT remains rejected for activation. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Frozen contract: XAUUSDm M15, LONG only, lot 0.01, planned risk about $0.85-$1.10, emergency guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready, fixed stop, inherited +$2 -> about +$1 profit ratchet.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Sep 2025-May 2026 is development-only. Actual DEMO execution transport is proven PASS.

## Settled research before V71

- XAU live no-trade window was bearish `short_edge`; LONG-only isolation was working, not broker failure.
- All-bar coverage rejected global LONG starvation.
- Downstream LONG funnel localized dominant attrition upstream of final separation; hard structural failure was the largest terminal family.
- V70 true-position telemetry replaced invalid post-exit `V64_NOISE_SHADOW` MFE attribution.
- V70 same-run baseline +$6.44 versus accepted V69 +$7.14 was one -$0.70 swap drift with identical exit time/price/gross profit/reason.
- V70 TIERED exit shadow improved reused development economics by only +$0.68 and was not promoted.

## V71 FX direct-portability campaign — completed

V71 kept frozen V69 LONG decision/entry/real-exit semantics exactly after metadata normalization. No symbol-specific retune was applied.

Campaign: XAUUSDm control plus EURUSDm, GBPUSDm, USDJPYm and AUDUSDm; M15 real ticks; `2025.09.01 -> 2026.06.01`; lot 0.01; risk $0.85-$1.10; emergency $1.20; target $3.50; separation $1.30; no SHORT; no REAL.

Tester evidence HEAD: `82994371d4717ed947a0d9e8057617bf96ea8c8b`.
Generated source SHA256: `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`.
EX5 SHA256: `69896c6b330c6dd4bbb13acf7ee27ea1efccbe7f7cc47b64f582ea02db0c20b5`.
Compile 0/0. `V71_V69_LONG_STRATEGY_EQUIVALENT=1`.

Same-run results:

- XAUUSDm: 24 trades, 10W/14L, +$6.44, PF 1.417098, DD $3.65.
- EURUSDm: 8 trades, 4W/4L, +$4.55, PF 2.060606, DD $3.30.
- AUDUSDm: 7 trades, 3W/4L, +$1.29, PF 1.305687, DD $2.10.
- USDJPYm: 6 trades, 2W/4L, +$0.21, PF 1.049065, DD $3.28.
- GBPUSDm: 19 trades, 3W/16L, -$14.43, PF 0.171166, DD $16.32.

## V71 raw EUR/GBP/XAU review — completed

The strongest raw contrast is post-entry follow-through, not loss-dollar geometry:

- EUR average loss `-$1.0725`, GBP average loss `-$1.088125`;
- EUR average winner `+$2.21`, GBP average winner `+$0.9933`;
- EUR reached inherited `PROFIT_LOCK` in 4/8 trades and produced two full target exits;
- GBP reached `PROFIT_LOCK` only 3/19 times and produced zero full target exits.

The <=60-second statistic was too narrow across instruments. GBP had 0/16 losses <=60 seconds but 8/16 <=15 minutes; EUR had 0/4 losses <=15 minutes; XAU remained the ultra-fast case at 10/14 <=60 seconds.

Both `BREAKOUT_RETEST_BOS` and `PULLBACK_SWEEP_BOS` occur around winners and losers. No archetype pruning or naive time-of-day filter is justified from the small FX sample.

## V72 EURUSD untouched temporal validation — completed FAIL

Branch: `agent/v72-eurusd-independent-validation`.

Preregistered contract was fixed before the result:

- `EURUSDm`, M15, real ticks;
- period `2024.09.01 -> 2025.09.01`;
- exact V71 source SHA256 `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- same V69/V71 LONG entry and exit semantics;
- no entry retune, no exit retune, no SHORT, no REAL;
- <8 trades -> `INSUFFICIENT_SAMPLE`;
- otherwise PASS required net >0, PF >=1.25, max realized DD <=$5.00, >=2 positive months and ex-best-trade net >0.

The corrected collector first rejected mixed/stale evidence in the shared V71 telemetry root, archived it, then performed one fresh real-tick tester pass. Evidence collection and analysis completed successfully.

V72 untouched-period result:

- 23 trades, 8 wins / 15 losses;
- net `+$4.11`;
- gross profit `$20.52`, gross loss `$16.41`;
- PF `1.250457`;
- max realized DD `$10.23`;
- best trade `+$3.51`;
- ex-best-trade net `+$0.60`;
- 2 positive months, 7 negative months;
- 5/15 losses <=15 minutes = 33.33%;
- 8 `PROFIT_LOCK` events;
- 4,436 entry-eval rows.

Monthly realized PnL with trades:

- 2024-09 `-$1.11`;
- 2024-11 `-$1.10`;
- 2025-01 `-$1.21`;
- 2025-02 `-$1.08`;
- 2025-03 `-$3.42`;
- 2025-04 `-$2.31`;
- 2025-05 `+$7.02`;
- 2025-06 `+$9.42`;
- 2025-08 `-$2.10`.

Classification is `FAIL`. All preregistered gates except drawdown passed; DD `$10.23` exceeded the fixed `$5.00` ceiling. The result also shows strong regime/month concentration: the two positive months contributed `$16.44` while seven negative months totaled `-$12.33`.

Interpretation:

- unchanged EURUSD portability remains mildly profitable across this earlier period, so V71 was not a pure one-trade illusion;
- however the risk path is not acceptable for the $40-account research objective at fixed 0.01 lot, because the untouched DD is about 25.6% of starting capital and more than twice the preregistered ceiling;
- the V71 EURUSD screen therefore does **not** earn promotion to prospective DEMO under the unchanged V69/V71 contract;
- do not retune EURUSD on this failed holdout to rescue the candidate.

The prior telemetry-root mismatch is resolved and no longer blocks V72 evidence interpretation.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_EXIT_POLICY_DECISION=NO_PROMOTION`
`V71_RESEARCH=FX_PORTABILITY_DIRECT_NO_RETUNE`
`V71_TESTER_CAMPAIGN=PASS_5_SYMBOLS`
`V71_EURUSD_SCREEN=BEST_FX_CANDIDATE_SMALL_SAMPLE`
`V71_GBPUSD_DIRECT_PORTABILITY=REJECTED`
`V71_RAW_CONTRAST=GBP_POST_ENTRY_FOLLOW_THROUGH_FAILURE`
`V72_RESEARCH=EURUSD_UNTOUCHED_TEMPORAL_VALIDATION`
`V72_TESTER_EVIDENCE=PASS`
`V72_ECONOMIC_CLASSIFICATION=FAIL`
`V72_FAILURE_GATE=MAX_REALIZED_DD`
`V72_EURUSD_UNCHANGED_CANDIDATE=REJECTED_FOR_PROMOTION`
`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Do not tune EURUSD thresholds on the failed V72 untouched period and do not promote unchanged EURUSD to prospective DEMO.
2. If continuing FX research, the clean next candidate is AUDUSD because it ranked second in the preregistered V71 no-retune screen (+$1.29, PF 1.305687, DD $2.10), but its V71 sample was only 7 trades.
3. Any AUDUSD successor should use the same exact V71/V69 LONG source with zero retuning and a preregistered earlier-period validation gate before the result is visible.
4. USDJPY remains near-flat screening evidence and GBPUSD remains rejected; do not pool FX pairs to manufacture a positive aggregate.
5. Do not enable SHORT. Do not authorize REAL money.
