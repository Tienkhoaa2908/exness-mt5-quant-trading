# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 16:48 (+07)

## User input

User ran the corrected V72 EURUSD untouched validation launcher and supplied the full terminal output. The run completed evidence collection and analysis successfully and produced a preregistered economic classification of `FAIL`.

## State read before work

Fresh-resolved pre-turn remote HEAD on `agent/v72-eurusd-independent-validation`:

`d2fcb065a3a217953a44d0824210f9aca7be6f2c`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent branch commits and exact-head CI. Pre-turn exact-head CI had 8 checks, all completed success.

## Operator evidence inspected

Harness recovery behavior:

- static tests PASS count=6;
- secret scan PASS;
- source SHA remained exactly `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- MetaEditor compile `0 errors, 0 warnings`;
- the collector correctly rejected the shared V71 telemetry root because it contained mixed timestamps through 2026-05-31;
- stale/mixed root was archived;
- a fresh exact V72 real-tick pass was run on `EURUSDm`, M15, `2024.09.01 -> 2025.09.01`;
- MT5 returned `rc=0`;
- evidence copy PASS;
- analyzer PASS;
- launcher PASS.

The prior telemetry-root mismatch is therefore resolved and no longer blocks interpretation.

## V72 untouched economic result

Preregistered classification: `FAIL`.

Metrics:

- trades: 23;
- wins/losses: 8 / 15;
- net: `+$4.11`;
- gross profit/loss: `$20.52 / $16.41`;
- PF: `1.250457`;
- max realized DD: `$10.23`;
- best trade: `+$3.51`;
- ex-best-trade net: `+$0.60`;
- positive months: 2;
- negative months: 7;
- losses <=15 minutes: 5/15 = 33.33%;
- profit locks: 8;
- entry-eval rows: 4,436.

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

## Gate interpretation

The preregistered requirements were:

- >=8 trades;
- net >0;
- PF >=1.25;
- max realized DD <=$5.00;
- >=2 positive months;
- ex-best-trade net >0.

V72 passed every requirement except drawdown. `$10.23` DD is more than double the fixed ceiling and about 25.6% of the $40 research account.

The result is therefore a genuine strategy/risk-path rejection of the unchanged EURUSD candidate, not a harness failure. No threshold will be changed after seeing this holdout.

The monthly path is also regime-concentrated: May+June contribute `+$16.44`, while seven negative months total `-$12.33`.

## Decision

- do not promote unchanged EURUSD to prospective DEMO;
- do not retune EURUSD on the consumed V72 holdout;
- preserve V71 EURUSD as a promising screen that failed independent risk validation;
- if FX research continues, AUDUSD is the next clean candidate because it ranked second in the original V71 no-retune screen, but any successor must use zero retuning and a preregistered earlier-period validation gate;
- USDJPY remains near-flat screening evidence;
- GBPUSD remains rejected;
- do not pool FX pairs to manufacture aggregate profitability.

## Safety

`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`V72_SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next action

No additional V72 rerun is required. If continuing Forex validation, create a separate AUDUSD successor lineage from the exact V71/V69 LONG source, preregister the earlier-period gate before the tester result is visible, and keep SHORT/REAL disabled.
