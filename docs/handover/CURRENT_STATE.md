# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 15:45 (+07)

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

The plain-text raw bundles made `V64_DEALS.csv`, `V64_EVENTS.csv` and `V64_ENTRY_EVAL.csv` readable after ZIP attachment mounting repeatedly failed.

The strongest raw contrast is post-entry follow-through, not loss-dollar geometry:

- EUR average loss `-$1.0725`, GBP average loss `-$1.088125`; normalized loss size is essentially the same.
- EUR average winner `+$2.21`; GBP average winner only `+$0.9933`.
- EUR reached the inherited `PROFIT_LOCK` in 4/8 trades = 50%; GBP only 3/19 = 15.8%.
- EUR produced two full target exits (`reason=5`, about +$3.50) = 25% of all EUR trades; GBP produced zero full target exits in 19 trades.
- GBP therefore loses primarily because far more entries fail to produce sustained favorable excursion; simply widening stops is contradicted by the evidence.

The old <=60-second comparison was too narrow for cross-instrument timing:

- XAU: 10/14 losses <=60 seconds = 71.4%.
- GBP: 0/16 losses <=60 seconds, but 8/16 = 50% of GBP losses still finish within 15 minutes.
- EUR: 0/4 losses <=15 minutes; its four losses last about 17-39 minutes.

So XAU has an ultra-fast failure mode, while GBP has a slower but still severe early-failure mode. EUR is materially cleaner on this timing dimension in the reused V71 sample.

Raw paths show both `BREAKOUT_RETEST_BOS` and `PULLBACK_SWEEP_BOS` can appear around winners and losers. Do not prune or promote an archetype from this small FX sample alone. Session/time filters are also not justified yet; on 2026-01-27 EUR and GBP both lost around 15:22 while AUDUSD won, so a naive time block could remove a valid winner on another pair.

## V72 EURUSD independent validation — prepared, not yet run

Branch: `agent/v72-eurusd-independent-validation`.

Purpose: validate the selected EURUSD candidate on an earlier period that was not used by the V71 EURUSD screen, with **zero retuning** after seeing V71.

Contract:

- symbol `EURUSDm`, M15, real ticks;
- exactly one tester pass;
- period `2024.09.01 -> 2025.09.01`;
- exact V71 source builder and source SHA256 pinned to `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- same V69/V71 LONG entry and exit semantics;
- no entry retune, no exit retune, no SHORT, no REAL.

Preregistered result classification before the tester is run:

- fewer than 8 trades -> `INSUFFICIENT_SAMPLE`;
- otherwise PASS requires all of: net > 0; PF >= 1.25; max realized DD <= $5.00; at least 2 positive months; ex-best-trade net > 0;
- any other adequately sampled result -> `FAIL`.

This gate deliberately prevents one oversized winner from manufacturing a PASS. No threshold may be changed after seeing the untouched-period result.

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
`V72_TESTER_RUNS=1`
`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Run the one-pass V72 EURUSD real-tick validation on `2024.09.01 -> 2025.09.01`.
2. Do not change acceptance thresholds after seeing the result.
3. PASS -> EURUSD earns a stronger validation status and can proceed to a separate prospective DEMO gate.
4. INSUFFICIENT_SAMPLE -> extend evidence only under a predeclared rule; do not call it a pass.
5. FAIL -> reject the unchanged EURUSD portability candidate; do not rescue it by tuning on the failed holdout.
6. Do not enable SHORT. Do not authorize REAL money.
