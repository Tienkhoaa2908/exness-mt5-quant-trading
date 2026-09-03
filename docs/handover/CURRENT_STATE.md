# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 14:15 (+07)

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

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Sep 2025-May 2026 is development-only.

Actual DEMO execution transport PASS. `V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`.

## Settled research before V71

- XAU live no-trade window was bearish `short_edge`; LONG-only isolation was working, not broker failure.
- All-bar coverage: 23,526 M15 bars; LONG 3,576; SHORT 1,744; neutral 18,206. Global LONG starvation rejected.
- Downstream LONG funnel: `460 -> 404 -> 167 -> 95 -> 51 -> 49 -> 24 -> 24`; separation is not the dominant contraction.
- HARD_STRUCTURAL 235/460 is the largest XAU cycle terminal family.
- BREAKOUT_RETEST_BOS produced 22/24 XAU trades; PULLBACK_SWEEP_BOS only 2.
- V70 true-position telemetry replaced invalid post-exit `V64_NOISE_SHADOW` MFE attribution.
- V70 same-run baseline was +$6.44 because one historical swap row changed by -$0.70 versus accepted V69; raw audit proved identical exit time/price/gross profit/reason and cost-only drift.
- V70 TIERED exit shadow was best (+$0.68 vs contemporaneous baseline) but changed only 4/24 reused development trades, so no exit semantic was promoted.

## V71 FX direct-portability campaign — completed

User requested testing Forex because XAU moves quickly and fast XAU losses may be partly instrument-specific.

V71 kept the frozen V69 LONG decision/entry/real-exit semantics exactly after metadata normalization. No symbol-specific retune was applied.

Campaign contract:

- control `XAUUSDm`; FX `EURUSDm`, `GBPUSDm`, `USDJPYm`, `AUDUSDm`;
- M15, LONG only, real ticks (`Model=4`);
- `2025.09.01 -> 2026.06.01`;
- fixed lot 0.01;
- cash-risk band $0.85-$1.10;
- emergency loss $1.20;
- target $3.50;
- risk/spread >=4;
- V69 separation $1.30 and confirmation age 30s;
- no V70 exit promotion; no SHORT; no REAL.

Operator completed all five tester passes successfully at evidence HEAD:

`82994371d4717ed947a0d9e8057617bf96ea8c8b`

Generated source SHA256:

`32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`

EX5 SHA256:

`69896c6b330c6dd4bbb13acf7ee27ea1efccbe7f7cc47b64f582ea02db0c20b5`

Compile: `0 errors, 0 warnings`. `V71_V69_LONG_STRATEGY_EQUIVALENT=1`.

## V71 economic results

Same-run no-retune results:

- `XAUUSDm`: 24 trades, 10W/14L, +$6.44, PF 1.417098, DD $3.65, fast-loss share 10/14 = 71.43%.
- `EURUSDm`: 8 trades, 4W/4L, +$4.55, PF 2.060606, DD $3.30, fast-loss share 0/4. Positive months Sep +$4.42 and Apr +$3.32; negative Dec -$1.09 and Jan -$2.10; five flat months.
- `AUDUSDm`: 7 trades, 3W/4L, +$1.29, PF 1.305687, DD $2.10, fast-loss share 0/4.
- `USDJPYm`: 6 trades, 2W/4L, +$0.21, PF 1.049065, DD $3.28, fast-loss share 0/4.
- `GBPUSDm`: 19 trades, 3W/16L, -$14.43, PF 0.171166, DD $16.32, fast-loss share 0/16; zero positive months and seven negative months.

Interpretation:

- XAU's <=60-second loss pathology did **not** transfer to the four FX pairs in this sample. This supports the user's hypothesis that the XAU speed profile materially affects the fast-loss statistic.
- Direct strategy portability is **not universal**: GBPUSD is strongly rejected under the unchanged V69 geometry.
- EURUSD is the strongest FX candidate, but eight trades over nine months is still a small reused development sample. PF 2.06 is promising screening evidence, not proof of deployable edge.
- AUDUSD is weak-positive; USDJPY is effectively flat. Do not optimize all pairs simultaneously from this screen.

## V71 evidence packaging

Because the operator requested richer evidence than pasted terminal output, V71 now includes packaging-only tooling that reuses the completed tester files and does **not** rerun MT5:

- `scripts/package_v71_fx_evidence.py`;
- `runtime/v71_fx_portability_research/PACK_V71_FX_EVIDENCE_GIT_BASH.sh`;
- `tests/test_v71_fx_evidence_packaging.py`.

The packer verifies:

- source is still exactly the current V71 builder output and remains V69-LONG equivalent;
- analysis protocol is V71 FX portability;
- SHORT false / REAL false / development-only classification preserved;
- every symbol has raw `V64_DEALS.csv`, `V64_EVENTS.csv`, `V64_ENTRY_EVAL.csv`;
- raw deal-pair count equals analyzed trade count.

It exports:

- `V71_FX_EVIDENCE_FULL.zip` — all allowlisted raw text/CSV/config/source evidence for all symbols;
- `V71_FX_EVIDENCE_CORE.zip` — smaller summary/deals/events/status package;
- one full ZIP per symbol;
- a SHA256 manifest with packaging HEAD, original evidence HEAD, source SHA and every packed file hash/size.

No EX5 binary is included. Packaging does not require MT5/MetaEditor to be closed.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_EXIT_POLICY_DECISION=NO_PROMOTION`
`V71_RESEARCH=FX_PORTABILITY_DIRECT_NO_RETUNE`
`V71_TESTER_CAMPAIGN=PASS_5_SYMBOLS`
`V71_EVIDENCE_HEAD=82994371d4717ed947a0d9e8057617bf96ea8c8b`
`V71_V69_LONG_STRATEGY_EQUIVALENT=1`
`V71_XAU_FAST_LOSS_SHARE=0.714286`
`V71_FX_FAST_LOSS_SHARE=0_FOR_ALL_TESTED_FX`
`V71_EURUSD_SCREEN=BEST_FX_CANDIDATE_SMALL_SAMPLE`
`V71_GBPUSD_DIRECT_PORTABILITY=REJECTED`
`V71_FX_ENTRY_RETUNE=0`
`V71_FX_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Package the already-completed V71 raw evidence; do not rerun Strategy Tester merely to obtain ZIPs.
2. Prefer `V71_FX_EVIDENCE_FULL.zip` for deep review; if upload size is inconvenient, use the EURUSD and GBPUSD symbol ZIPs first because they provide the strongest positive/negative contrast.
3. Use raw evidence to compare EURUSD versus GBPUSD and XAU at trade/event/setup/session level before any FX-specific threshold tuning.
4. If EURUSD retains a coherent advantage after raw-path analysis, create a separate EURUSD successor research line with validation; do not mutate frozen V69.
5. Do not enable SHORT. Do not authorize REAL money.
