# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 05:44 (+07)

## User input

Operator ran the pinned V70 one-pass exit-harvest research launcher from exact checkpoint:

`61fb41aace6bd7a7fd8954778cffa4f97081f7ce`

The launcher selected Python 3.12, passed compile/static/secret-scan preflight, resolved the MT5 data/common/expert directories, then stopped before MetaEditor compile or Strategy Tester launch because `terminal64.exe` was still running.

Exact terminal error:

`FATAL: RuntimeError: MetaTrader 5 must be closed for the one-pass V70 tester replay`

## Classification

This is an expected harness safety guard, not a strategy, broker, compiler, or tester failure.

No V70 replay month started. No candidate policy result exists yet. No V69/V70 strategy order was added by this failed attempt. SHORT remains disabled. REAL authorization remains false.

The static baseline-identity regression itself passed and printed:

`V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS trades=24 wins=10 losses=14 net_usd=7.14000000`

That line came from the static regression fixture, not from the nine-month Windows Strategy Tester replay, so it must not be mistaken for completed V70 replay evidence.

## GitHub state inspected

Active branch:

`agent/v70-exit-harvest-research`

Remote HEAD before this synchronization:

`61fb41aace6bd7a7fd8954778cffa4f97081f7ce`

All six exact-head workflows on that checkpoint were completed/success, including full `quality` and `v70-exit-harvest-quality`.

No source/runtime change is required for this incident. The process guard behaved as designed.

## Next operator action

1. Close MetaTrader 5 completely and also close MetaEditor if it is open.
2. Keep the repository on `agent/v70-exit-harvest-research`; there is no need to repeat the earlier diagnostic chain.
3. Fast-forward to the current exact branch HEAD after this handover-sync commit and export `V70_EXIT_HARVEST_EXPECTED_HEAD` to that SHA.
4. Run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once.
5. The decisive evidence is the final `V70_EXIT_HARVEST_SHADOW`, `TRUE_EXCURSION`, four `POLICY_*` summaries, and `V70_EXIT_HARVEST_RESEARCH=PASS`.

Do not enable SHORT. Do not authorize REAL money.
