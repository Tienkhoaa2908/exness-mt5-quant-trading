# V65 Recovery State

Last updated: 2026-08-31.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active branch: `agent/v65-micro-stop-calibration-research`
- V65 is Strategy Tester research only. REAL-money authorization is false.
- Base checkpoint is accepted V64 evidence head `762dd7ea89654c76ab9a18281787cab08ae07378`.
- V65 substantive/static checkpoint: `a6fe2e23cd1b6253d48f4fc1d66ea815b6c19446`.
- GitHub Actions quality run `#870` / run id `33325985091` completed successfully on that exact substantive checkpoint. Python compile, V65 Bash syntax, active-policy scan, full pytest, secret scan and V29 quarantine all passed.
- Any later documentation-only head must itself pass quality before being used for Windows runtime.

## Accepted V64 evidence

Uploaded V64 evidence ZIP SHA256: `346a7e8a87980cb2e967dc4e713b8746576c165e1706e5dcf233daef7de74d22`.

Integrity:

- ZIP CRC passed;
- 79 manifest payloads + manifest;
- every manifest SHA256 matched;
- no missing or extra payloads;
- evidence branch/head matched `agent/v64-microstructure-trigger-shadow-research` / `762dd7ea89654c76ab9a18281787cab08ae07378`.

Runtime:

- LONG compile: 0 errors, 0 warnings;
- SHORT compile: 0 errors, 0 warnings;
- SCREEN compile: 0 errors, 0 warnings;
- annual screen: 23,526 rows, 361-day span;
- 4 fixed August benchmark weeks completed LONG-only and SHORT-only;
- 4 bearish SHORT windows completed;
- total Model=4 passes: 12.

V64 actual result: 0 broker-simulated trades in all 12 passes.

Important event anatomy:

- August benchmark LONG: 48 pending arms, 5,166 risk-zone waits, 1,645 entry vetoes, 229 refine waits, 0 refined entries.
- Dominant benchmark LONG blockers: `stop_too_far_atr=2578`, `structural_risk_cash_cap=2437`, `m15_efficiency_weak=1636`.
- Bearish SHORT: 41 pending arms, 4,038 risk-zone waits, 1,196 entry vetoes, 121 refine waits, 0 refined entries.
- Dominant bearish SHORT blockers: `stop_too_far_atr=2093`, `structural_risk_cash_cap=1856`, `m15_efficiency_weak=1028`.
- Across all 12 passes only about 26 attempts reached the final micro-trigger detail stage; none passed to execution.

Interpretation: V64 evaluated old M5/M15 structural-stop cash feasibility before the closed-M1 micro trigger. This defeated the intended entry-location refinement because an old M5 swing remained the mandatory stop even after a valid micro setup was being sought.

V64 telemetry defect also found: `V64_NOISE_SHADOW.csv` was declared as a Common-root filename instead of under the milestone FILE_COMMON root. The accepted ZIP therefore contained no per-pass noise-shadow CSV. Because there were zero actual trades this does not affect V64 PnL, but it would have prevented the intended shadow evidence from being packaged if trades existed.

## V65 decision

V65 changes stop ownership, not the research sample.

Execution order:

`pending -> regime/quality -> M5 context -> closed-M1 trigger -> M1 micro structural stop -> risk/spread gate -> preflight -> order`.

M5 remains a context/structure confirmation. It no longer owns the mandatory cash stop.

Micro stops:

- pullback sweep: beyond the actual swept M1 extreme + ATR buffer;
- breakout retest: beyond the M1 retest candle extreme + ATR buffer;
- no stop clamping to the risk budget.

Cash contract:

- fixed lot `0.01`;
- planned risk `$0.85-$1.25`;
- emergency cash guard about `$1.20`;
- target `+$3.50`;
- minimum risk/spread ratio `4.0`.

Telemetry:

- every confirmed micro trigger emits `MICRO_CANDIDATE` with risk/spread diagnostics;
- rejected candidates emit `MICRO_REJECT`;
- accepted trades retain independent actual-fill noise shadow;
- noise CSV path is fixed to the V65 FILE_COMMON root.

## Frozen V65 validation windows

No new selection is performed after V65 behavior is known.

Benchmark Model=4 direction-isolated:

- week1: 2026.08.03 -> 2026.08.08;
- week2: 2026.08.10 -> 2026.08.15;
- week3: 2026.08.17 -> 2026.08.22;
- week4: 2026.08.24 -> 2026.08.29;
- each LONG-only and SHORT-only = 8 passes.

Bearish SHORT Model=4 windows frozen from accepted V64 PnL-independent screen:

- bearish1: 2026.07.13 -> 2026.07.18;
- bearish2: 2026.06.29 -> 2026.07.04;
- bearish3: 2026.06.22 -> 2026.06.27;
- bearish4: 2026.06.15 -> 2026.06.20.

Total V65 = 12 Model=4 passes.

## V65 implementation layers

- `scripts/build_v65_micro_stop_calibration_source.py`: strategy transform and M1 micro-stop semantics.
- `scripts/build_v65_micro_stop_calibration_source_fixed.py`: owning fixed layer that normalizes all inherited V64 FILE_COMMON root occurrences and then requires no stale root remains.
- `runtime/v65_micro_stop_calibration/RUN_V65_MICRO_STOP_CALIBRATION.py`: frozen-window 12-pass protocol, analysis and packaging.
- `runtime/v65_micro_stop_calibration/RUN_V65_MICRO_STOP_CALIBRATION_FIXED.py`: routes the runtime through the fixed builder.
- `runtime/v65_micro_stop_calibration/START_V65_MICRO_STOP_CALIBRATION_GIT_BASH.sh`: branch-pinned local gate and runner launcher.
- `tests/test_v65_micro_stop_calibration_static.py`: generated LONG/SHORT sequencing, structural-stop/no-clamp, FILE_COMMON/noise path, frozen-window, fixed-layer and launcher regressions.
- `docs/adr/ADR-067-v65-micro-stop-calibration-research.md`.
- `docs/handoff/V65_RECOVERY_STATE.md`.
- `.github/workflows/quality.yml` includes V65 runtime Python compile, V65 launcher Bash syntax and V65 active quarantine coverage.

The first V65 CI attempt failed only in static glue: the inherited V64 root occurred six times while the first builder attempted a one-occurrence replacement, and one test lowercased source text before splitting on uppercase markers. The fixed builder normalizes all root occurrences; the test now reads the correct fixed layers. No strategy/runtime evidence was produced during those failed CI attempts.

## Safety / recovery

- Do not rerun V50-V64 merely to recover V65.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Do not overwrite accepted V64 evidence.
- Do not activate REAL-money trading.
- Do not call V65 Windows PASS until both generated V65 experts compile 0 errors / 0 warnings and all 12 Model=4 passes package fresh evidence.
- Do not claim the +$6/week KPI is achieved unless fresh V65 evidence shows it.
- Direction-isolated sums are diagnostics, not concurrent portfolio equity.

## Next recovery step

Resolve the exact latest branch head and require GitHub Actions quality success on that exact head. Then run only the V65 launcher with MT5 and MetaEditor closed. If runtime completes, inspect ZIP integrity, both compile logs, all 12 fixed-window Model=4 passes, actual trades, `MICRO_CANDIDATE` / `MICRO_REJECT` distributions, realized losses and inherited noise-shadow evidence.
