# V45 Multi-year Single-run Validation — Results

Date: 2026-08-22

## Evidence integrity

Accepted uploaded ZIP SHA256:
`490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`

ZIP CRC: PASS.
Internal bundle manifest: 23/23 listed files hash exactly; manifest intentionally does not self-list.

Canonical run provenance:
- HEAD `1566a0bf0988fbab4395f5a604a0d428f4f95b97`;
- branch `agent/v45-multiyear-single-run-validation`;
- accepted V38 parent ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`;
- accepted V38 parent source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- frozen V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- compiler evidence `Result: 0 errors, 0 warnings`;
- MT5 launch rc=0;
- exact run id `v45_multiyear_single_run_validation_v1__XAUUSDm__PERIOD_M15__2022-01-01_00-00-00__972671`.

Safety markers PASS: `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`, `risk_changed=0`, `live_authorized=0`.

## Protocol

One continuous exact MT5 Strategy Tester run only, XAUUSDm M15, 2022-01-01 -> 2026-08-01, $40 USD, 1:200, cold-start adaptive state, no 2025 state injected. Raw coverage is 55 monthly rows per frozen candidate, January 2022 through July 2026. First six months are preregistered warm-up; readiness evaluation covers July 2022 through July 2026 (49 months).

## Formal result

`STATUS=HOLD`

No frozen candidate passes the V45 multi-year readiness gate. `ready_candidates=[]`. `LIVE_AUTHORIZED=0`.

### adaptive_ewma_hl8_thr0

Evaluation after warm-up:
- compounded return +111.884951%;
- geometric month +1.544196%; annualized +20.188040%;
- max reported MTM DD 59.9492%;
- 22/49 positive months = 44.90%;
- worst month -12.2442%; best +21.3101%;
- 1,730 trades; AvgR 0.068454R; SumR 118.42613R; PF 1.126242;
- full years: 2/3 positive; worst full year -31.004730%;
- rolling 12m: 22/38 positive = 57.89%; worst -33.779135%;
- -0.05R/trade stress remains positive at +31.92613R.

Full cold-start economics including warm-up: $40 -> $60.670566, +51.6764% total over 55 months, approximately +0.7603% geometric/month.

### adaptive_ewma_hl8_thr0p05

Evaluation after warm-up:
- compounded return +95.603830%;
- geometric month +1.378644%; annualized +17.857634%;
- max reported MTM DD 56.2877%;
- 20/49 positive months = 40.82%;
- worst month -10.2440%; best +21.6005%;
- 1,565 trades; AvgR 0.074175R; SumR 116.08332R; PF 1.136437;
- full years: 2/3 positive; worst full year -23.050274%;
- rolling 12m: 21/38 positive = 55.26%; worst -28.341895%;
- -0.05R/trade stress remains positive at +37.83332R.

Full cold-start economics including warm-up: $40 -> $60.350520, +50.8763% total over 55 months, approximately +0.7506% geometric/month.

### adaptive_ewma_hl10_thr0p05 — preregistered primary

Evaluation after warm-up:
- compounded return +105.786638%;
- geometric month +1.483694%; annualized +19.331535%;
- max reported MTM DD 56.2976%;
- 20/49 positive months = 40.82%;
- worst month -10.9191%; best +19.3409%;
- 1,556 trades; AvgR 0.072124R; SumR 112.22564R; PF 1.132725;
- full years: 2/3 positive; worst full year -25.749354%;
- rolling 12m: 23/38 positive = 60.53%; worst -30.690805%;
- -0.05R/trade stress remains positive at +34.42564R.

Full cold-start economics including warm-up: $40 -> $63.863453, +59.6586% total over 55 months, approximately +0.8543% geometric/month.

## Year/regime decomposition — primary HL10p05

After warm-up:
- 2022 Jul-Dec: -25.576981%, SumR -31.03432R;
- 2023: +17.830616%, SumR +18.50377R, PF 1.115028;
- 2024: -25.749354%, SumR -28.28029R, PF 0.841045;
- 2025: +70.358836%, SumR +72.75584R, PF 1.255416;
- 2026 Jan-Jul: +85.518335%, SumR +80.28064R, PF 1.606545.

The worst rolling 12m for HL10p05 ends 2025-01 at -30.690805%. The best ends 2026-07 at +138.285055%.

The same 2025-08 -> 2026-07 segment inside the long cold-start path compounds about +138.2851% (+7.5040% geometric/month), confirming that the recent regime remains strong but is materially weaker than the accepted V44 one-year path because adaptive state/history path matters.

## Structural diagnosis

The failure is broad-regime, not one isolated expert. Realized-R contribution by selected source for HL10p05:
- 2022: EMA -21.237R, SlowMom -26.666R, Trend20 -10.642R; MACD +2.500R, BOS/FVG -1.001R;
- 2023: SlowMom +21.969R and Trend20 +5.902R offset EMA/BOS weakness;
- 2024: EMA -8.462R, SlowMom -10.462R, Trend20 -7.480R, BOS/FVG -3.488R; only MACD +1.611R;
- 2025: EMA +40.187R, Trend20 +25.309R, BOS/FVG +11.189R;
- 2026 Jan-Jul: SlowMom +45.948R, EMA +30.186R, MACD +8.730R.

Thus the current router can still choose a locally eligible expert when the broader expert ensemble is unhealthy. The existing `adaptive_min_score=0.05` gates the selected expert only; it does not require cross-expert health breadth.

A causal diagnostic reconstruction of the exact HL10 expert EWMAs from norm-book shadow-expert exits shows a strong monotonic research signal: when at least 4 of 5 HL10 expert scores are >=0.05, the observed primary-router trades have materially higher realized-R quality. A post-hoc indicative replay using the original per-trade risk fractions gives approximately $40 -> $85.86 (+114.6%) with ~15.9% closed-balance DD versus the actual $63.86 and ~55% closed-balance DD. This replay is diagnostic only, not accepted evidence and not a promotion result.

## Decision

V45 formally rejects direct deployment escalation of the current frozen baseline family. The strong 2025-2026 performance is real in the exact tester evidence, but it is regime-dependent and does not survive the preregistered 2022-2026 robustness gate.

Next research should target the structural failure rather than retune HL8/HL10 half-life or the 0.05 threshold on the same V45 sample. The preferred V46 hypothesis is a causal cross-expert breadth/cash gate: preserve the HL10p05 router but allow new risk only when enough independent shadow experts have positive/healthy EWMA scores. Breadth4 (>=4 of 5 experts above 0.05) is the preregistered primary hypothesis from V45 diagnosis; breadth3/breadth5 may be sensitivity comparators only and must not be promoted by same-sample ranking.

V46 should include the previously unseen 2021 history available from the broker cache, cold-start before 2021, retain monthly/yearly/rolling evidence, and keep all safety/live prohibitions unchanged.
