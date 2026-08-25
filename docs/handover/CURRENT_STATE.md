# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-25

## Project objective

The project targets production/live deployment after sufficient evidence. Current research bottleneck is signal frequency/opportunity selection, not broker plumbing.

## Inherited historical baseline

Frozen reference candidate:
`v46_hl10_thr0p05_breadth4`

Accepted V46 evidence remains historical `STATUS=HOLD` because one preregistered full-year sign gate failed, but breadth4 materially improved drawdown/PF versus the previous router and remains the baseline for challenger research.

## V50 execution qualification — ACCEPTED

Accepted recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Integrity:
- ZIP CRC PASS;
- manifest 9/9 PASS.

Authoritative raw EA FINAL:
- `verdict=EXECUTION_PIPELINE_PASS`;
- `probe_round_trips=3`;
- `probe_requests=6`;
- `probe_rejects=0`;
- final probe positions/pending/halt all zero;
- run id `v50_execution_probe_v1__XAUUSDm__PERIOD_M15__2026-08-25_15-02-29__666031`.

Conclusion:
`EXECUTION_PIPELINE_PASS=1`

Do not repeat V50 plumbing probes. Their total approximately -1.91 USD PnL was probe cost, not alpha evidence.

See `docs/research/v50_execution_probe_results_2026-08-25.md`.

## Current milestone — V51 higher-frequency challenger

Branch:
`agent/v51-higher-frequency-challenger`

ADR:
`docs/adr/ADR-051-higher-frequency-hybrid-challenger.md`

Plan:
`docs/research/v51_higher_frequency_plan.md`

V51 runs one exact historical MT5 tournament. It does not replace breadth4 blindly with breadth3.

Baseline:
- `v46_hl10_thr0p05_breadth4`.

Preregistered challengers:
- `v51_b4_or_b3_avg0p075`;
- `v51_b4_or_b3_avg0p10`;
- `v51_b4_or_b3_avg0p15`.

Hybrid semantics:
- if healthy breadth >=4: preserve the breadth4 path;
- if healthy breadth ==3: allow the extra lane only when average expert-health score clears the fixed candidate quality floor.

No native broker execution is introduced in V51 historical source. No Martingale/grid and no risk increase.

## V51 selection guardrails

A challenger is eligible only if:
- trade count >=1.20x breadth4 baseline;
- max MTM DD <=20%;
- DD increase <=3 percentage points versus baseline;
- PF >=1.15 and >=90% of baseline PF;
- AvgR >=0.08R and >=65% of baseline AvgR;
- annualized return >=8%;
- `SumR - 0.05R * trades > 0`;
- worst full year >=-10%;
- worst rolling12 >=-10%.

If multiple pass, select highest friction-stressed SumR per unit DD. If none pass, `V51_KEEP_BREADTH4` is a valid result.

## Current action

Run one V51 Windows historical tournament, then upload exactly:
`runtime/v51_higher_frequency/OUTPUT_V51/v51_higher_frequency_tournament.zip`

Do not run another V50 execution probe.

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=IMPLEMENTED_PENDING_WINDOWS_RUN`
