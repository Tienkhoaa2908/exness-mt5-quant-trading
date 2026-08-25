# V50 Execution Probe Results — 2026-08-25

Accepted recovered ZIP SHA256:
`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Bundle integrity:
- ZIP CRC PASS;
- internal SHA256 manifest 9/9 PASS.

Authoritative raw EA FINAL:
- `verdict=EXECUTION_PIPELINE_PASS`;
- `reason=three_min_volume_demo_round_trips_confirmed`;
- `probe_round_trips=3`;
- `probe_requests=6`;
- `probe_rejects=0`;
- `strategy_round_trips=0`;
- `strategy_healthy_breadth=3`;
- run id `v50_execution_probe_v1__XAUUSDm__PERIOD_M15__2026-08-25_15-02-29__666031`.

Broker transaction evidence contains exactly three entry and three exit deals at 0.01 XAUUSDm. Final probe state is flat with zero pending/open probe positions and no halt.

Visible/probe-derived realized PnLs were approximately:
- BUY: -0.840 USD;
- SELL: -0.459 USD;
- BUY: -0.611 USD;
- total: -1.910 USD.

The PnL is not strategy-alpha evidence. The probe intentionally alternated direction and held positions long enough to force the native broker open/close/reconciliation path. The execution qualification question is therefore closed as PASS; do not repeat the same probe merely for more samples.

Observed orchestration defect: startup Python briefly hit a Windows file-sharing `PermissionError` while reading the MQL status file. Recovery tooling later captured the completed EA evidence. The recovery metadata parser also did not normalize literal `\\r\\n`, causing `EA_FINAL_FINAL`/blank metadata in `v50_recovery_final.txt`; raw V50 FINAL/status files remain authoritative and intact.

Decision:
`EXECUTION_PIPELINE_PASS=1`

Next research bottleneck:
signal frequency / opportunity selection, addressed by V51 ADR-051.
