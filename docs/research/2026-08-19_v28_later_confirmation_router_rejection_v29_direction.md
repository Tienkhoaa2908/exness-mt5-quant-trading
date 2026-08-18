# V28 later confirmation: fixed range router rejected; V29 direction

Ngày: 2026-08-19.

## Runtime/data evidence
Latest V3 user diagnostic ZIP SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`.

- MetaEditor compile remains 0 errors / 0 warnings.
- V2 partial recovered: 671 USD calendar rows, Apr-01 through early Jun.
- V3 current partial: 38 USD calendar rows, Jun-11 through Jun-15.
- V3 progress stopped at Jun-20 with `last_error=0`; this is not a calendar API data error.
- Merge V27 recovered + V1 March + V2 + V3 and dedupe by `value_id` gives 25,017 calendar values, with USD coverage through 2026-06-15.
- Calendar extraction is CLOSED. Do not ask the user to run another calendar exporter.

## Later confirmation without retuning V28 threshold
The cross-asset range model was frozen through Feb-2026 and scored Mar-May 2026 without retuning the natural V28 0.25 threshold.

Monthly future-range Spearman:
- Mar: base ~0.5907, event-aware ~0.5842;
- Apr: base ~0.5271, event-aware ~0.5360;
- May: base ~0.6901, event-aware ~0.6810.

Mean:
- base ~0.60263;
- event-aware ~0.60042;
- event incremental uplift ~-0.00221.

Conclusion: **the range/regime predictive layer generalizes strongly, but the incremental USD-calendar uplift does not confirm in Mar-May.** Calendar remains useful context/telemetry, not a mandatory alpha block.

The event-aware low25 bucket still separates future magnitude well, but that does NOT imply a stable family switch.

## Fixed V28 low25 routing hypothesis fails
On `usd40_r1p0_cent`, Mar-May later confirmation:

`ema_h1_skip20`:
- score <25%: n=16, AvgR ~+0.2704;
- middle 50%: n=49, AvgR ~+0.1670;
- high25: n=32, AvgR ~-0.3137.

`router_ema_bos8`:
- low25 AvgR ~+0.3213;
- middle50 ~+0.1569;
- high25 ~-0.2445.

This reverses the earlier screening premise that low25 was the weak EMA state and should route to MACD. Family × scalar-range mapping is nonstationary.

**Decision: reject the existing V28 pre-registered low25 stateful replay. Do NOT ask the user to run `mt5_quant_v28_event_regime_replay_lab_one_click.zip`.**

## Other ML gates checked
- Frozen cross-asset direction classifier remains only modest in Mar-May (AUC approximately 0.529 / 0.514 / 0.520) and does not provide a stable family-level veto.
- EMA trade-level meta-labeler that looked good pre-confirmation collapses near random in Mar-May (~0.516 combined AUC) and its veto direction is not economically stable.
- Future path/trend-efficiency prediction is weak and is not promoted.

Therefore ML should continue to own continuous market-state estimation, not direct Buy/Sell and not a fixed one-dimensional family map.

## V29 orthogonal-alpha screening
A new multi-horizon slow-momentum expert was screened from existing MT5 bars; no new user data is required.

Natural construction:
- decision only at server 00:00 and 08:00, avoiding the rollover window;
- 16h and 24h trailing-return directions must agree;
- enter next bar;
- 8h maximum hold;
- 2 ATR initial stop;
- TP 4R.

M15 screening AvgR:
- 2024 ~+0.112R;
- 2025 ~+0.161R;
- 2026 ~+0.147R.

Nearby 12h-24h lookback variants are directionally robust. Raw-return screening remains positive after historical spread plus 1-3 bps additional friction for the central 16h+24h agreement specification during 2024-2026.

However, longer M30 history exposes regime dependence:
- after historical spread + 1bp stress, 8h slow-momentum net expectancy is roughly -1.75 bps in 2022, -1.86 bps in 2023, +0.86 bps in 2024, +3.96 bps in 2025, +5.55 bps in 2026;
- with the 2ATR/TP4R research stop, AvgR evolves from ~-0.066R (2022) to ~+0.018R (2023), +0.037R (2024), +0.111R (2025), +0.124R (2026).

Thus this is a promising **orthogonal expert**, not a universally-on replacement.

## V29 architecture decision
Literature direction and project evidence now agree on a different architecture:

1. Keep the validated ML range model as a continuous state feature.
2. Add a genuinely different slow multi-horizon momentum expert.
3. Maintain existing EMA/BOS/MACD/Trend experts as independent shadow books.
4. Introduce change-point / regime-transition severity as a control on **how fast the meta-router forgets stale expert performance**, not as a hard Buy/Sell rule.
5. Use nonstationary online-expert allocation / switching-cost-aware logic rather than a fixed `range_pct -> family` lookup.
6. Evaluate worst-window/DD/turnover penalties, not mean return alone.
7. Fast-reversion/changepoint expert remains experimental until its conditional edge is stable; generic shock fading is rejected because 2026 behavior differs from 2024-2025.

Relevant research references: Wood/Roberts/Zohren, *Slow Momentum with Fast Reversion*; Adams/MacKay Bayesian Online Changepoint Detection; fixed-share/tracking-expert literature; Deep Momentum Networks and Momentum Transformer. These are architecture references only, not evidence that XAU will reproduce published results.

## Next gate
Create V29 Adaptive Change-Point + Multi-Horizon Expert Lab offline first. Do not request more MT5 data. Do not run V28 fixed low25 replay. Only one MT5 replay batch should be given to the user after the V29 candidate catalog is frozen.

Safety unchanged: REAL-MONEY LIVE TRADING = FORBIDDEN; no native broker orders; stop-risk research ceiling 1.00%/trade.