# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current campaign

Active branch: `agent/v46-expert-breadth-walkforward`.
Accepted V44 base: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.
V45 source/recovery commit: `1566a0bf0988fbab4395f5a604a0d428f4f95b97`.
Accepted V45 evidence ZIP SHA256: `490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`.
V45 formal result: `HOLD`.

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v45_multiyear_single_run_validation_results.md`
3. `docs/research/v46_expert_breadth_walkforward_plan.md`
4. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
5. `docs/research/v45_clean_clone_recovery.md`

Never `git clean`.

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Research risk <=1.00%/trade. No Martingale/grid/doubling. Strategy Tester only with `AllowLiveTrading=0`, `AllowDllImport=0`, no native/external broker orders. `LIVE_AUTHORIZED=0`.

## Why V46 exists

V45 exact multi-year evidence shows the frozen baseline family is regime-dependent. Primary HL10p05 is strong in 2025-2026 but weak in 2022 and 2024; full cold-start $40 -> $63.863453 over 55 months, DD 56.2976%, PF 1.132725, worst full year -25.749354%. V45 therefore blocks deployment escalation.

Do not simplify this to "war years are invalid". 2022 was a genuine conflicting-force crisis/transition regime and can reasonably be a low-exposure/flat regime. 2024, however, was a very strong gold year, so the router's large loss there still indicates a regime/routing problem. The engineering objective is capital preservation when the ensemble is unhealthy, not forced profitability in every crisis year.

## V46 preregistered primary

`v46_hl10_thr0p05_breadth4`

Before opening new risk:
- use inherited HL10 expert EWMAs;
- inherited selected-expert threshold remains 0.05;
- require at least 4 of all 5 shadow experts to have HL10 EWMA >=0.05;
- scores remain updated causally from realized-R of independent norm-book shadow experts.

Sensitivity only and never promotable from this sample:
- `v46_hl10_thr0p05_breadth3_sensitivity`;
- `v46_hl10_thr0p05_breadth5_sensitivity`.

Post-hoc V45 observations such as ADX<=30 or DI direction alignment are not allowed into the V46 primary. They may be separately preregistered for V47 if breadth alone is insufficient.

## V46 exact protocol

One continuous Strategy Tester invocation only:
- XAUUSDm / M15 / Model=0;
- Deposit=$40 USD / leverage 1:200;
- FromDate=2021.01.03;
- ToDate=2026.08.01;
- cold-start adaptive state;
- first 6 observed months warm-up;
- 2021 post-warm-up segment tracked as previously unused historical holdout;
- monthly summary + full trade ledger retained;
- yearly + rolling 3/6/12m retained.

## Canonical V46 source SHA correction

The first V46 static failure and the later source-SHA failure both occurred before MetaEditor/MT5. No V46 tester evidence exists yet.

The tracked V46 transformation applied to the accepted V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2` deterministically produces:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

This exact value was observed on Windows and independently reproduced from the accepted V45 evidence ZIP. The earlier value `3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13` was a preparation-time frozen-hash error, not a change in generated MQL bytes.

Canonical V46 entrypoint:
`runtime/v46_expert_breadth/BOOTSTRAP_V46_CANONICAL_GIT_BASH.sh`.

Canonical wrapper chain:
- `scripts/build_v46_expert_breadth_source_canonical.py` hard-gates the corrected V46 SHA and the accepted V45 parent SHA;
- `runtime/v46_expert_breadth/RUN_V46_EXPERT_BREADTH_ONE_SHOT_CANONICAL.py` hard-gates V38 -> V45 provenance and runs the existing V46 orchestrator with the corrected source identity;
- `tests/test_v46_canonical_sha_fix_static.py` locks this correction.

## V46 readiness gate

Only breadth4 can pass. All breadth4 checks must pass:
- >=60 evaluation months;
- full cold-start max MTM DD <=20%;
- PF >=1.20;
- annualized return >=10%;
- >=4 full calendar years;
- >=75% full years nonnegative;
- worst full year >=-10%;
- >=75% rolling-12m windows not worse than -5%;
- worst rolling-12m >=-10%;
- >=24 active months;
- >=50% positive active months;
- post-warm-up 2021 holdout return >=-10%;
- >=400 evaluation trades;
- SumR remains positive after -0.05R/trade stress.

A V46 pass permits paper/demo execution-reconciliation research only; never live capital.

## Provenance

Accepted V38 ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
Accepted V38 source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
Frozen V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.
Canonical V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.
V34 tape SHA `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`.

Clean-clone provenance must remain hard-gated: installed V45 exact SHA -> recovered accepted V38 exact SHA -> rebuilt V45 exact SHA -> canonical V46 exact SHA. Never weaken this chain to make a runner pass.

## Runtime / storage

Workspace supported at `D:\v31_mt5_40usd`.
MetaTester physical storage: `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.
The original C MetaQuotes Tester path is an NTFS junction; do not manually delete it.

Expected successful ZIP:
`runtime/v46_expert_breadth/OUTPUT_V46/v46_expert_breadth_walkforward.zip`.

Recovery ladder:
`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`.

If `OUTPUT_V46/checkpoint/MT5_DONE.json` exists, MT5 MUST NOT RERUN. If `DONE.txt` exists, analysis/package only. If completed evidence exists and ZIP creation failed, run package-only recovery.
