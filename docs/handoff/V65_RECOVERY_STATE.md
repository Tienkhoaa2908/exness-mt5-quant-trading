# V65 Recovery State

Last updated: 2026-08-31.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active branch: `agent/v65-micro-stop-calibration-research`
- V65 is Strategy Tester research only. REAL-money authorization is false.
- Base checkpoint is accepted V64 evidence head `762dd7ea89654c76ab9a18281787cab08ae07378`.
- Accepted V65 source/runtime evidence head: `a45657c6a27bdd02b4de031a462ea11fb72ca7f2`.
- GitHub Actions quality run `#871` / run id `33326065203` completed successfully on that exact head.

## Accepted V64 evidence

Uploaded V64 evidence ZIP SHA256: `346a7e8a87980cb2e967dc4e713b8746576c165e1706e5dcf233daef7de74d22`.

- ZIP CRC passed; 79 manifest payloads + manifest; every manifest SHA256 matched.
- LONG / SHORT / SCREEN MetaEditor compile all `0 errors, 0 warnings`.
- Annual screen: 23,526 rows / 361-day span.
- 12 Model=4 passes completed.
- Actual result: 0 broker-simulated trades.
- Main defect: old M5 structural swing owned the cash stop before the M1 trigger, so thousands of attempts died on structural risk before microstructure could define invalidation.
- `V64_NOISE_SHADOW.csv` also used the wrong Common-root path; no PnL impact because V64 had zero actual trades.

## V65 decision / implementation

V65 changed stop ownership without changing the research sample:

`pending -> regime/quality -> M5 context -> closed-M1 trigger -> M1 micro structural stop -> risk/spread gate -> preflight -> order`.

- M5 remains context/structure only.
- Pullback-sweep stop is beyond the actual swept M1 extreme + ATR buffer.
- Breakout-retest stop is beyond the M1 retest-candle extreme + ATR buffer.
- No stop clamp.
- fixed lot `0.01`;
- planned risk `$0.85-$1.25`;
- emergency cash guard about `$1.20`;
- actual target `+$3.50`;
- minimum risk/spread ratio `4.0`.
- Every confirmed micro trigger emits `MICRO_CANDIDATE`; rejected candidates emit `MICRO_REJECT`.
- Noise shadow is anchored to actual simulated fill and written under the milestone FILE_COMMON root.

## Frozen V65 validation windows

No PnL reselection.

August benchmark, each LONG-only and SHORT-only:

- week1: 2026.08.03 -> 2026.08.08;
- week2: 2026.08.10 -> 2026.08.15;
- week3: 2026.08.17 -> 2026.08.22;
- week4: 2026.08.24 -> 2026.08.29.

Frozen bearish SHORT windows from accepted V64 screen:

- bearish1: 2026.07.13 -> 2026.07.18;
- bearish2: 2026.06.29 -> 2026.07.04;
- bearish3: 2026.06.22 -> 2026.06.27;
- bearish4: 2026.06.15 -> 2026.06.20.

Total: 12 Model=4 passes.

## Accepted V65 runtime evidence

Uploaded V65 evidence ZIP SHA256: `ef0f8a665d797023ab2f364a1efa862bd6ceb6274fec7ab3091d6c8a968316d5`.

Integrity:

- ZIP CRC passed;
- 82 manifest payloads + manifest;
- every manifest SHA256 matched;
- no missing or extra payloads;
- branch/head matched `agent/v65-micro-stop-calibration-research` / `a45657c6a27bdd02b4de031a462ea11fb72ca7f2`.

Runtime:

- LONG MetaEditor compile: `0 errors, 0 warnings`;
- SHORT MetaEditor compile: `0 errors, 0 warnings`;
- all 12 frozen Model=4 passes completed;
- noise-shadow CSV is now present in every pass directory.

Actual broker-simulated result:

- August benchmark LONG: 2 trades, 2 wins, 0 losses, net `+$7.04`, average win `+$3.52`;
- August benchmark SHORT: 0 trades;
- August combined direction-isolated diagnostic sum: 2 trades, 2 wins, net `+$7.04`;
- both trades occurred in week4 LONG; week4 net `+$7.04`;
- bearish SHORT validation: 0 trades.

The two actual LONG trades:

- 2026.08.24 22:45:00: planned micro risk `$1.15`, spread `$0.26`, risk/spread `4.4231`; fill 4661.866; TP exit at 4665.380 for `+$3.51`; profit lock modified after floating profit about `$2.05`.
- 2026.08.25 22:13:01: planned micro risk `$1.14`, spread `$0.26`, risk/spread `4.3846`; fill 4662.417; TP exit at 4665.947 for `+$3.53`; profit lock modified after floating profit about `$2.01`.

Noise-shadow for both actual entries:

