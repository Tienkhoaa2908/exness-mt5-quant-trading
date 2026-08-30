# ADR-066 — V64 Microstructure Trigger + Independent Noise Shadow Research

Status: accepted for Strategy Tester research only.

## Context

Accepted V63 evidence showed that smaller cash losses alone did not create a profitable system. V63 completed 12 Model=4 real-tick passes, but the August benchmark and bearish SHORT validation were both negative. The most important diagnostic was microstructure timing: most losing trades were stopped within roughly one minute, frequently within seconds, while planned stop cash was small relative to the XAUUSDm spread.

The user-approved economic objective remains approximately three quality trades per week with materially positive expectancy; a reference case is two +$3.5 winners and one approximately -$1 loser, about +$6 for a week. This is a research KPI, not a promised return and not a data-selection criterion.

## GitHub engineering research

V64 reviewed public implementations for reusable engineering patterns. Their strategy performance claims are **unverified** and are not accepted as evidence for this project.

- `MunchonGithub/thragg-ea`: useful pattern is conditional setup arming followed by trigger-level execution, explicit setup expiry/invalidation, separate breakout/fill trigger styles, and ATR-normalized stop/spread geometry. V64 adopts the separation between belief/setup and execution trigger, not the repository's performance or AI claims.
- `smtlab/smartmoneyconcepts`: useful conceptual representation is liquidity as clustered highs/lows with a later swept state, plus FVG/OB zone mitigation. Its batch implementation can depend on future bars/zigzag state, so V64 does **not** copy it directly; all V64 microstructure tests use closed bars and past reference windows only.
- `foeed/FvgGold-EA`: useful patterns are FVG displacement/freshness, OB confluence, HTF alignment and entering near a zone rather than treating every signal as an immediate market entry. Advertised backtest returns/win rates are unverified and are not used as evidence or thresholds.
- `Solasent/MT5-SMC-Institutional-Liquidity-Scanner`: useful decomposition is Structure / OB / FVG / Liquidity / Sweep / Zone-state modules. The repository itself describes the real EA bridge as unfinished, so it is not an execution reference.

## Decision

V64 remains XAUUSDm M15, fixed lot `0.01`, Strategy Tester only, REAL-money authorization false.

### Economic contract

- Fixed lot: `0.01`.
- Actual target: `+$3.50`.
- Planned structural cash-risk band: `$0.85-$1.20`.
- Emergency cash-loss guard: approximately `$1.15`; slippage means realized loss is not guaranteed to stop exactly there.
- Minimum planned-risk / spread-cash ratio: `4.0`.
- Existing +$2 -> protect +$1 ratchet remains the actual position-management control.

The V64 risk band is deliberately not tightened below V63. V63 evidence indicated that stops around $0.60-$1.05 were frequently inside immediate XAUUSDm micro-noise relative to spread. V64 tests slightly more breathing room while still keeping losses near the user's approximately $1 preference.

### Trigger archetypes are separate

A setup must belong to one complete archetype. Scores from unrelated archetypes may not compensate for each other.

1. `PULLBACK_SWEEP_BOS`
   - H4/H1 direction aligned;
   - M15 pullback context;
   - at least one directional liquidity-sweep / OB-retest / premium-discount location context;
   - price must naturally fit the M5 structural risk zone;
   - closed M1 bars must show a sweep beyond an older reference range, reclaim it, then a displacement micro-BOS.

2. `BREAKOUT_RETEST_BOS`
   - H4/H1 direction aligned;
   - M15 BOS/CHoCH and structure aligned;
   - FVG or OB-retest context;
   - price must naturally fit the M5 structural risk zone;
   - closed M1 bars must retest an older micro level then produce a displacement micro-BOS.

### Trend quality

H4/H1 trend is no longer accepted only from sign. Entry also requires normalized quality:

- EMA20/EMA50 separation divided by ATR;
- EMA20 slope divided by ATR;
- M15 directional efficiency/path ratio;
- existing DI/MACD/ADX/M15 conflict vetoes remain.

Thresholds are preregistered in source and must be changed only in a later version after evidence review.

### Spread/stop geometry

A structurally valid setup is rejected when `planned_risk_cash / spread_cash < 4.0`. This directly targets V63 cases where spread consumed a large fraction of a very small stop budget.

### Independent post-stop noise shadow

Actual broker-simulated position management remains unchanged by the diagnostic shadow. Every actual entry starts an independent virtual path that remains alive for up to 480 minutes even if the actual position is stopped.

The shadow records first-hit outcomes for a 3x3 matrix:

- stop cash: `$1.10`, `$1.35`, `$1.60`;
- target cash: `$3.00`, `$3.50`, `$4.00`.

It also records maximum and minimum PnL over the fixed horizon. A `stop-then-recovery` diagnostic occurs when a variant hit its stop first but the same virtual path later reached that target within the horizon. This is specifically designed to answer whether tight V63 stops were noise sweeps followed by the expected move, or whether the setup genuinely failed.

The legacy single-shadow lifecycle must not block new V64 actual entries.

## Causality

- Microstructure uses `CopyRates(..., shift=1, ...)` closed bars.
- H1/H4 quality uses closed bars.
- Older M1 reference ranges are formed only from already closed bars.
- No centered/future pivot, negative shift, PnL-based window selection, or post-outcome feature is permitted for entry decisions.

## Validation protocol

For direct apples-to-apples comparison with V62/V63, retain the four fixed August 2026 benchmark weeks:

- week1: 2026.08.03 -> 2026.08.08
- week2: 2026.08.10 -> 2026.08.15
- week3: 2026.08.17 -> 2026.08.22
- week4: 2026.08.24 -> 2026.08.29

Each week runs LONG-only and SHORT-only Model=4 real ticks: 8 passes.

Also retain the PnL-independent annual directional screen from 2025.09.01 through 2026.08.29. Excluding benchmark weeks, select the four most recent bearish weeks with at least 8 strict SHORT signals and SHORT share >=60%, then run four SHORT-only Model=4 real-tick passes.

Total: **12 Model=4 real-tick passes** plus the Model=2 directional screen.

## Required analysis

Report actual broker-simulated performance per benchmark week/direction, monthly aggregate, bearish SHORT aggregate, trade frequency, win rate, average/max loss, profit factor, archetype counts, veto/rejection reasons, risk/spread geometry and the full 3x3 independent noise-shadow matrix.

Do not interpret direction-isolated sums as a concurrent account equity curve.

## Safety

- Strategy Tester research only.
- REAL-money authorization remains false.
- Do not promote based on static CI or external GitHub claims.
- Require Windows MetaEditor `0 errors, 0 warnings` for LONG, SHORT and screen sources plus fresh packaged tester evidence before any V64 profitability verdict.
