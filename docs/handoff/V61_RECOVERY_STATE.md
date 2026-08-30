# V61 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local Windows/Git Bash repo used by operator: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v61-profit-ratchet-m5-refinement-research`
- Accepted V61 research source/evidence head: `65cb308818a835c25e5fff17d8d71351ab901267`.
- V61 is Strategy Tester research only. It is not authorization for REAL-money activation.

## Frozen research intent

- XAUUSDm M15.
- Lot fixed at `0.01`.
- Strict H4 + H1 trend alignment; LONG and SHORT score logic symmetric.
- M15 structure/SMC signal engine with causal closed-bar data.
- M5 refinement is causal.
- Structural cash-risk band `$0.75-$1.25` at 0.01 lot.
- Actual target `$3`; profit ratchet arms at `+$2` and attempts to protect `+$1`.
- `OrderCheck()` before simulated broker order submission.
- Shadow targets `$2/$3/$4`.
- Tester-only; REAL money authorization remains false.

## Historical V61 recovery failures

1. Old head `bc0215e20b56714e582763b3da650c3517b82668`: generated MQL wrote FILE_COMMON to legacy `mt5_quant\v61_small_loss_cash_target` while runner read canonical `mt5_quant\v61_profit_ratchet_m5_refinement`. Fixed with canonical builders/runner plus legacy-root quarantine.
2. Head `7e3a7881ad5201ab1f51c62fbd1f6ab98da433a7`: Model=2 selector incorrectly required full execution `feasible=1`; fixed so screening uses directional signal + strict H4/H1, never PnL and never Model=2 execution feasibility.
3. Head `7699983739c9dbdb9cf9d611d5b4db98001a0bd1`: full-year screen produced only one row because screen was still the stateful execution EA with `ScreenOnly=true`. Fixed with a dedicated per-M15 directional screen path and coverage guard >=5000 rows / >=250 days.

Do not interpret any of those failures as alpha/model failure.

## Accepted V61 completed evidence

Operator returned the completed V61 evidence ZIP from head `65cb308818a835c25e5fff17d8d71351ab901267`.

Package integrity:

- ZIP CRC: PASS.
- ZIP SHA256: `1a421abe21d2879c25dd2ea1e46cd3ce29308c25d0e364bb611d53b1d0ba571f`.
- Bundle manifest: 44 entries, all SHA256 matches, no unlisted payload files except the manifest itself.
- Real and dedicated-screen MetaEditor logs both report `Result: 0 errors, 0 warnings`.

Dedicated screen coverage:

- `23526` M15 rows from `2025.09.01 00:00:00` through `2026.08.28 20:45:00`.
- Strict directional signals: `3576 LONG`, `1744 SHORT`.
- This proves the directional engine is not long-only.
- Selected validation weeks were two recent LONG weeks (`2026.08.24`, `2026.08.17`) and two recent SHORT weeks (`2026.08.03`, `2026.07.27`), selected without PnL.

Model=4 execution result over the four selected windows:

- Selected setups evaluated: `387`.
- Feasible setups: `4`.
- Feasible direction: `LONG=4`, `SHORT=0`.
- Actual round trips: `4`.
- Wins/losses: `3/1`, win rate `75%`.
- Gross profit `+$7.27`, gross loss `-$0.88`, net `+$6.39`.
- PF `8.2614`.
- Average winner `+$2.4233`, average loser `-$0.88`, max single loss `-$0.88`.
- Max realized DD `$0.88`.
- Profit-lock modifications `3`, failures `0`.
- OrderCheck preflight blocks `0`.
- Soft-loss exits `0`.
- All four feasible stops used source `m15`; M5 refinement produced no feasible trade.

Shadow target comparison on the four feasible LONG setups:

- `$2`: 3 wins / 1 loss, net `+$5.16`, PF `7.1429`.
- `$3`: 3 wins / 1 loss, net `+$8.16`, PF `10.7143`.
- `$4`: 0 wins / 4 losses, net `-$4.26`.

Actual ratchet behavior is meaningful in this small sample: one winner armed above +$2 and later exited through the moved stop around +$0.98; two other winners reached roughly +$3.19 and +$3.10. The one loser was about -$0.88.

## Critical V61 limitation discovered after completion

V61 did **not** actually validate SHORT execution/PnL.

- The runner selected two SHORT-regime weeks, but the real-tick pass did not enforce a direction filter.
- The broker trades occurring inside those SHORT-labelled windows were LONG trades when regime flipped later in the same week.
- Therefore V61 `+$6.39` is valid only as combined-engine evidence over the four windows. It is not evidence that SHORT trading is profitable or even executable under the current risk band.

SHORT feasibility evidence:

- Across the two SHORT-labelled real-tick windows there were `38` SHORT directional signals.
- Stop source among these SHORT signals: `20 m15`, `18 m5`.
- None were feasible at `$0.75-$1.25` risk.
- Of SHORT candidates reaching cash-risk calculation, minimum risk was about `$2.39`, median about `$4.94`, maximum about `$9.66`.
- Rejections were dominated by `stop_too_far_atr` and `structural_risk_cash_cap`.
- This means merely refining the stop is insufficient. With fixed 0.01 and small-loss priority, the next system should refine the **entry location**, waiting for M5/M1 retrace/retest closer to structural invalidation rather than widening the loss cap.

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60 merely to recover V61.
- Do not use `git clean`.
- Do not `stash pop` while tester/runtime is active.
- Do not overwrite accepted historical evidence.
- Do not promote V61 to production from four all-LONG feasible trades.
- Do not claim SHORT performance from V61.
- Do not arm or execute REAL-money trading as part of this research.

## Next research direction

Use a distinct V62 research branch. Required changes:

1. Direction-isolate real-tick validation: LONG-labelled passes may execute only LONG; SHORT-labelled passes may execute only SHORT.
2. Keep fixed lot `0.01`, structural risk band around `$0.75-$1.25`, target `$3`, +$2 -> +$1 profit ratchet.
3. Move from stop-only refinement to entry-timing refinement: M15/H4/H1 defines setup, but M5/M1 must wait for a real market retrace/retest near structural invalidation before market entry.
4. Do not fake/tighten the structural stop and do not widen loss budget just to create trades.
5. Preserve dedicated M15 directional screen and its coverage guard.
6. Report LONG and SHORT broker results independently, plus combined result.
7. Treat V61 sample as exploratory only; substantially larger direction-isolated real-tick evidence is required before promotion.
