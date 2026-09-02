# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 04:21 (+07)

## User input

Operator successfully ran the read-only V69 cycle economics + re-arm recovery at exact checkpoint:

`0ca414f6ea8bfd1e7a3aa842845ec70a1f19e41f`

The runtime reproduced accepted V69 development identity and completed with:

- `V69_CYCLE_ECONOMICS_RECOVERY=PASS`;
- `V69_CYCLE_ECONOMICS_LAUNCHER=PASS`;
- MT5 remained available to keep running;
- MetaEditor not required;
- orders sent `0`;
- strategy changed `0`;
- REAL authorization `0`.

## Exact operator evidence

Accepted identity:

`24 trades / 10W / 14L / +$7.14` — PASS.

Terminal families across `460` PENDING_ARM cycles:

- `HARD_STRUCTURAL=235` (`51.087%`);
- `TTL_EXPIRY=120`;
- `CONTEXT_QUALITY=80`;
- `SENT_ORDER=24`;
- `UNTERMINATED=1`.

TTL + context = `200` cycles (`43.4783%`).

### Archetype economics

`BREAKOUT_RETEST_BOS`:

- `241` cycles;
- `22` sent (`9.1286%` conversion);
- `9W / 13L`;
- gross profit `$19.08`;
- gross loss `$14.32`;
- net `+$4.76`;
- PF `1.332402`.

`PULLBACK_SWEEP_BOS`:

- `219` cycles;
- `2` sent (`0.9132%` conversion);
- `1W / 1L`;
- gross profit `$3.50`;
- gross loss `$1.12`;
- net `+$2.38`;
- PF `3.125`.

Do not promote pullback from the headline PF; the sent sample is only two trades. Breakout-retest generated `22/24` actual V69 trades and is the relevant economic engine.

### Rearm associations

Context-quality rejects:

- eligible `80`;
- next cycle exists `80`;
- next cycle sent `4`;
- `3W / 1L`;
- next-cycle net `+$6.90`.

TTL rejects:

- eligible `120`;
- next cycle exists `119`;
- next cycle sent `8`;
- `3W / 5L`;
- next-cycle net `+$2.46`.

Hard-structural rejects:

- eligible `235`;
- next cycle exists `228`;
- next cycle sent `12`;
- `4W / 8L`;
- next-cycle net `-$2.22`.

The diagnostic explicitly states `same_archetype_is_not_setup_identity=true` and does not link cross-month rearms. These are next-cycle associations, not proof that relaxing the rejected gate would have captured that PnL.

### Trade transitions

- `L->L=7`, destination net `-$7.67`;
- `L->W=6`, destination net `+$16.11`;
- `W->L=6`, destination net `-$6.65`;
- `W->W=4`, destination net `+$6.47`.

Loss clustering is present, but no post-win/post-loss throttle is authorized from these counts alone.

### Monthly cycle economics

- Sep 2025: `82` cycles, `6` trades, `1W/5L`, `-$1.84`, PF `0.664234`;
- Oct: `91` cycles, `8` trades, `5W/3L`, `+$9.15`, PF `3.747748`;
- Nov: `41` cycles, `3` trades, `1W/2L`, `+$1.24`;
- Dec: `79` cycles, `4` trades, `1W/3L`, `-$2.28`, PF `0.302752`;
- Jan 2026: `89` cycles, `3` trades, `2W/1L`, `+$0.87`;
- Feb: `35` cycles, `0` trades;
- Mar: `8` cycles, `0` trades;
- Apr: `26` cycles, `0` trades;
- May: `9` cycles, `0` trades.

## Decisive interpretation

Do **not** loosen entry filters first.

Reasons:

1. `235/460` cycles are hard structural failures, the largest family.
2. Separation is not the dominant bottleneck; prior funnel evidence showed `51 reversal-confirm -> 49 separation`.
3. Positive next-cycle PnL after TTL/context rejects is not same-setup counterfactual evidence.
4. Pullback's PF is sample-starved at only two trades.
5. The user's earlier observed problem — trades showing profit then giving it back — remains economically unresolved and can now be measured directly on the 24 actual sent trades.

