# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V51 higher-frequency challenger tournament.

Authoritative branch:
`agent/v51-higher-frequency-challenger`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/research/v50_execution_probe_results_2026-08-25.md`
3. `docs/adr/ADR-051-higher-frequency-hybrid-challenger.md`
4. `docs/research/v51_higher_frequency_plan.md`
5. `runtime/v51_higher_frequency/START_V51_HIGHER_FREQUENCY_GIT_BASH.sh`

## Accepted V50 evidence

Recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Raw EA FINAL:
`EXECUTION_PIPELINE_PASS`

Evidence contains three completed 0.01-lot XAUUSDm DEMO round trips, six requests, zero rejects, final flat state and no halt. Do not rerun V50 plumbing probes.

## V51 purpose

The execution pipeline is no longer the bottleneck. V51 tests whether the strategy can trade materially more often without undoing breadth4 robustness.

Baseline:
`v46_hl10_thr0p05_breadth4`

Preregistered challengers:
- `v51_b4_or_b3_avg0p075`;
- `v51_b4_or_b3_avg0p10`;
- `v51_b4_or_b3_avg0p15`.

The breadth4 path is preserved. The challengers add only an exactly-three-healthy-expert opportunity lane with a fixed average health-quality threshold.

## Run semantics

One exact historical MT5 run:
- XAUUSDm M15;
- 2021-01-03 -> 2026-08-01;
- cold start;
- first 6 months warm-up;
- $40, leverage 1:200;
- no broker orders;
- no risk increase;
- no threshold changes after seeing the run.

Possible outcome:
- `V51_CHALLENGER_SELECTED`;
- `V51_KEEP_BREADTH4`.

If selected, only a short broker-DEMO confirmation is needed next because V50 already qualified native order plumbing.

## User workflow

Close MetaEditor and MT5 before the historical tester run, then run the canonical V51 Git Bash bootstrap supplied by the coordinator.

After completion upload one file only:
`runtime/v51_higher_frequency/OUTPUT_V51/v51_higher_frequency_tournament.zip`

Current classification:
`V50_EXECUTION_PIPELINE=PASS`
`V51_HIGHER_FREQUENCY=IMPLEMENTED_PENDING_WINDOWS_RUN`
