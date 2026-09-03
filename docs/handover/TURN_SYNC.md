# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 15:45 (+07)

## User input

User uploaded plain-text V71 raw review bundles for EURUSDm, GBPUSDm and XAUUSDm after repeated ZIP mount failures. No separate typed request was supplied; continue the previously requested deep raw-evidence review and next research action.

## State read before work

Fresh-resolved pre-turn remote HEAD on `agent/v71-fx-portability-research`:

`1933b73c08f082ddc227f9d7a5e437be6b1fdc92`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI. Pre-turn exact-head CI was 7/7 completed success.

## Raw evidence reviewed

Plain-text `V64_DEALS.csv`, `V64_EVENTS.csv` and `V64_ENTRY_EVAL.csv` are readable for EURUSDm, GBPUSDm and XAUUSDm.

Confirmed aggregate identity remains:

- EURUSDm: 8 trades, 4W/4L, +$4.55, PF 2.060606, DD $3.30.
- GBPUSDm: 19 trades, 3W/16L, -$14.43, PF 0.171166, DD $16.32.
- XAUUSDm: 24 trades, 10W/14L, +$6.44 contemporaneous, PF 1.417098, DD $3.65.

Raw contrast:

- normalized losing-trade size is nearly identical: EUR average loss -$1.0725 versus GBP -$1.088125;
- EUR average winner +$2.21 versus GBP +$0.9933;
- EUR has 4 PROFIT_LOCK events / 8 trades and two full target exits (`reason=5`); GBP has 3 PROFIT_LOCK events / 19 trades and zero full target exits;
- therefore GBP's observed failure is weak post-entry favorable follow-through, not an obviously too-tight dollar stop;
- the prior <=60-second metric was too narrow across instruments: GBP has 0/16 losses <=60 seconds but 8/16 = 50% <=15 minutes; EUR has 0/4 <=15 minutes; XAU remains the ultra-fast case at 10/14 <=60 seconds;
- both BREAKOUT_RETEST_BOS and PULLBACK_SWEEP_BOS occur around winners and losers, so the small raw sample does not justify archetype pruning;
- naive time-of-day exclusion is also not justified: around 2026-01-27 15:22 both EUR and GBP lost while AUDUSD won under the same no-retune strategy family.

## Action taken

Created successor branch:

`agent/v72-eurusd-independent-validation`

V72 does not retune EURUSD. It validates the exact V71/V69 LONG candidate on an earlier temporal period not used in the V71 EURUSD screen.

Prepared tooling:

- `scripts/analyze_v72_eurusd_validation.py`;
- `runtime/v72_eurusd_independent_validation/RUN_V72_EURUSD_INDEPENDENT_VALIDATION.py`;
- `runtime/v72_eurusd_independent_validation/RUN_V72_EURUSD_INDEPENDENT_VALIDATION_GIT_BASH.sh`;
- `tests/test_v72_eurusd_independent_validation.py`;
- `.github/workflows/v72_eurusd_independent_validation_quality.yml`.

V72 contract:

- EURUSDm M15 real ticks;
- one tester pass only;
- `2024.09.01 -> 2025.09.01`;
- exact V71 builder output pinned to source SHA256 `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- entry retune 0; exit retune 0; SHORT 0; REAL 0.

Preregistered classification before the tester result is visible:

- <8 trades -> `INSUFFICIENT_SAMPLE`;
- otherwise PASS requires net >0, PF >=1.25, max realized DD <=$5.00, >=2 positive months and ex-best-trade net >0;
- otherwise `FAIL`.

Initial V72 CI correctly caught a synthetic fixture error in the test itself; only the fixture was corrected. The acceptance logic was not changed. The V72-specific check on the corrected commit passed.

## Safety

`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`V72_SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next operator action

After final exact-head CI is fully green, run the single V72 EURUSD tester validation. Do not alter the preregistered thresholds after seeing the result. No GBP retune, no SHORT activation and no REAL authorization.