Next priority: **MFE/MAE/giveback and inherited V61 profit-ratchet audit**.

## Code work this turn

A read-only MFE/giveback recovery was added on the current branch.

Code/CI checkpoint before handover docs:

`c60f4a05b14f993745433f94f3c15a58221443e9`

Files:

- `scripts/analyze_v69_mfe_giveback_recovery.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_mfe_giveback_recovery.py`;
- extended `.github/workflows/v69_upstream_diag_quality.yml`.

The recovery reuses the existing trade-quality instrumentation:

- `V64_DEALS.csv` for realized entry/exit PnL;
- `V64_NOISE_SHADOW.csv` `max_pnl/min_pnl` for MFE/MAE matched to entry time;
- sent-cycle archetype from existing cycle telemetry;
- `PROFIT_LOCK` events within each trade window.

It reports:

- MFE-match coverage;
- median MFE winners/losers and loser MAE;
- median giveback and winner capture ratio;
- positive-MFE realized losses;
- sub-`$2` peak round-trip losses where the V61 ratchet could not arm;
- `MFE >= $2` but realized `<$1`, split by presence/absence of profit-lock events;
- profit-lock modified/failed trade counts;
- threshold-reach diagnostics `$0.5` through `$3.5`;
- by-month, by-archetype and compact per-trade rows.

Safety/methodology:

- exact branch/HEAD contract;
- clean worktree required;
- accepted development identity must remain `24 / 10 / 14 / +$7.14`;
- no MT5/MetaEditor launch;
- zero order path;
- frozen strategy unchanged;
- SHORT disabled;
- REAL authorization false;
- development-only, not independent edge evidence;
- trailing-stop counterfactual deliberately **not** simulated from peak MFE alone because chronological path is missing.

## CI

At checkpoint `c60f4a05b14f993745433f94f3c15a58221443e9`, the dedicated `v69-upstream-diag-quality` workflow passed the new MFE/giveback tests and read-only safety contract. Other exact-head workflows were still completing when handover synchronization began; resolve the final post-doc HEAD and require all five workflows `completed/success` before operator execution.

## Safety and strategy status

- frozen V69 semantics unchanged;
- DEMO broker execution transport remains proven PASS;
- no need to rerun the forced execution probe;
- live bearish-window abstention remains explained;
- selector global-starvation hypothesis remains rejected;
- downstream funnel localized;
- cycle economics localized;
- no entry gate has been loosened;
- SHORT remains disabled/rejected;
- REAL authorization false.

## Next operator action

After final handover HEAD is exact-CI-green:

1. leave MT5 running;
2. fast-forward only to the exact final branch HEAD;
3. export `V69_MFE_GIVEBACK_EXPECTED_HEAD` to that SHA;
4. run `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh` once;
5. return output from `V69_MFE_GIVEBACK_ACCEPTED_DEVELOPMENT_IDENTITY=PASS` through `V69_MFE_GIVEBACK_RECOVERY=PASS`, especially noise-match coverage, MFE/MAE, giveback, ratchet audit, threshold diagnostics, archetype/month breakdown and compact trade rows;
6. if the runtime reports insufficient/missing `V64_NOISE_SHADOW` data, stop and return the exact FATAL; do not fabricate MFE or rerun accepted strategy evidence blindly.

After that result:

- if many losers have positive MFE but peak `<$2`, formulate an earlier-harvest successor hypothesis;
- if `MFE >= $2` trades still realize `<$1`, audit profit-lock execution/event behavior before parameter changes;
- if winners capture a small fraction of MFE, prioritize exit-harvest architecture;
- if MFE/giveback is not a dominant failure, return focus to entry-state/reentry quality rather than forcing a harvest change.
