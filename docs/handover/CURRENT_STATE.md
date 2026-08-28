# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-28

## Authoritative working branch

`agent/v54-production-readiness-hardening`

V54 is based on accepted V53 HEAD:

`4b7b5a348e9412d2d34c827f86eae37904ddc627`

`main` is stale for current V50–V54 work and must not be used as the recovery source.

## Project objective

`LIVE_RESEARCH_ALLOWED=1`

`LIVE_DEPLOYMENT_TARGET=1`

The project targets production/live deployment after sufficient technical and
operational evidence. Candidate research is frozen. Current work is production
readiness, not another alpha tournament.

No V54 artifact should be interpreted as proof that real-money execution has already
been activated.

## Accepted evidence chain

### V50 execution plumbing — PASS

Accepted recovered ZIP SHA256:

`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

Authoritative result:

`EXECUTION_PIPELINE_PASS`

Three completed XAUUSDm DEMO round trips, six requests, zero rejects, final flat/no
halt. Do not rerun V50 probe trades.

### V51 higher-frequency tournament — KEEP BREADTH4

Accepted ZIP SHA256:

`8475b12077a28b18df722965895565772a6020a12ddebfd958aed67652808d98`

Formal result:

`V51_KEEP_BREADTH4`

Broad breadth3 expansion increased frequency but violated drawdown/rolling-stability
guardrails. Same-sample diagnostics motivated one source-aware TREND/BOS lane.

### V52 generated-tick run — INVALID DATA

ZIP SHA256:

`01f63cdcbff48ea0bb7d5d7ebf405e9612a7783e6ecc35b7c9afe6ef81abbed8`

Formal classification:

`V52_RESULT=INVALID_DATA_CONTAMINATION`

Do not use its raw challenger selection or metrics as evidence.

### V52R real-tick reproducibility — PASS

Accepted ZIP SHA256:

`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Formal result:

`V52R_CHALLENGER_SELECTED`

Selected research candidate:

`v52_b4_or_b3_trend_bos`

Clean real-tick comparison:

- breadth4: 819 trades, PF 1.2894, annualized 21.47%, max MTM DD 16.60%;
- TREND+BOS: 951 trades (+16.12%), PF 1.2649, annualized 22.17%, max MTM DD 16.10%.

Interpretation: frequency increased materially without giving back drawdown. Do not
represent this as a large friction-adjusted return improvement.

### V53 natural broker-DEMO confirmation — CLOSED BY WAIVER

Accepted recovered ZIP SHA256:

`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

Accepted run state:

- DEMO;
- market days 2;
- round trips 0;
- requests/rejects 0/0;
- duplicate events 0;
- direction mismatches 0;
- no pending request;
- no owned position;
- final virtual/broker state flat;
- DLL permission off;
- MetaEditor `0 errors, 0 warnings`;
- recovered immutable package CRC PASS and manifest 19/19 PASS.

Formal classification:

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

This is not `DEMO_CONFIRMATION_PASS`. Do not force a signal or extend the waiting gate.

## V54 production-readiness hardening

V54 inherits the exact selected-candidate builder from V53 and the proven V49/V50
broker execution architecture. It does not reopen strategy thresholds.

Production-readiness scope:

- `XAUUSDm M15`;
- owned magic `540054`;
- maximum one owned strategy position;
- same-symbol foreign-position ambiguity fails closed;
- no Martingale;
- no grid;
- no doubling after loss;
- risk-cap sizing using stop loss and `OrderCalcProfit`;
- default risk cap 0.50% equity and hard input ceiling 1.00%;
- daily/session loss stop 2.00%;
- peak-equity drawdown stop 6.00%;
- spread guard;
- stale broker-tick guard;
- stale strategy-state/restart guard;
- disconnect handling;
- repeated broker-reject halt;
- SL/TP presence validation;
- deterministic broker/virtual reconciliation;
- request/retcode/deal audit trail;
- MetaQuotes push notification path;
- immutable snapshot evidence ZIP;
- fail-closed rollback/runbook.

V54 activation boundary:

`PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE`

`real_money_authorized=0`

The generated V54 runtime retains an `ACCOUNT_TRADE_MODE_DEMO` guard. This permits
production engineering and Windows compile/recovery testing without fabricating
real-money deployment evidence.

## CI defect found during recovery

The accepted V53 HEAD had GitHub Actions `quality` failure. The first observed failure
was the repo-wide live-policy wording scanner, which treated historical ADR/research
quotes as current policy. The workflow also contained an unconditional historical V29
`exit 86`, so it could not become green even after the first failure was fixed.

V54 changes the scanner to active operator-facing documents and removes the unrelated
historical V29 migration failure from the global quality gate while keeping the old
archive quarantined and unused by V54.

Do not claim V54 CI PASS until the V54 commit's workflow concludes successfully.

## Current classification

`V50_EXECUTION_PIPELINE=PASS`

`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`

`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`

`V52R_REAL_TICK_REPRO=PASS`

`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

`V54_PRODUCTION_READINESS=IMPLEMENTED_PENDING_CI_WINDOWS_COMPILE`

`PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE`

## Next gate

1. obtain green V54 GitHub static/secret/unit-test evidence;
2. run the single V54 Windows starter;
3. require MetaEditor `0 errors, 0 warnings`, DEMO READY, clean ownership/reconciliation
   and automatic immutable startup evidence ZIP;
4. use normal V54 operation to collect fault/restart/notification evidence as needed;
5. retain `V53_NATURAL_MAPPING=NOT_OBSERVED` until a natural selected-candidate mapping
   is actually observed.

Do not reopen alpha research unless a real implementation defect invalidates the
selected candidate or its evidence.
