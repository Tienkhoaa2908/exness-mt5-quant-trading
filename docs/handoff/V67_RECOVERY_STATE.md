# V67 Recovery State

Last updated: 2026-08-31.

## Repository / safety

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`.
- Active branch: `agent/v67-post-zone-reclaim-quality-research`.
- V67 is Strategy Tester research only. REAL-money authorization is false.
- Do not `git clean`.
- Do not `stash pop` while MT5/tester work is active.
- Do not rerun older milestones merely to recover V67.

## Accepted V66 evidence

Accepted V66 runtime/evidence head: `55ac20678776696c13fbdd714025b7302e579d71`.

Accepted V66 evidence ZIP SHA256: `4b8e85a35255216ecb14e7d87b01c2091c995158b77f341ab12d36ef753eb904`.

Integrity / protocol:

- ZIP CRC passed;
- all manifest payload hashes matched and no payload was missing or extra;
- LONG and SHORT MetaEditor compile both `0 errors, 0 warnings`;
- all 12 frozen Model=4 passes completed.

V66 benchmark LONG:

- 29 trades;
- 11 wins / 18 losses;
- net `+$8.52`;
- PF about `1.37`;
- average win about `+$2.85`;
- average loss about `-$1.27`;
- 16 of 18 losing trades exited within 60 seconds.

V66 bearish SHORT:

- 28 trades;
- 5 wins / 23 losses;
- net `-$14.08`;
- PF about `0.52`;
- average loss about `-$1.28`;
- 16 of 23 losing trades exited within 60 seconds.

V66 stage-two conversion:

- 99 micro-entry arms;
- 57 zone touches / orders;
- 37 expiries;
- 5 structural/context invalidations.

Interpretation: the post-BOS retracement concept successfully restored execution, but first cash-zone touch was still treated as an immediate order trigger. Fast stop-outs show that local sweep/rejection often continued after the first touch. SHORT execution was restored but remained unprofitable, so LONG and SHORT must remain independent evaluation lanes.

## Revised research objective

There is no fixed weekly trade-count promotion quota and no fixed weekly dollar-profit promotion quota.

The objective is:

- stable positive expectancy;
- repeatable profitability across samples;
- controlled drawdown and realized losses;
- fewer very-fast losing trades;
- technically defensible causal entry geometry;
- enough opportunity to produce useful returns without forcing frequency.

Trade count and weekly dollars remain diagnostics, not hard external promotion targets.

## V67 decision

V67 preserves the V66 M1 structural stop and post-BOS cash-zone stage, but first zone touch can never send an order.

Flow:

`M15 setup -> regime/quality -> M5 context -> closed-M1 BOS -> freeze M1 structural stop -> zone touch -> deeper zone penetration -> closed-M1 rejection/reclaim -> cash/spread feasibility -> context revalidation -> OrderCheck -> order`.

Key rules:

- fixed lot `0.01`;
- planned risk band `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20` as best effort, not a guaranteed realized cap;
- target `+$3.50`;
- minimum risk/spread ratio `4.0`;
- stage-two TTL stays 30 minutes from first micro arm and is not reset;
- deeper-penetration threshold is prospective risk `<= $0.92` while structure remains valid;
- first zone touch logs and returns with no order;
- a closed M1 reclaim is required after penetration;
- a new adverse extreme after reclaim invalidates that confirmation and requires a fresh reclaim;
- confirmation validity is five minutes;
- structural stop remains fixed and is never clamped;
- actual entry revalidates H4/H1, current selector, entry quality, trend quality and M5 context;
- actual-fill noise shadow remains enabled.

Closed-M1 reclaim contract:

- body >= `0.18 × ATR14`;
- body/range >= `0.45`;
- directional close-location >= `0.65`;
- progress beyond prior close by `0.02 × ATR`;
- recovery from adverse zone extreme >= `0.12 × ATR`.

These are preregistered V67 calibration thresholds. They are not claimed as optimal and must be judged only by fresh Model=4 evidence.

## Frozen V67 validation

Exactly the same windows as accepted V66; no new screen and no PnL reselection.

Benchmark, direction-isolated Model=4:

- week1: 2026.08.03 -> 2026.08.08 LONG + SHORT;
- week2: 2026.08.10 -> 2026.08.15 LONG + SHORT;
- week3: 2026.08.17 -> 2026.08.22 LONG + SHORT;
- week4: 2026.08.24 -> 2026.08.29 LONG + SHORT.

Frozen bearish SHORT Model=4:

- 2026.07.13 -> 2026.07.18;
- 2026.06.29 -> 2026.07.04;
- 2026.06.22 -> 2026.06.27;
- 2026.06.15 -> 2026.06.20.

Total = 12 Model=4 passes.

## V67 observability

Important events:

- `MICRO_ENTRY_ARM`;
- `MICRO_ENTRY_ZONE_TOUCH`;
- `MICRO_ENTRY_PENETRATION`;
- `POST_ZONE_CONFIRM_WAIT`;
- `POST_ZONE_REVERSAL_CONFIRM`;
- `POST_ZONE_CONFIRM_RESET`;
- `POST_ZONE_ENTRY_READY`;
- `MICRO_ENTRY_INVALIDATE`;
- `MICRO_ENTRY_EXPIRE`;
- `REFINED_ENTRY`;
- `NOISE_SHADOW`.

The analyzer must report stage conversion, consistency by lane, realized loss statistics, and losing-trade duration counts within 15/30/60 seconds. Historical frequency/profit goal counters inherited from the V64 analyzer are retained only as legacy diagnostics and are explicitly not promotion gates.

## V67 files

- `scripts/build_v67_post_zone_reclaim_quality_source.py`;
- `scripts/analyze_v67_post_zone_reclaim_quality.py`;
- `runtime/v67_post_zone_reclaim_quality/RUN_V67_POST_ZONE_RECLAIM_QUALITY.py`;
- `runtime/v67_post_zone_reclaim_quality/START_V67_POST_ZONE_RECLAIM_QUALITY_GIT_BASH.sh`;
- `tests/test_v67_post_zone_reclaim_quality_static.py`;
- `docs/adr/ADR-069-v67-post-zone-reclaim-quality-research.md`;
- `docs/handoff/V67_RECOVERY_STATE.md`.

## Promotion interpretation

Do not promote a direction because the opposite lane is profitable. LONG and SHORT are assessed independently.

Do not promote from static CI. Windows MetaEditor compile and Model=4 runtime evidence are required.

Prefer evidence of positive expectancy, multiple positive periods, lower fast-loss incidence, controlled realized losses and acceptable drawdown. Frequency is allowed to rise or fall if those technical/economic properties improve.

## Next recovery step

Require GitHub Actions success on the exact final V67 head. Then, with MT5 and MetaEditor closed, run only the V67 launcher. If runtime completes, inspect ZIP integrity, both compile logs, all 12 pass directories, stage conversion, lane PnL/PF, weekly consistency, realized losses, short-duration losing trades and noise-shadow outcomes before deciding any next change.
