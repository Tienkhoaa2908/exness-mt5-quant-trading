# V61 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local Windows/Git Bash repo used by operator: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v61-profit-ratchet-m5-refinement-research`
- V61 is Strategy Tester research only. It is not authorization for REAL-money activation.

## Frozen research intent

- Symbol/runtime research target: XAUUSDm M15.
- Lot is fixed at `0.01` for V61 research.
- Strict H4 + H1 trend alignment; LONG and SHORT remain symmetric.
- M15 structure/SMC signal engine with causal closed-bar data.
- M5 refinement is causal and may only refine the structural stop when it remains structurally valid.
- Structural cash-risk band: `$0.75` to `$1.25` at 0.01 lot.
- Actual target: `$3`.
- Profit ratchet: arm at `+$2`, then attempt to protect at least `+$1`.
- `OrderCheck()` preflight is required before simulated broker order submission.
- Shadow targets remain `$2`, `$3`, `$4` for comparison.

## Accepted V60 evidence that motivated V61

V60 real-tick broker simulation produced 5 completed round trips: 3 wins / 2 losses, net about `+$4.22`, PF about `3.24`, average winner about `+$2.03`, average loser about `-$0.94`, maximum single loss about `-$1.00`. One very tight stop setup was rejected with retcode 10016. V60 shadow evidence suggested `$3` outperformed `$2` in the small sample, while `$4` did not. Treat this as research evidence, not production proof.

## V61 failure 1: FILE_COMMON path mismatch

Old failed head: `bc0215e20b56714e582763b3da650c3517b82668`.

What passed on Windows before the failure:

- Static tests and secret scan passed.
- Both V61 sources were generated.
- `V61ProfitRatchetM5Refinement` compiled `0 errors, 0 warnings`.
- `V61ProfitRatchetM5RefinementScreen` compiled `0 errors, 0 warnings`.

Failure: screen launched, then runner raised `V61 run screen missing entry evaluation evidence`.

Confirmed root cause: inherited builder transformed V60 namespace to legacy `mt5_quant\v61_small_loss_cash_target`, while V61 runner expected canonical `mt5_quant\v61_profit_ratchet_m5_refinement`.

Fixed layer introduced canonical builders/runner/launcher and regression coverage. The fixed runner archives both canonical and legacy roots, emits canonical/legacy listings on missing evidence, and explicitly fails with `V61_FILE_COMMON_ROOT_MISMATCH` if fresh evidence leaks to the legacy root.

## V61 failure 2: Model=2 screen selection incorrectly required execution feasibility

Head observed on Windows: `7e3a7881ad5201ab1f51c62fbd1f6ab98da433a7`.

What passed in this run:

- Fixed-layer static tests passed.
- Fixed real source SHA256: `69ffa10aad67cb393c641f7e7d4d35ed8abd7b69305f3f36249e7f864923a4b9`.
- Fixed screen source SHA256: `627ab5b24f0422eca3df06c589a4312d1f6201e75df253fa88d722bb4ebeaf94`.
- Both fixed V61 sources compiled with MetaEditor `0 errors, 0 warnings`.
- Model=2 screen ran and `V61_EVIDENCE_ROOT_PASS label=screen` proved canonical FILE_COMMON evidence path was fixed.
- `MT5_LAUNCH_RC=100007` is not, by itself, evidence of tester failure because screen evidence was successfully produced and copied.

Failure: selection raised `V61 screen did not find two feasible strict H4/H1 weeks per side; long_weeks={} short_weeks={}`.

Confirmed design bug: the screen selector required `feasible=1`. In V61, `feasible` includes the narrow `$0.75-$1.25` risk band plus spread/margin/broker geometry and M5 stop refinement. That is inappropriate for Model=2 whose purpose is only PnL-independent directional/window screening. Execution feasibility belongs to Model=4 real-tick validation.

Fix: `RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py` now selects two most recent LONG and SHORT weeks using `selected_direction` plus strict H4/H1 alignment, without using PnL and without requiring Model=2 execution feasibility. It separately records `screen_feasible_signal_count`, rejection counts, and `V61_SCREEN_DIAGNOSTICS.json`. Model=4 remains authoritative for actual trade feasibility and broker mapping.

## Fixed layer files

Use the fixed thin layer, not the old V61 launcher:

- `scripts/build_v61_profit_ratchet_m5_refinement_source_fixed.py`
- `scripts/build_v61_profit_ratchet_m5_refinement_screen_source_fixed.py`
- `runtime/v61_profit_ratchet_m5_refinement/RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py`
- `runtime/v61_profit_ratchet_m5_refinement/START_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED_GIT_BASH.sh`
- `tests/test_v61_file_common_path_fix_static.py`

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60 merely to recover V61.
- Do not use `git clean`.
- Do not `stash pop` while a tester/runtime task is active.
- Do not overwrite accepted historical evidence.
- Do not claim V61 Windows PASS until the current fixed source is recompiled 0/0 and all requested Model=4 tester passes finish with an evidence ZIP.
- Do not arm or execute REAL-money trading as part of V61 research.
- Do not infer alpha/model failure from orchestration, FILE_COMMON, or screen-selection errors.

## What a new chat should do next

1. Read this file first.
2. Resolve latest branch head and verify CI on that exact SHA.
3. Run only `START_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED_GIT_BASH.sh` after MT5 and MetaEditor are closed.
4. Require fixed-source MetaEditor 0/0 evidence.
5. Require `V61_EVIDENCE_ROOT_PASS` for screen and every real-tick pass.
6. Inspect `V61_SCREEN_DIAGNOSTICS` / `V61_SCREEN_DIAGNOSTICS.json`; screen selection must be PnL-independent and must not require execution feasibility.
7. If fewer than two directional weeks exist on either side, treat that as a directional-model frequency problem and inspect counts before changing execution/risk logic.
8. Once V61 completes, analyze LONG/SHORT separately, `m15` vs `m5` stop-source counts, OrderCheck blocks, profit-lock modifications/failures, actual net USD/PF/average loss/max loss, and shadow `$2/$3/$4` outcomes.
