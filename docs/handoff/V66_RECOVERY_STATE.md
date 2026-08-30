# V66 Recovery State

Last updated: 2026-08-31.

## Repository

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`.
- Active branch: `agent/v66-post-bos-cash-zone-research`.
- V66 is Strategy Tester research only. REAL-money authorization is false.
- V66 branches from the V65 accepted-evidence lineage after the V65 evidence handoff update.
- V66 substantive code checkpoint: `cf64bcf3c4a43c4128f77506e120957c078a586e`.
- GitHub Actions quality run `#884` / run id `33328003987` completed successfully on that exact substantive checkpoint. Python compile, V66 Bash syntax, active-policy scan, full pytest, secret scan and quarantine all passed.

## Accepted V65 evidence

- Accepted source/runtime evidence head: `a45657c6a27bdd02b4de031a462ea11fb72ca7f2`.
- Evidence ZIP SHA256: `ef0f8a665d797023ab2f364a1efa862bd6ceb6274fec7ab3091d6c8a968316d5`.
- ZIP CRC passed; 82 manifest payloads + manifest; every SHA matched; no missing or extra payloads.
- LONG and SHORT MetaEditor compile both `0 errors, 0 warnings`.
- All 12 frozen Model=4 passes completed.
- V65 actual result: 2 LONG trades, 2 wins, net `+$7.04`; both in August week4. Benchmark SHORT and bearish SHORT had 0 trades.
- Both actual trades used breakout-retest M1 micro stops with planned risk `$1.15` / `$1.14`, spread `$0.26`, reached TP around `+$3.51/$3.53`, and profit-lock modification succeeded.
- Independent noise-shadow showed both actual entries reached each tested `$3/$3.5/$4` target before `$1.10/$1.35/$1.60` stops.

Micro-candidate anatomy across all 12 V65 passes:

- 205 confirmed micro candidates;
- 115 LONG, 90 SHORT;
- 202 rejected by `micro_risk_cash_cap`;
- 1 rejected by `micro_risk_spread_ratio_low`;
- 2 actual entries, both wins.
- LONG risk: min `$0.92`, median `$3.98`, mean about `$4.71`, max `$15.53`; only 3 <= `$1.25`.
- SHORT risk: min `$1.65`, median `$4.815`, mean `$5.11`, max `$12.34`; none <= `$1.25`.
- Breakout-retest: 135 candidates, median risk about `$3.90`, all three <= `$1.25` candidates.
- Pullback-sweep: 70 candidates, median risk about `$5.395`, none <= `$1.25`.

Interpretation: M1 stop ownership works, but market entry at the closed-M1 BOS price occurs too late. The current price is usually already several dollars away from structural invalidation. Do not widen the loss cap.

## V66 decision

V66 preserves V65 structural semantics but adds a second-stage execution state.

Flow:

`M15 arm -> regime/quality -> M5 context -> closed-M1 micro trigger -> fixed M1 structural stop -> second-stage arm -> wait on real ticks for cash-feasible zone -> revalidate -> preflight -> order`.

Rules:

- fixed lot `0.01`;
- planned risk `$0.85-$1.25`;
- emergency cash guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- M1 micro stop is fixed after trigger; no stop clamp;
- second-stage TTL 30 minutes from first micro arm;
- TTL is not reset;
- structural-stop breach invalidates;
- current risk above cap => wait for retracement toward stop;
- current risk too tight / broker-stop-too-close => wait for a rebound away from stop if structure has not broken;
- spread geometry can wait within TTL;
- actual entry revalidates H4/H1, selector, entry-quality, trend-quality and M5 context;
- noise shadow remains anchored to actual simulated fill.

Telemetry:

- `MICRO_ENTRY_ARM`;
- `MICRO_ENTRY_REFRESH`;
- `MICRO_ENTRY_WAIT`;
- `MICRO_ENTRY_ZONE_TOUCH`;
- `MICRO_ENTRY_INVALIDATE`;
- `MICRO_ENTRY_EXPIRE`;
- `MICRO_ENTRY_BLOCK`;
- `MICRO_ENTRY_END`.

## Frozen validation

Exactly the same samples as V65, no new screen and no PnL reselection.

August benchmark:

- 2026.08.03 -> 2026.08.08 LONG + SHORT;
- 2026.08.10 -> 2026.08.15 LONG + SHORT;
- 2026.08.17 -> 2026.08.22 LONG + SHORT;
- 2026.08.24 -> 2026.08.29 LONG + SHORT.

Frozen bearish SHORT:

- 2026.07.13 -> 2026.07.18;
- 2026.06.29 -> 2026.07.04;
- 2026.06.22 -> 2026.06.27;
- 2026.06.15 -> 2026.06.20.

Total = 12 Model=4 passes.

## V66 files

- `scripts/build_v66_post_bos_cash_zone_source.py`;
- `scripts/build_v66_post_bos_cash_zone_source_fixed.py`;
- `scripts/analyze_v66_post_bos_cash_zone.py`;
- `runtime/v66_post_bos_cash_zone/RUN_V66_POST_BOS_CASH_ZONE.py`;
- `runtime/v66_post_bos_cash_zone/RUN_V66_POST_BOS_CASH_ZONE_FIXED.py`;
- `runtime/v66_post_bos_cash_zone/START_V66_POST_BOS_CASH_ZONE_GIT_BASH.sh`;
- `tests/test_v66_post_bos_cash_zone_static.py`;
- `docs/adr/ADR-068-v66-post-bos-cash-zone-research.md`;
- `docs/handoff/V66_RECOVERY_STATE.md`.

The V66 analyzer explicitly repairs the inherited V65 summary-label defect: planned-risk label must be `$0.85-$1.25` and emergency-loss label `$1.20`.

## Safety / recovery

- Do not rerun V50-V65 merely to recover V66.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Preserve V64 and V65 evidence ZIPs.
- Do not activate REAL-money trading.
- Do not call V66 Windows PASS until both V66 experts compile `0 errors, 0 warnings` and all 12 Model=4 passes package fresh evidence.
- Do not claim the `+$6/week` KPI from the V65 two-trade sample or from static CI.

## Next recovery step

Resolve the exact latest V66 branch head and require quality success on that exact head. Then, with MT5 and MetaEditor closed, run only the V66 launcher. If Windows runtime completes, inspect bundle integrity, both compile logs, 12-pass completeness, LONG/SHORT actual metrics, stage-two arm-to-zone-touch conversion, expiry/invalidation reasons, planned vs realized loss, and noise-shadow first-hit outcomes.
