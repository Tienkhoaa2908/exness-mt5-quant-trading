# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 04:24 (+07)

## User input

Operator successfully ran V69 cycle economics + re-arm recovery at exact checkpoint:

`0ca414f6ea8bfd1e7a3aa842845ec70a1f19e41f`

The run reproduced accepted V69 development identity and ended PASS with MT5 left available, MetaEditor not required, zero orders, zero strategy changes and REAL authorization false.

## Decisive cycle-economics evidence

Accepted identity: `24 trades / 10W / 14L / +$7.14`.

Terminal families across `460` PENDING_ARM cycles:

- `HARD_STRUCTURAL=235` (`51.087%`);
- `TTL_EXPIRY=120`;
- `CONTEXT_QUALITY=80`;
- `SENT_ORDER=24`;
- `UNTERMINATED=1`.

TTL + context = `200` cycles (`43.4783%`).

Archetypes:

- `BREAKOUT_RETEST_BOS`: `241` cycles, `22` trades, `9W/13L`, net `+$4.76`, PF `1.332402`;
- `PULLBACK_SWEEP_BOS`: `219` cycles, only `2` trades, `1W/1L`, net `+$2.38`, PF `3.125`.

Do not promote pullback from a two-trade PF. Breakout-retest is the current economic engine (`22/24` actual V69 trades).

Rearm associations:

- context-quality next cycles: `4` sent, `3W/1L`, `+$6.90`;
- TTL next cycles: `8` sent, `3W/5L`, `+$2.46`;
- hard-structural next cycles: `12` sent, `4W/8L`, `-$2.22`.

These are chronological next-cycle associations only. `same archetype != same setup identity`, and cross-month rearms are not linked. They do not prove that relaxing TTL/context would capture the observed next-cycle PnL.

Trade transitions:

- `L->L=7`, destination net `-$7.67`;
- `L->W=6`, `+$16.11`;
- `W->L=6`, `-$6.65`;
- `W->W=4`, `+$6.47`.

Loss clustering exists but does not authorize a post-win/post-loss throttle without counterfactual evidence.

## Decision

Do **not** loosen entry filters first.

Reasons:

1. hard structural failures are the largest attrition family;
2. prior funnel evidence showed V69 separation retained `49/51` reversal-confirm cycles, so separation is not the dominant bottleneck;
3. positive next-cycle PnL after TTL/context is not same-setup missed-edge proof;
4. pullback economics are sample-starved;
5. the unresolved economic complaint is still profit excursion being given back after entry.

The next gate is therefore **MFE / MAE / realized giveback / inherited V61 profit-ratchet audit on the accepted 24 sent trades**.

## MFE/giveback recovery implementation

Read-only files added on `agent/v69-one-shot-prospective-demo`:

- `scripts/analyze_v69_mfe_giveback_recovery.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_mfe_giveback_recovery.py`;
- extended `.github/workflows/v69_upstream_diag_quality.yml`.

The recovery uses existing accepted V69 development telemetry:

- realized entry/exit PnL from `V64_DEALS.csv`;
- MFE/MAE from `V64_NOISE_SHADOW.csv` `max_pnl/min_pnl`, matched to entry time;
- sent-cycle archetype;
- `PROFIT_LOCK` events inside each trade window.

It reports MFE coverage, winner/loser MFE, loser MAE, giveback, winner capture ratio, positive-MFE realized losses, sub-`$2` round-trip losers, `MFE >= $2` but realized `<$1` split by profit-lock event presence, profit-lock modified/failed counts, threshold diagnostics, month/archetype breakdown and compact per-trade rows.

It intentionally does **not** simulate a trailing-stop counterfactual from MFE peak alone because peak excursion lacks chronological path ordering.

Safety:

- accepted identity must remain `24 / 10 / 14 / +$7.14`;
- read-only;
- no MT5/MetaEditor launch;
- zero order path;
- frozen strategy unchanged;
- SHORT disabled;
- REAL authorization false;
- development-only, not independent edge evidence.

## CI incident and resolution

Code/CI checkpoint `c60f4a05b14f993745433f94f3c15a58221443e9` passed the dedicated `v69-upstream-diag-quality` MFE/giveback tests and safety contract.

The first post-handover exact HEAD `1d5f91b9f09f52c19ae4008079035e15ed9ad43a` then failed `v69-forward-quality` only because `tests/test_v69_frozen_forward_demo_static.py` still asserted the obsolete literal handover phrase `DEMO only`.

The generated frozen-forward source tests before that assertion passed. This was a stale documentation-string contract, not a strategy or runtime failure.

Checkpoint `78c439c67034c1153828a5a96257c91eb4c55ccb` replaced the fragile literal assertion with durable canonical safety checks: frozen research identity, LONG-only, SHORT disabled, DEMO execution context and REAL unauthorized. Frozen V69 source/strategy semantics were not changed.

Resolve the final branch HEAD after this TURN_SYNC commit and require all five exact-head workflows `completed/success` before operator execution.

## Current safety/strategy status

- frozen V69 semantics unchanged;
- DEMO broker execution transport remains proven PASS;
- no execution probe rerun needed;
- live bearish-window abstention remains explained;
- selector global-starvation hypothesis rejected;
- downstream funnel localized;
- cycle economics localized;
- no entry gate loosened;
- SHORT disabled/rejected;
- REAL authorization false.

## Next operator action

After the final exact HEAD is CI-green:

1. leave MT5 running;
2. fast-forward only to that exact branch HEAD;
3. export `V69_MFE_GIVEBACK_EXPECTED_HEAD` to the exact SHA;
4. run `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh` once;
5. return output from `V69_MFE_GIVEBACK_ACCEPTED_DEVELOPMENT_IDENTITY=PASS` through `V69_MFE_GIVEBACK_RECOVERY=PASS`;
6. if `V64_NOISE_SHADOW` coverage is missing/insufficient, stop at the exact FATAL; do not fabricate MFE or rerun accepted strategy evidence blindly.

Interpretation after that run:

- positive-MFE losers whose peak stays `<$2` identify the inherited ratchet's sub-arm harvest gap;
- `MFE >= $2` but realized `<$1` requires direct `PROFIT_LOCK` event audit before any threshold change;
- poor winner MFE capture prioritizes an exit-harvest successor hypothesis;
- if giveback is not dominant, return focus to entry/reentry quality rather than forcing an exit change.
