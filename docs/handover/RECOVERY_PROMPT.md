# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current milestone

V50 DEMO execution qualification — **recover existing executed run, do not rerun probes**.

Authoritative branch:
`agent/v50-execution-probe`

Read first:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-050-decouple-alpha-frequency-from-execution-qualification.md`
3. `docs/research/v50_execution_probe_plan.md`
4. `runtime/v50_execution_probe/RECOVER_V50_EXECUTION_PROBE.py`

## Frozen alpha

Do not lower or retune `v46_hl10_thr0p05_breadth4` merely to accelerate execution qualification.

## Executed V50 run

Windows executed runtime HEAD:
`761a65f573b110fcbad8b86608e39c76edd9d73c`

Pre-transition/run evidence:
- static 8/8 PASS;
- secret scan PASS;
- V50 source SHA256 `1db600a934c7ddd2797b40045280f1948ae0e7dddce80bc244bc599e10c6a040`;
- MetaEditor `0 errors, 0 warnings`;
- V50 EX5 SHA256 `e81dfa0559d2f5e2422ac03551fc88908c32d755ca927b3c04e4a827964c2268`;
- V50 config SHA256 `b7c95b43a6f957a1ec47782cbdfde04e944117face7b7d75dbb5b9682921e290`;
- terminal launched PID 14328.

The Python startup runner then exited on a transient Windows file-sharing `PermissionError` while reading `Common\\Files\\mt5_quant\\v50\\V50_EXECUTION_PROBE_STATUS.txt`. Source inspection confirms the MQL path is correct; this is a reader/share-lock race.

Despite the runner exit, MT5/EA continued. User screenshots show three XAUUSDm 0.01-lot probe round trips completed and the Trade tab flat afterward. Visible realized PnLs are approximately `-0.84`, `-0.46`, and `-0.61` USD, total `-1.91` USD. Do not create additional probes.

## Recovery implementation

Current branch includes:
- share-lock retry in `RUN_V50_EXECUTION_PROBE.py`;
- share-lock retry in `SUPERVISE_V50_EXECUTION_PROBE.py`;
- read-only `RECOVER_V50_EXECUTION_PROBE.py`.

The recovery script:
- never launches MT5;
- never calls broker execution;
- waits briefly for an existing EA FINAL;
- snapshots status/final/events/transactions with share-lock retries;
- includes run evidence when available;
- writes `bundle_manifest_sha256.txt`;
- creates `V50_EXECUTION_PROBE_RECOVERED_*.zip`;
- records `LATEST_V50_ZIP.txt`.

If EA FINAL exists, preserve its verdict. If not, package `RECOVERY_NO_EA_FINAL` without fabricating a PASS.

## Current classification

`EXECUTION_PLUMBING=OBSERVED_3_DEMO_ROUND_TRIPS`

`V50_FINAL_EVIDENCE=PENDING_RECOVERY_ZIP`

Next action is only recovery/package. Do not run `START_V50_EXECUTION_PROBE_GIT_BASH.sh` again for this evidence set.
