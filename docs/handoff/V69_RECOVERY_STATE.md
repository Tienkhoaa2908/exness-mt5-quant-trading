# V69 Recovery State

Last updated: 2026-08-31.

## Repository / safety

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`.
- Active branch: `agent/v69-confirm-separation-retest-research`.
- V69 is Strategy Tester research only. REAL-money authorization is false.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Do not rerun older milestones merely to recover V69.

## Accepted V68 evidence

Accepted V68 runtime/evidence head: `e1684df89078c9a8c0320df2370bbee19d00ff42`.

Accepted V68 ZIP SHA256: `bb7b54f2ef0b30b83b2ee130c460ef2d0a50c9dfd9d78cdb89a88f084e35addb`.

Integrity / protocol:

- ZIP CRC passed;
- 118 manifest payloads matched SHA256 and no payload was missing or extra;
- V68 evidence pins V67 accepted head `782b44a566c772f833cb666ead1bbb21ce150b75` and V67 accepted ZIP SHA `545b0baecba5f9ce077b692be90803623b23106b41eca43ef2728214c4d3707b`;
- LONG and SHORT MetaEditor compile both `0 errors, 0 warnings`;
- all 18 Model=4 calendar-month passes completed with `state=STOPPED`, `detail=1`, symbol `XAUUSDm`, fixed lot `0.01`.

V68 LONG holdout:

- 28 trades;
- 10 wins / 18 losses;
- WR `35.71%`;
- gross profit `$22.57`, gross loss `$19.70`;
- net `+$2.87`;
- PF about `1.1457`;
- average win about `+$2.257`;
- average loss about `-$1.094`;
- max single loss `-$1.15`;
- max realized DD `$6.04`;
- 3 positive months / 2 negative / 4 flat;
- month PnL: Sep `-$4.93`, Oct `+$8.02`, Nov `+$1.24`, Dec `-$2.33`, Jan `+$0.87`, Feb-May flat;
- 5 losers <=15s, 7 <=30s, 11 <=60s.

V68 SHORT holdout:

- 2 trades;
- 0 wins / 2 losses;
- net `-$2.22`;
- PF `0`;
- max single loss `-$1.12`;
- both losses exited within 15 seconds;
- no positive month.

V68 LONG noise shadow across the same 28 entries:

- `$1.10 / $3.50`: 9 target-first, 19 stop-first, net `+$10.60` in shadow accounting; 15 stop-first paths later reached target;
- `$1.35 / $3.50`: 11 target-first, 17 stop-first, net `+$15.55`; 13 stop-first paths later reached target;
- `$1.60 / $3.50`: 12 target-first, 16 stop-first, net `+$16.40`; 12 stop-first paths later reached target.

These wider-stop shadows are diagnostic only. V69 does not widen the structural stop.

## V68 root-cause diagnostic used for V69

The V67/V68 state machine requires zone penetration and a closed-M1 reclaim, but once reclaim is confirmed it can enter whenever the existing cash-risk band is feasible. It does not require the reclaim to establish favorable separation from the structural stop and then survive a later retest.

Observed on the 28 V68 LONG entries:

- four entries had confirmation-to-entry delay exactly 0 seconds; all four lost;
- confirmation-to-entry delay below 30 seconds was associated with materially worse development-sample economics than entries delayed at least 30 seconds;
- this observation is post-hoc and is not treated as proof of an optimal timer.

Technical interpretation: `reclaim confirmation` and `entry trigger` are still partially conflated. A valid reversal should first demonstrate displacement/separation away from invalidation, then offer a later retest into the bounded cash-risk zone.

## V69 decision

V69 preserves all V67/V68 signal and risk semantics and inserts one causal state:

`M15 setup -> M5 context -> M1 BOS -> fixed structural stop -> cash-zone touch -> deeper penetration -> closed-M1 reclaim -> favorable separation -> later cash-zone retest -> revalidation -> OrderCheck -> order`.

Preregistered V69 additions:

- reclaim confirmation itself cannot order;
- minimum favorable post-confirm prospective risk distance: `$1.30` from the fixed stop;
- the tick first satisfying separation cannot order;
- entry must be a later retest into the unchanged `$0.85-$1.10` risk band;
- confirmation must be at least 30 seconds old;
- existing 5-minute confirmation validity remains;
- a new adverse extreme that invalidates confirmation also resets separation state.

Unchanged:

- XAUUSDm M15;
- fixed lot `0.01`;
- planned risk `$0.85-$1.10`;
- emergency cash loss guard about `$1.20` best effort;
- actual target `+$3.50`;
- risk/spread `>=4`;
- fixed BOS-owned M1 structural stop, no widening, no clamp;
- LONG and SHORT evaluated independently;
- no fixed weekly trade-count or dollar-profit promotion quota.

## V69 validation

V69 replays exactly the nine V68 months from 2025-09 through 2026-05, LONG + SHORT, Model=4, total 18 passes.

This is explicitly a **development replay, not an independent holdout**, because V69 was designed after inspecting V68. No month is selected by PnL. If V69 improves the replay, later untouched or forward evidence is still required.

## V69 observability

Important new events:

- `POST_CONFIRM_SEPARATION`;
- `POST_CONFIRM_RETEST_READY`;
- `POST_CONFIRM_ENTRY_READY`.

Existing stage and fast-loss diagnostics remain.

## Static checkpoint

- V69 substantive/static checkpoint: `695759bfcc1802179293639f341f5123f688a7c7`.
- V69-specific Actions run `#2` / run id `33335442297` completed successfully on that exact checkpoint: Python compile, launcher syntax, generated-source state-machine tests and secret scan passed.
- Full repository quality run `#926` / run id `33335442296` completed successfully on the same checkpoint: Python compile, historical launcher syntax checks, policy wording, full pytest, secret scan and V29 quarantine all passed.
- The earlier V69-specific run on `afecb535...` failed only because the test duplicated a FILE_COMMON literal with the wrong Python backslash representation. The test was corrected to use canonical builder constants; strategy logic was unchanged.
- Any later documentation-only head must itself pass V69-specific and full quality checks before Windows runtime is accepted.

## V69 files

- `scripts/build_v69_confirm_separation_retest_source.py`;
- `scripts/analyze_v69_confirm_separation_retest.py`;
- `runtime/v69_confirm_separation_retest/RUN_V69_CONFIRM_SEPARATION_RETEST.py`;
- `runtime/v69_confirm_separation_retest/START_V69_CONFIRM_SEPARATION_RETEST_GIT_BASH.sh`;
- `tests/test_v69_confirm_separation_retest_static.py`;
- `docs/adr/ADR-071-v69-confirm-separation-retest-research.md`;
- `docs/handoff/V69_RECOVERY_STATE.md`.

## Next recovery step

Require GitHub Actions success on the exact final V69 head. Then, with MT5 and MetaEditor closed, run only the V69 launcher. Do not call V69 runtime PASS until both experts compile `0 errors, 0 warnings`, all 18 Model=4 passes complete, and ZIP integrity passes.
