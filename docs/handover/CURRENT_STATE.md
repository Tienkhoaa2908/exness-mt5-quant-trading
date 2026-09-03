# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 16:40 (+07)

## Authority / safety

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active research branch: `agent/v72-eurusd-independent-validation`.

Always resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI before acting.

SHORT disabled. SHORT remains rejected for activation. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.

Frozen contract: XAUUSDm M15, LONG only, lot 0.01, planned risk about $0.85-$1.10, emergency guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready, fixed stop, inherited +$2 -> about +$1 profit ratchet.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`. Sep 2025-May 2026 is development-only. Actual DEMO execution transport is proven PASS.

## Settled research before V71

- XAU live no-trade window was bearish `short_edge`; LONG-only isolation was working, not broker failure.
- All-bar coverage rejected global LONG starvation.
- Downstream LONG funnel localized dominant attrition upstream of final separation; hard structural failure was the largest terminal family.
- V70 true-position telemetry replaced invalid post-exit `V64_NOISE_SHADOW` MFE attribution.
- V70 same-run baseline +$6.44 versus accepted V69 +$7.14 was one -$0.70 swap drift with identical exit time/price/gross profit/reason.
- V70 TIERED exit shadow improved reused development economics by only +$0.68 and was not promoted.

## V71 FX direct-portability campaign — completed

V71 kept frozen V69 LONG decision/entry/real-exit semantics exactly after metadata normalization. No symbol-specific retune was applied.

Campaign: XAUUSDm control plus EURUSDm, GBPUSDm, USDJPYm and AUDUSDm; M15 real ticks; `2025.09.01 -> 2026.06.01`; lot 0.01; risk $0.85-$1.10; emergency $1.20; target $3.50; separation $1.30; no SHORT; no REAL.

Tester evidence HEAD: `82994371d4717ed947a0d9e8057617bf96ea8c8b`.
Generated source SHA256: `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`.
EX5 SHA256: `69896c6b330c6dd4bbb13acf7ee27ea1efccbe7f7cc47b64f582ea02db0c20b5`.
Compile 0/0. `V71_V69_LONG_STRATEGY_EQUIVALENT=1`.

Same-run results:

- XAUUSDm: 24 trades, 10W/14L, +$6.44, PF 1.417098, DD $3.65.
- EURUSDm: 8 trades, 4W/4L, +$4.55, PF 2.060606, DD $3.30.
- AUDUSDm: 7 trades, 3W/4L, +$1.29, PF 1.305687, DD $2.10.
- USDJPYm: 6 trades, 2W/4L, +$0.21, PF 1.049065, DD $3.28.
- GBPUSDm: 19 trades, 3W/16L, -$14.43, PF 0.171166, DD $16.32.

## V71 raw EUR/GBP/XAU review — completed

The strongest raw contrast is post-entry follow-through, not loss-dollar geometry:

- EUR average loss `-$1.0725`, GBP average loss `-$1.088125`;
- EUR average winner `+$2.21`, GBP average winner `+$0.9933`;
- EUR reached inherited `PROFIT_LOCK` in 4/8 trades and produced two full target exits;
- GBP reached `PROFIT_LOCK` only 3/19 times and produced zero full target exits.

The <=60-second statistic was too narrow across instruments. GBP had 0/16 losses <=60 seconds but 8/16 <=15 minutes; EUR had 0/4 losses <=15 minutes; XAU remained the ultra-fast case at 10/14 <=60 seconds.

Both `BREAKOUT_RETEST_BOS` and `PULLBACK_SWEEP_BOS` occur around winners and losers. No archetype pruning or naive time-of-day filter is justified from the small FX sample.

## V72 EURUSD independent validation — tester completed, evidence recovery pending

Branch: `agent/v72-eurusd-independent-validation`.

Preregistered contract remains unchanged:

- `EURUSDm`, M15, real ticks;
- exactly one intended tester pass;
- `2024.09.01 -> 2025.09.01`;
- exact V71 source builder, source SHA256 pinned to `32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`;
- same V69/V71 LONG entry and exit semantics;
- no entry retune, no exit retune, no SHORT, no REAL;
- <8 trades -> `INSUFFICIENT_SAMPLE`;
- otherwise PASS requires net >0, PF >=1.25, max realized DD <=$5.00, >=2 positive months and ex-best-trade net >0;
- otherwise `FAIL`.

The operator ran the V72 tester at HEAD `e22da3f4ec24840db4eb735a14a3725921e944a1`. Build/compile passed with the expected pinned source SHA and MT5 returned `rc=0`, so the tester process completed. The runner then failed before analysis with:

`missing V64_ENTRY_EVAL.csv; root_listing=`

This is a harness/telemetry-path defect, not strategy evidence. Root cause is exact and deterministic:

- the exact pinned V71 source still hardcodes FILE_COMMON root `mt5_quant\\v71_fx_portability`;
- the original V72 runner incorrectly changed the reused V64 harness to wait under `mt5_quant\\v72_eurusd_independent_validation`;
- therefore MT5 wrote to the V71 source root while the Python collector inspected an empty V72 root.

Fix prepared on V72:

- the collector now uses `SOURCE_COMMON_DIR = "v71_fx_portability"`, matching the pinned source without changing source SHA or strategy semantics;
- before launching any new tester pass, it checks the existing V71 telemetry root for the already-completed V72 run;
- recovery is fail-closed: primary CSVs must exist and all timestamped rows must fall inside the preregistered `2024.09.01 -> 2025.09.01` period;
- valid evidence is copied/analyzed with `V72_EURUSD_TEST_RERUN=0`;
- stale V71 Sep-2025+ evidence is rejected and only then would a fresh tester pass be run.

No V72 economic classification has been recorded yet because the raw result has not been recovered/analyzed after the harness fix. Acceptance thresholds remain unchanged.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V70_EXIT_POLICY_DECISION=NO_PROMOTION`
`V71_RESEARCH=FX_PORTABILITY_DIRECT_NO_RETUNE`
`V71_TESTER_CAMPAIGN=PASS_5_SYMBOLS`
`V71_EURUSD_SCREEN=BEST_FX_CANDIDATE_SMALL_SAMPLE`
`V71_GBPUSD_DIRECT_PORTABILITY=REJECTED`
`V71_RAW_CONTRAST=GBP_POST_ENTRY_FOLLOW_THROUGH_FAILURE`
`V72_RESEARCH=EURUSD_UNTOUCHED_TEMPORAL_VALIDATION`
`V72_FIRST_TESTER_PROCESS=COMPLETED_RC0`
`V72_EVIDENCE_COLLECTION=BLOCKED_BY_TELEMETRY_ROOT_MISMATCH`
`V72_ECONOMIC_CLASSIFICATION=PENDING_RECOVERY`
`V72_EURUSD_ENTRY_RETUNE=0`
`V72_EURUSD_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Run the corrected V72 launcher once.
2. It must first attempt to recover the already-completed tester evidence from `mt5_quant\\v71_fx_portability`; do not rerun if the recovered timestamps match the preregistered period.
3. If recovery is valid, analyze immediately and apply the preregistered PASS/FAIL/INSUFFICIENT_SAMPLE gate unchanged.
4. If the source root contains stale/mixed evidence and fails the date guard, archive it and perform one fresh V72 tester pass automatically.
5. PASS -> proceed to a separate prospective DEMO EURUSD gate. FAIL -> reject the unchanged candidate. INSUFFICIENT_SAMPLE -> extend only under a new predeclared evidence rule.
6. Do not enable SHORT. Do not authorize REAL money.
