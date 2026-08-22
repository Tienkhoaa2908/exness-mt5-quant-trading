# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-22

## Safety

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade.
- No Martingale, uncontrolled grid, or doubling after loss.
- Strategy Tester only; `AllowLiveTrading=0`, `AllowDllImport=0`.
- Native/external broker orders remain forbidden.
- `LIVE_AUTHORIZED=0`.

## Repository

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.
Active campaign branch: `agent/v46-expert-breadth-walkforward`.
Accepted V44 base: `7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.
V45 source/recovery commit: `1566a0bf0988fbab4395f5a604a0d428f4f95b97`.
Never use `git clean`.

## Accepted V45 result — HOLD

Accepted V45 ZIP SHA256:
`490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`.

Integrity PASS: ZIP CRC, internal manifest 23/23, HEAD `1566a0bf0988fbab4395f5a604a0d428f4f95b97`, exact V38 parent SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`, exact V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`, compiler 0 errors/0 warnings, MT5 rc=0, tester/no-order/live guards PASS.

Protocol: one exact XAUUSDm M15 run, 2022-01-01 -> 2026-08-01, $40, 1:200, cold-start, first six months warm-up, 55 raw months / 49 evaluation months.

Primary HL10p05 after warm-up:
- +105.786638% compounded;
- +1.483694% geometric/month;
- reported max MTM DD 56.2976%;
- PF 1.132725;
- 20/49 positive months;
- worst full year -25.749354%;
- rolling-12m positive 23/38; worst -30.690805%;
- full cold-start $40 -> $63.863453 (+59.6586%).

Year decomposition:
- 2022 Jul-Dec -25.576981%;
- 2023 +17.830616%;
- 2024 -25.749354%;
- 2025 +70.358836%;
- 2026 Jan-Jul +85.518335%.

No frozen V45 candidate passes the preregistered multi-year gate. Direct deployment escalation is blocked.

Full result: `docs/research/v45_multiyear_single_run_validation_results.md`.

## Market-regime interpretation of V45

Do not treat every negative crisis year as proof the model is wrong, and do not remove crisis years from validation.

External gold-market context shows two different failure types:
- 2022 was a genuine conflicting-force regime: Russia-Ukraine safe-haven demand, inflation, rapidly rising rates and a strong USD pulled gold in opposing directions. A strategy may reasonably reduce or stop risk in such a transition regime instead of forcing positive returns.
- 2024 was different: gold rose roughly 25.5% and made about 40 new all-time highs. The primary HL10 router still lost materially. Therefore 2024 cannot be excused as simply "war made gold untradeable"; the router/regime layer failed to convert a strong gold trend into acceptable risk-adjusted performance.

Trade-level V45 decomposition reinforces this distinction. For HL10p05 after warm-up:
- 2022 LONG about -22.22R, SHORT about -8.81R;
- 2024 LONG about -23.92R, SHORT about -4.36R;
- 2025 LONG about +52.24R, SHORT about +20.51R;
- 2026 Jan-Jul LONG about +37.03R, SHORT about +43.25R.

Thus the primary engineering objective is not "make money every war year". It is: when ensemble evidence is unhealthy, stay in cash early enough that crisis/transition regimes do not create catastrophic drawdown, while retaining the 2025-2026 edge when the ensemble is healthy.

Post-hoc price-feature diagnostics from V45 are research-only, not promotable evidence. Examples: ADX<=30 materially improves 2024 trade-R in replay and DI direction-alignment improves aggregate R, but those observations were discovered after seeing V45 and must not be folded into the V46 primary. They are candidates for a separately preregistered V47 only if V46 breadth is insufficient.

## V46 structural hypothesis

V45 diagnosis shows weak years are broad ensemble failures. The inherited HL10p05 router only requires the currently selected expert's EWMA score >=0.05; it does not require the ensemble to be healthy.

V46 adds a causal portfolio-level breadth/cash gate while preserving the underlying expert signals, HL10 half-life, selected-expert 0.05 threshold, entry/exit geometry and risk.

Preregistered primary:
`v46_hl10_thr0p05_breadth4`

Rule: before opening new risk, at least 4 of all 5 shadow experts must have HL10 EWMA score >=0.05. Scores remain updated causally from realized-R of independent norm-book shadow experts.

Sensitivity only, never promotable from this sample:
- `v46_hl10_thr0p05_breadth3_sensitivity`;
- `v46_hl10_thr0p05_breadth5_sensitivity`.

## V46 frozen-source SHA correction — before MT5

Two V46 attempts stopped before MetaEditor/MT5:
1. initial static-test false positive on the builder's own forbidden-token scanner;
2. deterministic source build rejected because the preregistered expected SHA was miscomputed.

The second failure is not a strategy/source divergence. The Windows runner generated SHA:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

That exact SHA was independently reproduced from the accepted V45 ZIP bytes with parent SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2` using the tracked V46 transformation. Therefore the earlier expected value `3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13` is recorded as a preparation-time frozen-hash error.

Canonical V46 source SHA is now:
`6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`.

No V46 MT5 tester evidence exists yet. The correction does not change MQL bytes; it corrects the expected identity of the already generated deterministic MQL bytes.

Canonical entrypoint after this correction:
`runtime/v46_expert_breadth/BOOTSTRAP_V46_CANONICAL_GIT_BASH.sh`.

## V46 exact protocol

One Strategy Tester invocation only:
- XAUUSDm / M15 / Model=0;
- Deposit=$40 USD / leverage 1:200;
- 2021-01-03 -> 2026-08-01;
- cold-start adaptive state;
- first six observed months warm-up;
- post-warm-up 2021 is tracked as previously unused historical holdout;
- monthly summary + full trade ledger retained;
- yearly and rolling 3/6/12m analysis retained.

Only breadth4 can pass. Crisis years are not required to be profitable individually; the general readiness rules enforce capital preservation instead: full-run DD <=20%, PF >=1.20, annualized return >=10%, worst full year >=-10%, worst rolling-12m >=-10%, explicit 2021 holdout guard, activity floor and -0.05R/trade friction stress.

Plan: `docs/research/v46_expert_breadth_walkforward_plan.md`.

## Runtime / storage

Workspace is supported on `D:\v31_mt5_40usd`.
MetaTester physical storage is on `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`; the original C MetaQuotes Tester path is an NTFS junction and must not be manually deleted.

V45/V46 clean-clone recovery can rebuild the pinned Python environment on the repo volume. If the accepted V38 ZIP is absent, provenance can be recovered only through exact SHA-verified installed V45 source -> exact accepted V38 parent -> exact V45 parent transformation.

Recovery ladder:
`provenance -> source -> compile -> tester-storage migration -> disk preflight -> MT5 -> collection -> analysis -> packaging`.

V46 checkpoints:
- valid compile checkpoint -> do not recompile;
- `OUTPUT_V46/checkpoint/MT5_DONE.json` -> collection only, MT5 MUST NOT RERUN;
- `OUTPUT_V46/checkpoint/DONE.txt` -> analysis/package only, MT5 MUST NOT RERUN;
- completed bundle + ZIP failure -> package-only recovery.
