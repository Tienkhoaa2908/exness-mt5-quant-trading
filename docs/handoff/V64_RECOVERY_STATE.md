# V64 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v64-microstructure-trigger-shadow-research`
- V64 is Strategy Tester research only. REAL-money authorization remains false.

## Accepted V63 evidence motivating V64

- V63 accepted evidence head: `0ea78cf33e59a5d6cd7a24191abd04059e57e363`.
- V63 evidence ZIP SHA256: `51bf661266594c3f45c845de9b59a1303208e0f259b6936380baf7c721ca7929`.
- ZIP CRC passed; all 97 listed manifest payload hashes matched.
- V63 LONG, SHORT and screen experts compiled Windows MetaEditor with 0 errors / 0 warnings.
- V63 completed all 12 Model=4 real-tick passes.
- August isolated benchmark: 17 trades, 3 wins / 14 losses, net about `-$4.38`, PF about `0.647`.
- Four bearish SHORT weeks: 16 trades, 3 wins / 13 losses, net about `-$2.76`, PF about `0.745`.
- One bearish week showed the desired economic shape (4 trades, 3 wins / 1 loss, about `+$7.44`) but the other bearish weeks were negative.
- Critical failure anatomy: 20/27 losing trades in the combined diagnostic evidence stopped within about 30 seconds and 24/27 within about 60 seconds; loser median duration was about 11 seconds. Planned stops were frequently small relative to XAUUSDm spread.
- V63 M1 confirmation was too weak: essentially one directional closed M1 candle relative to the previous candle, not a full liquidity sweep/reclaim plus micro-BOS.
- Existing confluence score was not predictive enough: accepted entries generally already had MACD alignment and usually DI alignment, yet win rate remained poor. V64 therefore does not solve the problem by merely raising score or stacking indicators.

## User-approved research objective

Approximately three quality trades in a week is acceptable if expectancy improves materially. A useful reference case is two +$3.5 winners and one approximately -$1 loser, roughly +$6 for a week.

This is a research KPI, not a promised weekly return and not a PnL-based selection rule.

## GitHub engineering research used by V64

External strategy/backtest claims are **unverified**. Only engineering patterns/definitions are adopted.

- `MunchonGithub/thragg-ea`: arm a setup first and execute only after a conditional trigger; explicit invalidation/expiry; separate breakout vs fill trigger types; ATR-normalized spread and stop geometry.
- `smtlab/smartmoneyconcepts`: liquidity clusters, swept-state representation and FVG/OB mitigation concepts. Its batch/zigzag implementation is not directly causal, so V64 uses only past closed-bar reference windows.
- `foeed/FvgGold-EA`: XAUUSD/M15 FVG displacement/freshness, OB confluence and zone-oriented entry concepts. Advertised returns/win rates are unverified and are not evidence for this project.
- `Solasent/MT5-SMC-Institutional-Liquidity-Scanner`: useful Structure / OB / FVG / Liquidity / Sweep / Zone-state module decomposition; its own roadmap says the real EA bridge is unfinished, so it is not an execution reference.

## Frozen V64 architecture

- Symbol/timeframe: XAUUSDm M15.
- Fixed lot: `0.01`.
- Actual target: `+$3.50`.
- Planned structural cash-risk band: `$0.85-$1.20`.
- Emergency cash guard: approximately `$1.15`; realized loss can exceed it due to execution/slippage.
- Minimum planned-risk / spread-cash ratio: `4.0`.
- Existing +$2 -> protect +$1 ratchet remains actual position management.
- H4/H1 direction remains strict.
- H4/H1 trend quality additionally uses EMA20/50 separation/ATR and EMA slope/ATR.
- M15 directional efficiency is an additional regime-quality gate.
- Existing DI/MACD/ADX conflict veto remains.

### Separate trigger archetypes

1. `PULLBACK_SWEEP_BOS`
   - directional M15 pullback context;
   - liquidity sweep, OB retest, or correct premium/discount context;
   - M5 structural stop must naturally satisfy risk/spread geometry;
   - closed M1 sweep beyond an older range, reclaim, then displacement micro-BOS.

2. `BREAKOUT_RETEST_BOS`
   - directional M15 BOS/CHoCH + structure;
   - FVG or OB retest context;
   - M5 structural stop must naturally satisfy risk/spread geometry;
   - closed M1 retest then displacement micro-BOS.

Archetype scores may not compensate for each other. A setup must complete one archetype.

## Independent noise-shadow experiment

Every actual V64 entry starts an independent virtual path that remains alive for up to 480 minutes even if the actual trade is stopped. This path must not gate new actual trades.

First-hit matrix:

- stops: `$1.10`, `$1.35`, `$1.60`;
- targets: `$3.00`, `$3.50`, `$4.00`;
- 9 stop/target combinations total.

The path also records max/min cash PnL. Analyzer must count `stop-then-recovery`: a variant hit stop first, but the same virtual path later reached its target within the horizon. This is required before deciding whether any later version should widen stops or instead further improve entries.

## V64 validation protocol

Use the same fixed August benchmark for apples-to-apples comparison:

- week1: 2026.08.03 -> 2026.08.08
- week2: 2026.08.10 -> 2026.08.15
- week3: 2026.08.17 -> 2026.08.22
- week4: 2026.08.24 -> 2026.08.29

Each runs LONG-only and SHORT-only Model=4 real ticks: 8 passes.

Run the dedicated PnL-independent Model=2 directional screen from 2025.09.01 through 2026.08.29. Exclude benchmark weeks and select the four most recent weeks with strict SHORT signals >=8 and SHORT share >=60%. Run four SHORT-only Model=4 real-tick passes.

Total V64: **12 Model=4 real-tick passes** plus annual Model=2 directional screen.

## Required V64 evidence / reporting

- Windows MetaEditor compile logs for LONG, SHORT and screen experts, each 0 errors / 0 warnings.
- Direction-isolated actual broker-simulated results per benchmark week.
- Actual monthly LONG, SHORT and isolated sum.
- Bearish SHORT actual results.
- Archetype arm counts and entry/refinement veto reasons.
- Planned risk/spread ratio diagnostics.
- `V64_NOISE_SHADOW.csv` and 3x3 matrix results.
- `stop_then_later_target` counts for every stop/target variant.
- ZIP CRC + manifest hashes.

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60/V61/V62/V63 merely to recover V64.
- Do not `git clean`.
- Do not `stash pop` while tester work is active.
- Do not overwrite accepted V63 evidence.
- Do not activate REAL-money trading.
- Do not claim V64 Windows PASS until LONG, SHORT and screen compile 0/0 and all tester phases package fresh evidence.
- Do not claim the +$6/week research objective is achieved unless fresh evidence actually shows it.
- Do not interpret direction-isolated sums as a concurrent account equity curve.
- Do not treat public GitHub strategy performance claims as evidence for this system.

## What a new chat should do next

1. Read this file and `docs/handoff/V63_RECOVERY_STATE.md`.
2. Resolve the latest exact head of `agent/v64-microstructure-trigger-shadow-research`.
3. Verify GitHub Actions quality on that exact head.
4. Run only the V64 launcher after MT5 and MetaEditor are closed.
5. Require 0 errors / 0 warnings for V64 LONG, SHORT and screen experts.
6. Require annual screen coverage, eight fixed benchmark Model=4 passes and four bearish SHORT Model=4 passes.
7. Analyze actual profitability first, then archetype quality and the independent stop-then-recovery matrix.
