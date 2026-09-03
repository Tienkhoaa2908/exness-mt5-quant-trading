# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 07:02 (+07)

## User input

Operator ran the V70 fast existing-evidence reanalysis on exact checkpoint:

`a74e48c0bbf4d24801d798f10acbb27671e72dd7`

with:

- `V70_EXIT_HARVEST_EXPECTED_HEAD` pinned to that SHA;
- `V70_REANALYZE_EXISTING=1`;
- no Strategy Tester rerun.

Preflight passed:

- exact branch/head guard;
- Python 3.12 selected;
- all seven V70 static tests passed;
- secret scan PASS with 252 tracked files.

Existing generated-source identity also passed:

`V70_EXISTING_EVIDENCE_SOURCE_IDENTITY=PASS sha256=b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`

The fast path then stopped at:

`holdout_2026_02_long`

with:

`FATAL: RuntimeError: V70 existing evidence lacks exit-shadow lifecycle`

## Classification

This is a fast-path harness-integrity bug, not a strategy, tester, broker, source-identity, or raw-evidence failure.

The accepted V69/V70 development replay is flat from Feb through May 2026. A month with zero trades has no actual owned position lifetime, so it correctly has zero `V70_EXIT_SHADOW_START/END` blocks.

The previous fast-path implementation incorrectly required lifecycle marker strings in every one of the nine monthly directories.

No policy economics were produced by this failed fast reanalysis. The earlier first-run `POLICY_*` values remain invalid and must not be reused.

## Fix implemented

Active branch remains:

`agent/v70-exit-harvest-research`.

The existing-evidence guard now validates each month using the corrected analyzer's actual `analyze_run()` trade/shadow matcher rather than unconditional lifecycle-string presence.

Correct contract:

- zero trades + zero shadow blocks -> valid;
- trade(s) present -> exactly matching completed shadow block(s) required;
- stray shadow in a zero-trade month -> fail;
- missing shadow in a traded month -> fail;
- overlapping/unterminated shadow -> fail;
- entry/shadow timestamp mismatch -> fail;
- aggregate campaign must still contain matched trades.

New runtime markers include one `V70_EXISTING_EVIDENCE_MONTH=PASS month=... matched_trades=...` per month and aggregate `V70_EXISTING_EVIDENCE_LIFECYCLE=PASS`.

Regression coverage now includes a mixed zero-trade + valid-traded campaign and separately proves a traded month without lifecycle fails closed.

No V69 entry rule, actual exit rule, candidate exit policy, LONG-only constraint, SHORT state, or REAL authorization changed.

## GitHub / CI state

The original exact checkpoint `a74e48c0bbf4d24801d798f10acbb27671e72dd7` had all six exact-head workflows completed/success before this incident.

The corrected code/test checkpoint before handover synchronization is `51f9f421a30b0c7e570ff531784509e7387dcba8`; its dedicated V70 job reached Python compile, shell syntax, V70 tests, methodology contract, and secret scan successfully during inspection.

Because documentation synchronization changes the branch HEAD again, resolve the final remote HEAD and require all six checks completed/success before operator rerun.

## Next operator action

1. Do not run Strategy Tester again.
2. Fast-forward to the final exact `agent/v70-exit-harvest-research` HEAD after this sync.
3. Export `V70_EXIT_HARVEST_EXPECTED_HEAD` to that SHA.
4. Keep `V70_REANALYZE_EXISTING=1`.
5. Run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once.
6. Return the per-month evidence markers, aggregate lifecycle marker, legacy/economic baseline, `TRUE_EXCURSION`, four corrected `POLICY_*` lines, both PASS guards, and final V70 PASS.

If this succeeds, make the exit-harvest decision immediately. Do not add another diagnostic layer unless a concrete remaining integrity failure appears.

SHORT remains disabled. REAL money remains unauthorized.
