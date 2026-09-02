# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 06:45 (+07)

## User input

Operator reran the V70 one-pass exit-harvest research after closing MT5/MetaEditor, pinned to exact checkpoint:

`6d4095f1903f15077fdf805fda1f4485f4ffd314`

The run passed Python/static/secret-scan gates, compiled `V70ExitHarvestShadowLong` with `0 errors, 0 warnings`, completed all nine real-tick Strategy Tester months Sep 2025-May 2026, then analyzed the evidence and failed closed at baseline identity.

Generated source SHA256:

`b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`

EX5 SHA256:

`af321cdfe2f91b672443ad57aa7f33606d8e41d5660607cc3f74f6bf3f6a3f5f`

## First analyzer output — INVALID FOR POLICY SELECTION

The analyzer printed 24 trades and economic round-trip net `+$6.44`, then all-zero `TRUE_EXCURSION` and four `POLICY_*` summaries, and finally stopped with:

`FATAL: RuntimeError: V70 baseline net identity mismatch expected=7.14+/-0.05 actual=6.44000000`

Do not use any first-run `POLICY_*` number. In particular, do not promote `EARLY_100_025` from its apparent +$0.15 delta. The numeric shadow event path was parsed incorrectly.

## Source audit

Two harness/analyzer defects were identified.

### A. Event schema mismatch

Actual `V64_EVENTS.csv` numeric fields are `value1`, `value2`, `value3`.

V70 analyzer read `v1`, `v2`, `v3`, and its synthetic regression test used those same invented keys. Therefore all true excursion and shadow trigger numeric values became zero.

This explains the all-zero `TRUE_EXCURSION` and invalidates every policy counterfactual from the first full replay.

### B. Baseline accounting mismatch

`analyze_v69_forward_trade_quality.parse_deals()` calculates full economic round-trip PnL as exit profit + entry explicit costs + exit explicit costs. On the 24-trade V70 replay this was `+$6.44`.

The accepted V68/V69 headline analyzer calculates legacy headline PnL from exit rows only: exit profit + exit-row commission/swap/fee. That convention underlies the accepted V69 `+$7.14` headline.

The difference is an accounting-definition mismatch, not sufficient evidence of strategy drift.

## Patch implemented

Active branch remains:

`agent/v70-exit-harvest-research`

Code checkpoint before this handover synchronization:

`6d8138490b7413aed5b38e273275bd60380460d4`

Changes:

- V70 parses canonical `value1/value2/value3` event fields, with aliases only as fallback;
- tests now use the real event schema;
- analyzer reports `legacy_accepted_identity` and `economic_roundtrip_actual` separately;
- accepted 24/10/14/~+$7.14 identity gate uses legacy accounting only;
- policy deltas use economic round-trip accounting consistently;
- runtime fails closed if excursion/policy telemetry is still all-zero;
- static tests no longer print a misleading accepted-baseline PASS fixture during normal test execution.

No entry semantics, actual exit semantics, LONG-only boundary, SHORT state, or REAL authorization changed.

## CI

The dedicated `v70-exit-harvest-quality` workflow on code checkpoint `6d8138490b7413aed5b38e273275bd60380460d4` completed successfully. No failure was observed in the initial exact-head workflow inspection before handover sync.

Because handover commits change the branch HEAD, resolve the new final remote HEAD and require all six workflows completed/success before operator rerun.

## Decision

The first full Windows replay proved the compile/tester/evidence campaign works, but its policy economics are invalid because of analyzer bugs. This is a harness correction, not a new strategy tuning cycle.

Run the corrected V70 campaign one more time only. Interpret policies only after both markers pass:

- `V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS`
- `V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS`

Then make the exit-harvest decision immediately: promote at most one candidate if economics justify it; otherwise close exit-harvest research and move to entry/re-entry quality.

SHORT remains disabled. REAL money remains unauthorized.
