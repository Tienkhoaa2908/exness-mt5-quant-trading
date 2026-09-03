# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 08:00 (+07)

## Authority / safety

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active research branch: `agent/v71-fx-portability-research`.

Always resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI before acting.

SHORT disabled. SHORT remains rejected for activation. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Contract: XAUUSDm M15, LONG only, lot 0.01, planned risk about $0.85-$1.10, emergency guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready, fixed stop, inherited +$2 -> about +$1 profit ratchet.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Sep 2025-May 2026 is development-only. Month PnL: Sep -$1.84, Oct +$9.15, Nov +$1.24, Dec -$2.28, Jan +$0.87, Feb-May flat.

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

## Settled research before V71

- DEMO execution transport PASS on 0.01 XAUUSDm.
- Live no-trade window was bearish `short_edge`; LONG-only isolation was working, not broker failure.
- All-bar coverage: 23,526 M15 bars; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.
- Downstream LONG funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`; separation is not the dominant contraction.
- HARD_STRUCTURAL 235/460 is the largest cycle terminal family.
- BREAKOUT_RETEST_BOS produced 22/24 trades; PULLBACK_SWEEP_BOS only 2.
- V70 true-position telemetry replaced the invalid post-exit `V64_NOISE_SHADOW` MFE attribution.
- V70 same-run baseline was +$6.44 because one historical swap row changed by -$0.70 versus accepted V69. Raw audit proved identical exit time/price/gross profit/reason and cost-only drift.
- V70 TIERED exit shadow was best (+$0.68 vs contemporaneous baseline) but changed only 4/24 reused development trades, so no exit semantic was promoted.

## V71 FX portability objective

User requested testing the strategy on Forex because XAUUSD moves quickly and fast losses may be partly instrument-specific.

V71 is a **direct portability test**, not an optimization pass. It keeps the frozen V69 LONG decision/entry/real-exit semantics exactly after metadata normalization. It changes only version/magic/telemetry root and tester symbol.

Default campaign:

- control: `XAUUSDm`;
- FX: `EURUSDm`, `GBPUSDm`, `USDJPYm`, `AUDUSDm`;
- M15, LONG only;
- real ticks (`Model=4`);
- one full tester pass per symbol from `2025.09.01` to `2026.06.01`;
- fixed lot `0.01`;
- unchanged cash-risk band `$0.85-$1.10`;
- unchanged emergency loss `$1.20`;
- unchanged target `$3.50`;
- unchanged risk/spread floor `4.0`;
- unchanged V69 separation `$1.30` and confirmation age `30s`;
- no V70 exit-harvest promotion;
- no SHORT; no REAL.

Why no FX retune in the first pass: structural features are ATR-normalized and cash risk/spread are calculated through MT5 symbol/tick economics. Keeping the same dollar risk budget makes the first comparison interpretable. If a pair is promising, symbol-specific tuning must be a later research line with proper validation, not mixed into portability screening.

## V71 implementation

Added:

- `scripts/build_v71_fx_portability_source.py` — exact V69 LONG strategy-equivalence gate after metadata normalization.
- `scripts/analyze_v71_fx_portability.py` — per-symbol trades/wins/losses/net/PF/DD, explicit costs, fast-loss share, monthly PnL, event funnel and eval rejects.
- `runtime/v71_fx_portability_research/RUN_V71_FX_PORTABILITY_RESEARCH.py` — one compile + one full-period real-tick tester run per symbol.
- `runtime/v71_fx_portability_research/RUN_V71_FX_PORTABILITY_RESEARCH_GIT_BASH.sh` — exact-HEAD launcher.
- `tests/test_v71_fx_portability_research.py`.
- `.github/workflows/v71_fx_portability_quality.yml`.

The default campaign is five tester passes total, not 5 symbols x 9 monthly passes. Monthly economics are reconstructed from deal timestamps afterward to reduce operator time.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_EXIT_POLICY_DECISION=NO_PROMOTION`
`V71_RESEARCH=FX_PORTABILITY_DIRECT_NO_RETUNE`
`V71_V69_LONG_STRATEGY_EQUIVALENT=1`
`V71_DEFAULT_SYMBOLS=XAUUSDm,EURUSDm,GBPUSDm,USDJPYm,AUDUSDm`
`V71_TESTER_RUNS_DEFAULT=5`
`V71_FX_ENTRY_RETUNE=0`
`V71_FX_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Require exact-head CI success on the final V71 handover HEAD.
2. Operator closes MT5 and MetaEditor and runs the single V71 launcher.
3. If a configured broker symbol is unavailable, fail closed and adjust symbol naming only; do not alter strategy thresholds.
4. Compare each FX pair against the same-run XAU control using trade count, net, PF, DD, month breadth and fast-loss share.
5. Do not treat a small positive sample as proof of edge. The campaign is development-only portability evidence.
6. Only after the cross-symbol result choose whether to continue with one FX pair, broaden to more pairs, or return to XAU-specific research.
7. Do not enable SHORT. Do not authorize REAL money.
