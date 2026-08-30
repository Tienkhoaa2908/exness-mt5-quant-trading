# ADR-067 — V65 micro-stop calibration research

Status: research-only, tester-only.

## Decision

V64 completed its 12-pass Model=4 protocol with valid compile/runtime packaging but produced zero broker-simulated trades. The dominant blocker was architectural: V64 evaluated cash feasibility using the older M5 structural swing before the closed-M1 micro trigger. Only a very small number of pending minutes reached the final M1 confirmation gate, so the intended microstructure refinement could not actually own the trade invalidation.

V65 changes only that sequencing and stop ownership while freezing the validation windows selected by V64.

## V64 evidence motivating V65

Accepted V64 evidence head: `762dd7ea89654c76ab9a18281787cab08ae07378`.

Observed V64 results:

- ZIP integrity and manifest passed.
- LONG, SHORT and screen experts compiled `0 errors, 0 warnings`.
- Annual screen covered 23,526 rows / 361 days.
- All 12 Model=4 passes completed.
- Actual trades: 0 in the August benchmark and 0 in the four bearish SHORT windows.
- Benchmark LONG event totals included 2,578 `stop_too_far_atr`, 2,437 `structural_risk_cash_cap`, 1,636 `m15_efficiency_weak`, and only a few dozen final micro-trigger evaluations.
- Bearish SHORT event totals included 2,093 `stop_too_far_atr`, 1,856 `structural_risk_cash_cap`, and 1,028 `m15_efficiency_weak`.
- Across all 12 passes only about 26 attempts reached final micro-trigger rejection details, and no refined broker entry was sent.

V64 also exposed a telemetry-path defect: `V64_NOISE_SHADOW.csv` used a Common-root filename instead of the milestone FILE_COMMON root. V65 fixes the path even though the inherited analyzer retains the V64 telemetry filenames for compatibility.

## V65 architecture

V65 keeps:

- XAUUSDm M15;
- fixed lot `0.01`;
- strict H4/H1 direction;
- two non-fungible archetypes: `PULLBACK_SWEEP_BOS` and `BREAKOUT_RETEST_BOS`;
- first-arm pending TTL semantics;
- entry-quality veto and HTF trend-quality gates;
- closed-bar M1 confirmation;
- actual target `+$3.50`;
- risk/spread ratio minimum `4.0`;
- tester-only / no REAL authorization.

V65 changes execution order to:

`pending setup -> current regime/quality -> M5 context confirmation -> closed-M1 micro trigger -> micro structural stop -> cash/spread feasibility -> OrderCheck -> execution`.

The M5 swing is no longer the mandatory cash stop. M5 confirms trend/structure context only.

### Micro structural invalidation

For `PULLBACK_SWEEP_BOS`:

- identify a closed-M1 sweep beyond an older liquidity range and reclaim;
- require closed-M1 displacement and micro-BOS;
- structural stop is beyond the actual swept extreme plus a small M1 ATR buffer.

For `BREAKOUT_RETEST_BOS`:

- require a closed-M1 retest of the older breakout level;
- require closed-M1 displacement and micro-BOS;
- structural stop is beyond the retest candle extreme plus a small M1 ATR buffer.

This is not stop clamping. If the naturally derived micro invalidation does not fit the cash-risk and spread geometry, the setup is rejected.

## Cash contract

- fixed lot: `0.01`;
- planned structural risk band: `$0.85-$1.25`;
- emergency cash guard: approximately `$1.20` (realized execution can exceed the threshold because of tick movement/slippage);
- actual cash target: `$3.50`;
- minimum planned-risk / spread-cash ratio: `4.0`.

## Calibration telemetry

Every confirmed micro trigger emits `MICRO_CANDIDATE` with planned risk, spread cash and risk/spread ratio before the final feasibility decision. Rejections emit `MICRO_REJECT` with the exact reason. This guarantees useful calibration evidence even if actual trade count is still zero.

Actual accepted trades continue to start the independent V64-compatible noise-shadow path anchored to `ResultPrice()`. The noise file now resolves under the V65 milestone FILE_COMMON root so it can be packaged.

## Validation protocol

V65 deliberately does not run a new PnL-dependent or PnL-independent selector. It freezes the exact windows already selected before V65 behavior is observed.

August benchmark:

- 2026.08.03 -> 2026.08.08;
- 2026.08.10 -> 2026.08.15;
- 2026.08.17 -> 2026.08.22;
- 2026.08.24 -> 2026.08.29;
- each LONG-only and SHORT-only, Model=4.

Frozen bearish SHORT windows from the accepted V64 annual screen:

- 2026.07.13 -> 2026.07.18;
- 2026.06.29 -> 2026.07.04;
- 2026.06.22 -> 2026.06.27;
- 2026.06.15 -> 2026.06.20.

Total: 12 Model=4 real-tick passes.

## Success criteria

V65 is not promoted merely for producing trades. Evidence must show materially improved expectancy and a loss profile compatible with the small-account objective. Approximately three quality trades in a week and roughly +$6 in a good week remains a research KPI, not a guarantee and not a selection criterion.

## Safety

V65 is Strategy Tester research only. `REAL` money authorization is false. No production activation is permitted from this ADR. Do not widen a structural stop merely to force a trade to fit the risk band.
