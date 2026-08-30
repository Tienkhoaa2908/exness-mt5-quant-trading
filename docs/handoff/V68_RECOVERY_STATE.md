# V68 Recovery State

Last updated: 2026-08-31.

## Repository / safety

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`.
- Active branch: `agent/v68-v67-holdout-stability-research`.
- V68 is Strategy Tester research only. REAL-money authorization is false.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Do not rerun older milestones merely to recover V68.

## Accepted V67 evidence

- Accepted V67 runtime/evidence head: `782b44a566c772f833cb666ead1bbb21ce150b75`.
- Accepted V67 ZIP SHA256: `545b0baecba5f9ce077b692be90803623b23106b41eca43ef2728214c4d3707b`.
- ZIP CRC passed; 82 manifest payloads + manifest; every SHA matched; no missing or extra payloads.
- LONG and SHORT MetaEditor compile both `0 errors, 0 warnings`.
- All 12 frozen Model=4 passes completed.

V67 benchmark LONG:

- 4 trades, 3 wins / 1 loss;
- net `+$6.81`;
- PF about `6.82`;
- average win `+$2.66`;
- single loss `-$1.17`;
- 3 positive weeks, 1 flat week, 0 negative benchmark weeks;
- only 1 loser <=60 seconds;
- that LONG loser did not later reach any `$3/$3.5/$4` target after the stop in the independent noise shadow.

V67 bearish SHORT:

- 1 trade, 0 wins / 1 loss;
- net `-$1.10`;
- loss duration 351 seconds;
- the independent noise shadow shows the stop occurred before later reaching each tested target, so SHORT remains unvalidated and must not be promoted.

Stage conversion across all 12 V67 passes:

- 97 micro-entry arms;
- 60 first zone touches;
- 59 deeper penetrations;
- 44 post-zone closed-M1 reversal confirmations;
- 5 entry-ready / actual orders;
- 50 expiries;
- 42 structural invalidations.

Interpretation: V67 substantially reduced the V66 fast-stop problem and produced clean LONG benchmark economics, but only five actual trades across all evidence is too small for a stability claim.

## V68 decision

V68 is holdout validation only: **no strategy threshold change** relative to V67.

Generated-source equivalence is enforced by normalizing only version, magic, FILE_COMMON root and trade comment back to V67 and requiring exact equality with the V67 generated source for each direction.

V67 decision contract remains:

- XAUUSDm M15;
- fixed lot `0.01`;
- planned structural risk `$0.85-$1.10`;
- emergency loss guard about `$1.20` best effort;
- target `+$3.50`;
- risk/spread `>=4`;
- first cash-zone touch cannot order;
- deeper penetration risk threshold `$0.92`;
- closed-M1 post-zone reclaim required;
- confirmation validity 5 minutes;
- fixed BOS-owned M1 structural stop; no clamp;
- LONG/SHORT lanes evaluated independently;
- no fixed trade-count or weekly-dollar promotion quota.

## V68 holdout protocol

Calendar-month holdout relative to the V67 June-July-August calibration sequence:

- 2025-09-01 -> 2025-10-01;
- 2025-10-01 -> 2025-11-01;
- 2025-11-01 -> 2025-12-01;
- 2025-12-01 -> 2026-01-01;
- 2026-01-01 -> 2026-02-01;
- 2026-02-01 -> 2026-03-01;
- 2026-03-01 -> 2026-04-01;
- 2026-04-01 -> 2026-05-01;
- 2026-05-01 -> 2026-06-01.

Each month is run LONG-only and SHORT-only with Model=4 real ticks. Total = **18 Model=4 passes**.

No PnL-based month selection is allowed. These dates are a V67-calibration holdout, not a claim that no older project version ever viewed the dates.

## V68 evaluation

The analyzer reports for each independent lane:

- trades / wins / losses / WR / net / PF;
- average win / loss and max single loss;
- realized drawdown;
- positive / negative / flat months;
- best / worst / median monthly PnL and monthly dispersion;
- maximum consecutive negative months;
- losing trades <=15 / 30 / 60 seconds;
- stage conversion counts;
- noise-shadow stop-first / target-first outcomes.

Stable positive expectancy and loss control matter more than a fixed number of trades or fixed dollars per week.

## V68 files

- `scripts/build_v68_v67_holdout_stability_source.py`;
- `scripts/analyze_v68_v67_holdout_stability.py`;
- `runtime/v68_v67_holdout_stability/RUN_V68_V67_HOLDOUT_STABILITY.py`;
- `runtime/v68_v67_holdout_stability/START_V68_V67_HOLDOUT_STABILITY_GIT_BASH.sh`;
- `tests/test_v68_v67_holdout_stability_static.py`;
- `docs/adr/ADR-070-v68-v67-holdout-stability-research.md`;
- `docs/handoff/V68_RECOVERY_STATE.md`.

## Next recovery step

Require GitHub Actions success on the exact final V68 head. Then close MT5 and MetaEditor and run only the V68 launcher. Do not call V68 Windows PASS until both experts compile `0 errors, 0 warnings`, all 18 Model=4 passes complete, and the evidence ZIP passes integrity checks.
