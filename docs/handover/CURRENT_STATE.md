# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Tester/live guards and no-order constraints must not be weakened.
- `LIVE_AUTHORIZED=0` remains mandatory.

## Repository / current accepted campaign

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Accepted V44 base commit: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.
V45 source/recovery commit: `1566a0bf0988fbab4395f5a604a0d428f4f95b97`.
Current V45 branch: `agent/v45-multiyear-single-run-validation`.

Never use `git clean`. Local evidence, state backups, compiled EAs, checkpoints, Python envs and accepted ZIPs may be untracked recovery assets.

Read together:
- `docs/research/v44_baseline_robustness_validation_results.md`
- `docs/research/v45_multiyear_single_run_validation_plan.md`
- `docs/research/v45_multiyear_single_run_validation_results.md`
- `docs/research/v45_mt5_disk_failure_diagnosis.md`
- `docs/research/v45_clean_clone_recovery.md`
- `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`

## V44 accepted result

Accepted V44 evidence ZIP SHA256:
`550396cc2806538ae1f38ba596e3af705a08bcb2305335a14d0cfa39aabc8fa4`.

V44 = `PAPER_DEMO_READY` inside the one-year 2025-08 -> 2026-08 development period. Annual control reproduced exactly at $107.432645 / 563 trades. Frozen V45 candidates were:
1. primary `adaptive_ewma_hl10_thr0p05`;
2. return shadow `adaptive_ewma_hl8_thr0p05`;
3. control `adaptive_ewma_hl8_thr0`.

## V45 exact multi-year result — HOLD

Accepted V45 uploaded ZIP SHA256:
`490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`.

Integrity:
- ZIP CRC PASS;
- internal bundle manifest 23/23 PASS;
- HEAD `1566a0bf0988fbab4395f5a604a0d428f4f95b97`;
- accepted V38 parent source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- frozen V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- compiler `Result: 0 errors, 0 warnings`;
- MT5 launch rc=0;
- one exact run id `v45_multiyear_single_run_validation_v1__XAUUSDm__PERIOD_M15__2022-01-01_00-00-00__972671`;
- safety markers PASS: tester-only, no native/external broker orders, risk unchanged, live not authorized.

Protocol: one continuous exact MT5 run, XAUUSDm M15, 2022-01-01 -> 2026-08-01, $40 USD, leverage 1:200, cold-start adaptive state, first six months preregistered warm-up, 55 raw months / 49 evaluation months.

Formal status:
`STATUS=HOLD`
`ready_candidates=[]`
`LIVE_AUTHORIZED=0`

### Primary HL10p05

After warm-up:
- compounded return +105.786638%;
- geo/month +1.483694%; annualized +19.331535%;
- reported max MTM DD 56.2976%;
- positive months 20/49 = 40.82%;
- worst month -10.9191%; best +19.3409%;
- 1,556 trades; AvgR 0.072124R; SumR 112.22564R; PF 1.132725;
- 2/3 full years positive;
- worst full year -25.749354%;
- rolling-12m positive 23/38 = 60.53%;
- worst rolling-12m -30.690805%;
- SumR after -0.05R/trade stress +34.42564R.

Full cold-start economics including warm-up: $40 -> $63.863453, +59.6586% total over 55 months, about +0.8543% geometric/month.

Year decomposition for HL10p05:
- 2022 Jul-Dec -25.576981%, SumR -31.03432R;
- 2023 +17.830616%, SumR +18.50377R;
- 2024 -25.749354%, SumR -28.28029R;
- 2025 +70.358836%, SumR +72.75584R;
- 2026 Jan-Jul +85.518335%, SumR +80.28064R.

The same 2025-08 -> 2026-07 segment in the long cold-start path remains strong at about +138.2851% total / +7.5040% geometric/month, but the broader 2022-2026 history disproves regime-agnostic robustness.

### Other frozen candidates

`adaptive_ewma_hl8_thr0`: evaluation +111.884951%, PF 1.126242, DD 59.9492%, 22/49 positive months, worst full year -31.004730%, full cold-start $40 -> $60.670566.

`adaptive_ewma_hl8_thr0p05`: evaluation +95.603830%, PF 1.136437, DD 56.2877%, 20/49 positive months, worst full year -23.050274%, full cold-start $40 -> $60.350520.

No candidate passes the preregistered V45 multi-year gate.

## Structural diagnosis from V45

The failure is broad-regime rather than one isolated expert. HL10p05 selected-source R contribution:
- 2022: EMA -21.237R, SlowMom -26.666R, Trend20 -10.642R;
- 2023: SlowMom +21.969R and Trend20 +5.902R offset other weakness;
- 2024: EMA -8.462R, SlowMom -10.462R, Trend20 -7.480R, BOS/FVG -3.488R, only MACD +1.611R;
- 2025: EMA +40.187R, Trend20 +25.309R, BOS/FVG +11.189R;
- 2026 Jan-Jul: SlowMom +45.948R, EMA +30.186R, MACD +8.730R.

Current `adaptive_min_score=0.05` is a selected-expert gate only. It does not require the broader five-expert ensemble to be healthy. In weak regimes the router can therefore allocate risk to one locally eligible expert while the majority of the ensemble is deteriorating.

Causal post-hoc diagnostic reconstruction from the norm-book shadow-expert exits shows a promising structural signal: when at least 4 of the 5 HL10 expert EWMA scores are >=0.05, observed router trade quality improves sharply. Indicative replay with original observed risk fractions gives roughly $40 -> $85.86 (+114.6%) with ~15.9% closed-balance DD versus actual $63.86 / ~55% closed-balance DD. This is diagnostic only and MUST NOT be treated as accepted evidence or same-sample promotion.

## Decision / next campaign

V45 blocks direct deployment escalation of the frozen baseline. Do not paper/demo-promote the current baseline as if V45 passed.

Next campaign: V46 causal expert-breadth/cash gate.
- preserve HL10p05 scoring and all entry/exit/risk geometry;
- primary hypothesis: require >=4 of 5 HL10 shadow-expert EWMA scores >=0.05 before any new router risk;
- breadth3 / breadth5 may exist only as sensitivity comparators; do not promote them by same-sample ranking;
- include previously unseen broker history beginning in 2021 if available;
- cold-start state before the historical run;
- one exact MT5 tester invocation with monthly/yearly/rolling evidence;
- no real-money authorization.

## Runtime / storage recovery

MetaTester physical storage is on D via junction:
`D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.
The logical C path under `%APPDATA%\MetaQuotes\Tester\<terminal-id>` is a junction. Do not manually delete it.

Workspace may live at `D:\v31_mt5_40usd`. V45 clean-clone bootstrap can rebuild the pinned Python environment and, if the accepted V38 ZIP is missing, exactly recover the accepted V38 parent from the installed V45 source only when the frozen V45 SHA and recovered V38 SHA both match their hard gates.

Recovery ladder:
`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`.
If `MT5_DONE.json` exists, collect only; if `DONE.txt` exists, analyze/package only; if only packaging failed, package only. Never rerun completed MT5 evidence.
