# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-26

## Project objective

The project targets production/live deployment after sufficient evidence. Broker-DEMO execution plumbing is already qualified; the active research problem is increasing signal frequency without giving back the drawdown/stability benefit of breadth4.

## Inherited baseline

Current reference candidate:
`v46_hl10_thr0p05_breadth4`

Accepted V46 evidence remains historical `STATUS=HOLD` because one preregistered full-year sign gate failed, but breadth4 materially improved drawdown/PF versus the previous router and remains the baseline for challenger research.

## V50 execution qualification — ACCEPTED

Accepted recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Authoritative raw EA FINAL:
- `verdict=EXECUTION_PIPELINE_PASS`;
- `probe_round_trips=3`;
- `probe_requests=6`;
- `probe_rejects=0`;
- final flat / no halt.

Conclusion:
`V50_EXECUTION_PIPELINE=PASS`

Do not repeat V50 plumbing probes.

## V51 higher-frequency tournament — ACCEPTED

Accepted ZIP SHA256:
`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Integrity:
- ZIP CRC PASS;
- manifest 17/17 PASS;
- run HEAD `8c211b27e6676f3176e089a619679e6af263e3fd`;
- source SHA256 `927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6`;
- MetaEditor `0 errors, 0 warnings`;
- run id `v51_higher_frequency_challenger_v1__XAUUSDm__PERIOD_M15__2021-01-03_00-00-00__812031`.

Formal result:
`V51_KEEP_BREADTH4`

Baseline breadth4:
- 825 eval trades;
- AvgR +0.1443R;
- PF 1.2817;
- annualized +21.34%;
- max MTM DD 16.60%;
- worst rolling12 -1.95%.

V51 challengers raised trade count by roughly 27%–35%, but all failed drawdown/stability guardrails:
- avg0.075: 1110 trades, DD 28.62%, worst rolling12 -13.39%;
- avg0.10: 1101 trades, DD 25.04%, worst rolling12 -11.09%;
- avg0.15: 1050 trades, DD 28.56%, worst rolling12 -14.39%.

No V51 average-health challenger is promotable.

See `docs/research/v51_higher_frequency_results_2026-08-26.md`.

## V51 diagnostic implication

Same-sample diagnostic decomposition of the incremental breadth3 lane shows a stable source split across all three V51 thresholds:
- `TREND20_H1`: positive incremental edge;
- `BOS_FVG_H1`: positive incremental edge;
- `EMA_H1`: negative incremental edge;
- `MACD_H1`: negative incremental edge;
- `SLOW_MOM_16H24H`: negative incremental edge.

For the avg0.10 challenger specifically, incremental trades were approximately:
- TREND20_H1: 76 trades, AvgR +0.149R, SumR +11.36R;
- BOS_FVG_H1: 16 trades, AvgR +0.331R, SumR +5.30R;
- EMA_H1: 114 trades, AvgR -0.085R;
- MACD_H1: 25 trades, AvgR -0.194R;
- SLOW_MOM_16H24H: 72 trades, AvgR -0.073R.

This is diagnostic/same-sample evidence, not a promotion result.

## Current milestone — V52 source-aware opportunity lane

Branch:
`agent/v52-source-aware-challenger`

ADR:
`docs/adr/ADR-052-source-aware-breadth3-opportunity-lane.md`

Plan:
`docs/research/v52_source_aware_plan.md`

V52 derives deterministically from the accepted V51 generated source SHA:
`927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6`

Baseline:
`v46_hl10_thr0p05_breadth4`

Preregistered challengers:
- `v52_b4_or_b3_trend`;
- `v52_b4_or_b3_bos`;
- `v52_b4_or_b3_trend_bos`.

Semantics:
- breadth >=4: preserve the inherited path;
- breadth ==3: apply a selected-expert source mask only;
- no new average-health threshold;
- no risk increase;
- no native broker orders in the historical source.

Selection guardrails:
- trade count >=1.05x baseline;
- max MTM DD <=20%;
- DD increase <=3 percentage points;
- PF >=1.20 and >=95% baseline;
- AvgR >=0.10R and >=75% baseline;
- annualized >=10%;
- friction-stressed SumR remains positive;
- worst full year >=-10%;
- worst rolling12 >=-10%.

If none passes, `V52_KEEP_BREADTH4` is the correct result.

Implementation status:
- V52 builder implemented;
- V52 analyzer implemented;
- V52 one-shot runner implemented;
- V52 static contract test implemented;
- V52 Git Bash entrypoint implemented;
- Windows MetaEditor compile / exact MT5 run still pending.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`
`V52_SOURCE_AWARE=IMPLEMENTED_PENDING_WINDOWS_RUN`
