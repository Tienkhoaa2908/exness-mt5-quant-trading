# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current accepted state

V44 base commit: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.
V45 source/recovery commit: `1566a0bf0988fbab4395f5a604a0d428f4f95b97`.
V45 accepted evidence ZIP SHA256: `490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`.
V45 formal result: `HOLD`.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v45_multiyear_single_run_validation_results.md`
3. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
4. `docs/research/v45_clean_clone_recovery.md`

Never `git clean`.

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Research risk <=1.00%/trade. No Martingale/grid/doubling. Strategy Tester only with `AllowLiveTrading=0`, `AllowDllImport=0`, no native/external broker orders. `LIVE_AUTHORIZED=0`.

## V45 accepted result

One exact MT5 run XAUUSDm M15, 2022-01-01 -> 2026-08-01, cold-start, 55 raw months, first six warm-up, 49 evaluation months.

Primary `adaptive_ewma_hl10_thr0p05` after warm-up:
- +105.786638% compounded;
- +1.483694% geometric/month;
- max reported MTM DD 56.2976%;
- PF 1.132725;
- 20/49 positive months;
- worst full year -25.749354%;
- rolling-12m positive 23/38; worst -30.690805%;
- -0.05R/trade stress remains positive.

Full cold-start path $40 -> $63.863453 over 55 months. No frozen candidate passes the preregistered V45 gate. `ready_candidates=[]`.

The strong recent regime remains visible: HL10p05 2025 +70.36%, 2026 Jan-Jul +85.52%, and 2025-08 -> 2026-07 approximately +138.29%. But 2022 and 2024 are structurally weak, so V44's one-year performance is not regime-agnostic.

## Structural diagnosis / V46 hypothesis

Current adaptive router applies `adaptive_min_score=0.05` to the selected expert only. It can still trade when most of the five shadow experts are unhealthy.

V45 diagnostic reconstruction indicates a causal ensemble-breadth gate is the preferred next hypothesis. Primary V46 rule is preregistered as:

`HL10p05 router AND at least 4 of 5 HL10 shadow-expert EWMA scores >=0.05 before opening new risk`.

Breadth3 and breadth5 may be sensitivity comparators only. Do not promote them by same-sample ranking. Do not retune HL8/HL10 half-life or 0.05 threshold on V45.

V46 should include available 2021 broker history, cold-start before 2021, one exact MT5 invocation, and retain monthly/yearly/rolling evidence. Any V46 pass still supports paper/demo research only.

## Provenance

Accepted V38 ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
Accepted V38 source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
V45 frozen source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.
V34 tape SHA `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.

Clean-clone recovery may reconstruct accepted V38 parent from installed V45 source only when both exact SHA gates pass. No provenance gate may be weakened.

## Runtime storage

Workspace can be `D:\v31_mt5_40usd`.
MetaTester physical storage is `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`; the original C MetaQuotes Tester path is an NTFS junction and must not be manually deleted.

Recovery ladder:
`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`.

If `MT5_DONE.json` exists, MT5 MUST NOT RERUN. If `DONE.txt` exists, analyze/package only. Completed evidence with ZIP failure uses package-only recovery.