- every tested stop/target combination (`$1.10/$1.35/$1.60` x `$3/$3.5/$4`) reached target before its tested stop;
- no `stop_then_later_target` case;
- the actual `$3.50` target was therefore not obviously too ambitious for these two entries.

## V65 micro-candidate anatomy

Across all 12 passes:

- `PENDING_ARM=92`;
- `MICRO_CANDIDATE=205`;
- `MICRO_REJECT=203`;
- `REFINED_ENTRY=2`;
- both refined entries were sent and both won.

Candidate directions:

- LONG: 115 confirmed micro candidates; minimum risk `$0.92`, median `$3.98`, mean about `$4.71`, maximum `$15.53`; only 3 were at or below `$1.25`.
- SHORT: 90 confirmed micro candidates; minimum risk `$1.65`, median `$4.815`, mean `$5.11`, maximum `$12.34`; none were at or below `$1.25`.

Candidate archetypes:

- `BREAKOUT_RETEST_BOS`: 135 candidates; median planned risk about `$3.90`; all 3 candidates at or below `$1.25` were this archetype.
- `PULLBACK_SWEEP_BOS`: 70 candidates; median planned risk about `$5.395`; no candidate fit the `$1.25` cap.

Rejects:

- `micro_risk_cash_cap=202`;
- `micro_risk_spread_ratio_low=1` (candidate risk `$0.92` / spread `$0.26` = ratio `3.54`).

Interpretation:

V65 proved that moving stop ownership from M5 to M1 was directionally correct: it produced 205 real confirmed micro candidates and two clean profitable executions. The remaining bottleneck is no longer absence of microstructure. It is execution timing. The engine enters at the closed-M1 BOS market price, after price has already moved far from the micro invalidation. This leaves 98.5% of candidates above the `$1.25` cash-risk cap and all 90 SHORT candidates infeasible.

Do **not** respond by widening the loss budget. The next experiment must preserve the micro structural stop and wait for a post-BOS retracement back into a cash-feasible entry zone.

## Analyzer labeling defect

`V65_SUMMARY.txt` still prints inherited V64 labels `PLANNED_RISK_BAND_CASH=0.85,1.20` and `EMERGENCY_LOSS_CASH=1.15` even though the generated experts, protocol and evidence contract are `$0.85-$1.25` and `$1.20`. This is a summary/analyzer labeling defect only; generated MQL evidence confirms the actual V65 runtime inputs are max planned risk `$1.25` and emergency guard `$1.20`. Fix this in the next analyzer layer; do not reinterpret V65 trades using the stale labels.

## Next technical decision

V66 should use post-BOS cash-zone execution while preserving V65 structure and frozen samples:

1. A confirmed M1 trigger arms a second-stage micro setup with a fixed structural stop and first-arm TTL; it does not market-enter immediately when current risk is above the cap.
2. Compute a cash-feasible price zone for that fixed stop. Effective lower risk is `max($0.85, 4 * current spread cash)` and upper risk remains `$1.25`.
3. Wait on real ticks for price to retrace into that zone. LONG waits downward toward the fixed micro stop; SHORT waits upward toward it.
4. Cancel if the structural stop is invalidated, HTF direction flips, the setup expires, or price overshoots the safe zone toward the stop without a valid entry.
5. Do not reset the micro-stage TTL on repeated candidates. A fresher same-direction micro stop may replace the existing stop only if it improves geometry without loosening structural invalidation, while preserving the first-arm time.
6. Add `MICRO_ENTRY_ARM`, `MICRO_ENTRY_ZONE_TOUCH`, `MICRO_ENTRY_EXPIRE`, `MICRO_ENTRY_INVALIDATE`, `MICRO_ENTRY_OVERSHOOT` telemetry so zero-trade outcomes remain diagnosable.
7. Keep fixed `0.01`, target `+$3.50`, loss cap semantics, H4/H1 quality filters and the same 12 frozen Model=4 windows for apples-to-apples comparison.

## Safety / recovery

- Do not rerun V50-V64 merely to recover V65/V66.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Preserve accepted V64 and V65 evidence ZIPs as immutable evidence.
- Do not activate REAL-money trading.
- Do not claim the `+$6/week` research KPI is achieved from one profitable week or two trades.
- Direction-isolated sums are diagnostics, not concurrent portfolio equity.

## Next recovery step

Use accepted V65 evidence head `a45657c6a27bdd02b4de031a462ea11fb72ca7f2` as the source/runtime checkpoint. Implement V66 post-BOS retracement-to-cash-zone execution on a new research branch, retain the exact same 12 windows, add analyzer contract fixes and stage-two telemetry, require exact-head GitHub Actions success, then obtain fresh Windows MetaEditor + Model=4 evidence before making any profitability claim.
