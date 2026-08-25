# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-25

## Project objective

The project targets production/live deployment after sufficient evidence. Current implementation work remains on broker DEMO execution qualification.

Frozen alpha remains `v46_hl10_thr0p05_breadth4`; historical V46/V45 evidence is inherited and is not re-optimized merely to accelerate an execution test.

## V50 Windows execution evidence — authoritative

Branch/runtime used on Windows:
`agent/v50-execution-probe`

Executed runtime HEAD:
`761a65f573b110fcbad8b86608e39c76edd9d73c`

Accepted pre-transition evidence from the user run:
- V50 static tests PASS count=8;
- `SECRET_SCAN_PASS files=107 mode=git-tracked`;
- frozen V46 -> V47 -> V48 -> V49 source chain rebuilt successfully;
- V50 generated source SHA256 `1db600a934c7ddd2797b40045280f1948ae0e7dddce80bc244bc599e10c6a040`;
- MetaEditor compile PASS `Result: 0 errors, 0 warnings`;
- V50 EX5 SHA256 `e81dfa0559d2f5e2422ac03551fc88908c32d755ca927b3c04e4a827964c2268`;
- V49 was already closed/flat before transition;
- V50 state seed SHA256 `36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`;
- V50 config SHA256 `b7c95b43a6f957a1ec47782cbdfde04e944117face7b7d75dbb5b9682921e290`;
- MT5 launched V50 with terminal PID 14328.

After launch, the Python runner hit a transient Windows sharing race while reading `V50_EXECUTION_PROBE_STATUS.txt` and exited with `PermissionError`. This was an orchestration/read-side failure, not an EA execution failure. The EA continued running in MT5.

User screenshots of MT5 History show three new XAUUSDm probe round trips (0.01 lot each) completed around 2026-08-25 15:02-15:06. The three realized PnLs visible in History are approximately `-0.84`, `-0.46`, and `-0.61` USD, totaling `-1.91` USD. The Trade tab is flat afterward and the account balance shown is `38.09 USD` from the 40 USD rehearsal balance.

This is sufficient evidence that native DEMO order open/close plumbing executed; do not run additional probes merely to reproduce the same plumbing evidence. Final qualification still requires recovery of the EA FINAL/status/transaction files and packaging into the canonical ZIP.

## Share-lock incident and fix

Source inspection confirms the MQL creates the correct directory `mt5_quant\\v50` and writes the status as a file. The Python `PermissionError` can occur when it attempts to read during the short MT5 write handle window.

The branch now includes:
- retry-safe `kv()` in `RUN_V50_EXECUTION_PROBE.py`;
- retry-safe `kv()` in `SUPERVISE_V50_EXECUTION_PROBE.py`;
- `RECOVER_V50_EXECUTION_PROBE.py`, which performs read-only evidence recovery/package without starting MT5 or sending any new broker request;
- static coverage requiring share-lock tolerance and ensuring recovery cannot start/trade.

Operational rule: **recover/package the already executed run; do not restart V50 and do not create probe #4.**

## V50 decision

ADR-050 decouples alpha frequency from execution qualification.

V50 does **not** lower breadth4 and does **not** retune alpha. The execution probe uses separate magic `500050`, broker minimum volume, margin precheck, protective SL/TP, automatic close, transaction confirmation, and no overlap with breadth4 positions.

The observed cost of the three DEMO probes (`-1.91 USD` on a nominal 40 USD rehearsal balance) is materially too large for a plumbing-only test. Do not rerun this probe design for convenience. If a future execution probe is ever necessary, use a lower-cost dedicated design rather than repeating the 45-second three-trade sequence.

## Evidence workflow

Current task is recovery only.

Expected output:
`runtime/v50_execution_probe/OUTPUT_V50/V50_EXECUTION_PROBE_RECOVERED_*.zip`

The ZIP must include `bundle_manifest_sha256.txt` plus available V50 status/final/events/transactions and relevant run evidence.

If EA FINAL exists, preserve its verdict. If EA FINAL is absent, package as recovery evidence without fabricating `EXECUTION_PIPELINE_PASS`.

## Current readiness

`EXECUTION_PLUMBING=OBSERVED_3_DEMO_ROUND_TRIPS`

`V50_FINAL_EVIDENCE=PENDING_RECOVERY_ZIP`

Do not infer strategy failure solely from quiet breadth4 days, and do not infer alpha quality from the probe PnL. Probe trades exist only to qualify execution plumbing.
