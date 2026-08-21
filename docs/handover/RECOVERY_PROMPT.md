# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Current source of truth

Branch: `agent/v42-baseline-router-exact-mt5`.
Base: V41 implementation `60cd93ad9eefd07447f65b2e6909a20edf60f3ae`.
Never `git clean`; accepted runtime evidence, compiled EA artifacts, checkpoints, state and `.venv` may be untracked.

## Safety

REAL-MONEY LIVE TRADING forbidden. Research risk <=1.00%/trade. No Martingale/grid/doubling. Strategy Tester only; `AllowLiveTrading=0`, `AllowDllImport=0`, Model=0. No native/external broker orders.

## Exact baseline / target

Accepted exact control `adaptive_ewma_hl8_thr0`, USD40 continuous, 2025-08-01 -> 2026-08-01:

- $40 -> $107.432645;
- total return +168.5816%;
- geometric/month 8.58163%;
- max DD 9.9038%;
- 563 trades;
- AvgR 0.214608R;
- PF 1.500756.

15%/month would imply about $214.01 after 12 months from $40. Exact gap remains 6.41837pp/month.
Hard reproduction vectors in `scripts/analyze_v42_baseline_router_mt5.py` must not be weakened.

## V42 exact result — CLOSED HOLD

The exact Strategy Tester run completed successfully on 2026-08-21 from the verified compiled V42 EA. Control reproduction PASS.

Best V42 challenger by ending equity:

`v42_cp_fast5_slow20_switch15m`

- end $106.387574;
- geometric/month 8.493214%;
- DD 9.6614%;
- 507 trades;
- AvgR 0.243553R;
- PF 1.534444;
- turnover -3.01% vs control;
- beats control 6/12 months;
- end equity -$1.045071 vs control;
- geo -0.08842pp/month vs control.

`eligible_to_freeze_for_fresh_holdout=[]`.

Best V42 risk-efficiency arm was `v42_hl8_thr0p05_switch15m`: end $103.358584, 8.232381%/month, DD 7.9188%, 465 trades, AvgR 0.266639R, PF 1.538075, return/DD 20.0026. Keep as research insight only; it is not a return upgrade.

Historical exact comparators remain hypotheses, not promoted policies:

- `adaptive_ewma_hl8_thr0p05`: $111.285257, 8.900900%/month, DD 10.4368%;
- `adaptive_ewma_hl10_thr0p05`: $110.025682, 8.797648%/month, DD 9.8587%;
- `adaptive_ewma_hl12_thr0p05`: $107.797276, 8.612293%/month;
- `adaptive_cp_fast5_slow20_thr0p30`: $102.206843, 8.131360%/month.

Do not retune V42 switching delays on the same 12-month development window.

## Accepted V42 evidence identity

Successful run evidence says:

- head `9ddd9a99c708e66f62f0eae7bd85750ad32f2f13`;
- branch `agent/v42-baseline-router-exact-mt5`;
- V42 source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`;
- compiler `Result: 0 errors, 0 warnings`;
- V38 parent ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`;
- V38 parent source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- V34 tape SHA `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`;
- frozen state SHA `5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`.

User supplied a RAR containing the completed output after ZIP packaging failed. RAR outer SHA256:

`3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`

The bundle contains 18 manifest members and all 18 hashes verify.

## Packaging defect — diagnosed and fixed

MT5 and analysis completed. Final ZIP creation failed only because Git Bash/MSYS `sha256sum` generated manifest rows as:

`<64hex> *filename`

while the inline Python packager incorrectly assumed:

`<64hex><two spaces>filename`

and executed `line.split('  ',1)`.

This is packaging-only evidence; do not rerun MT5 to repair it.

Canonical fix:

- `scripts/package_research_bundle_portable.py` computes SHA256 in Python and writes a canonical platform-independent `<hash><two spaces>filename` manifest;
- `runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh` packages already completed V42 output only and never launches MetaEditor or MT5;
- bootstrap may call package-only recovery only when completed V42 evidence, analyzer JSON, monthly summary, trades and tester manifest already exist. It must not mask earlier runtime/research failures.

## Historical runner defects not to reintroduce

- Do not rebuild V42 parent through V30 -> V34 -> V38; use accepted V38 ZIP as immutable parent.
- Explicit UTF-8 only; Windows CP1252 caused a prior test-harness failure.
- No runtime shell patcher/self-modifying runner.
- No `set +e` under a global `ERR` trap; capture Windows rc in conditional context.
- Compile acceptance is source hash + final 0/0 log + EX5, not MetaEditor launcher rc.
- MT5 completion is a new `LATEST` run plus complete manifested outputs, not terminal rc alone.

## Required QA invariants

Preserve:

- exact V38 control reproduction;
- accepted V38 ZIP SHA/CRC/source extraction;
- no-order/tester safety lint;
- pinned Python/dependencies;
- explicit UTF-8;
- no `git clean`;
- one bundle with canonical internal SHA256 manifest and ZIP CRC verification;
- risk <=1.00%/trade;
- no live authorization.

## Next research direction

V42 switching hysteresis is rejected as a return upgrade. Keep `adaptive_ewma_hl8_thr0` as return control.

The next baseline cycle should investigate why thresholded EWMA variants (`hl8_thr0p05`, `hl10_thr0p05`) show modest exact return improvements while switch hysteresis improves trade quality/DD but sacrifices too much participation. Any new mechanism must be preregistered and exact-MT5 adjudicated; do not sweep V42 delay values on the same sample.
