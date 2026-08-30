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

## V61 failed run at old head

Old failed head: `bc0215e20b56714e582763b3da650c3517b82668`.

What passed on Windows before the failure:

- Static tests passed.
- Secret scan passed.
- Both V61 EA sources were generated.
- `V61ProfitRatchetM5Refinement` compiled with MetaEditor `0 errors, 0 warnings`.
- `V61ProfitRatchetM5RefinementScreen` compiled with MetaEditor `0 errors, 0 warnings`.

Failure:

- Screen Model=2 launched, then runner raised `V61 run screen missing entry evaluation evidence`.
- This failure must **not** be interpreted as alpha/signal/model failure.

Confirmed root cause:

- V61 builder inherited V60 by text transform.
- Generated MQL FILE_COMMON root became legacy `mt5_quant\v61_small_loss_cash_target`.
- V61 runner expected canonical `mt5_quant\v61_profit_ratchet_m5_refinement`.
- Therefore EA output and runner evidence lookup diverged.
- Reused V60 runner helpers also printed `V60_*` labels inside a V61 run; this is observability debt and can confuse diagnosis, but it was not the root cause.

## Fixed layer added after the failure

Use the fixed thin layer, not the old V61 launcher:

- `scripts/build_v61_profit_ratchet_m5_refinement_source_fixed.py`
- `scripts/build_v61_profit_ratchet_m5_refinement_screen_source_fixed.py`
- `runtime/v61_profit_ratchet_m5_refinement/RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py`
- `runtime/v61_profit_ratchet_m5_refinement/START_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED_GIT_BASH.sh`
- `tests/test_v61_file_common_path_fix_static.py`

The fixed builder rewrites the FILE_COMMON root to the canonical V61 root and rejects legacy-root leakage. The fixed runner archives both canonical and legacy roots before every pass, emits V61-native alias logs, and prints canonical/legacy directory listings if evidence is missing. If fresh evidence appears in the legacy root, it fails explicitly with `V61_FILE_COMMON_ROOT_MISMATCH`.

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60 merely to recover V61.
- Do not use `git clean`.
- Do not `stash pop` while a tester/runtime task is active.
- Do not overwrite accepted historical evidence.
- Do not claim V61 Windows PASS until the fixed source is recompiled 0/0 and all requested tester passes finish with an evidence ZIP.
- Do not arm or execute REAL-money trading as part of V61 research.

## What a new chat should do next

1. Read this file first.
2. Resolve the latest head of `agent/v61-profit-ratchet-m5-refinement-research` and verify CI on that exact SHA.
3. Run only the fixed V61 launcher after MT5 and MetaEditor are closed.
4. Require new MetaEditor 0/0 evidence for the fixed generated sources.
5. Require `V61_EVIDENCE_ROOT_PASS` for screen and every real-tick pass.
6. If missing evidence recurs, inspect the printed canonical and legacy listings before changing strategy logic.
7. Once V61 completes, analyze LONG/SHORT separately, stop-source counts (`m15` vs `m5`), OrderCheck blocks, profit-lock modifications/failures, actual net USD/PF/average loss/max loss, and shadow `$2/$3/$4` outcomes.
