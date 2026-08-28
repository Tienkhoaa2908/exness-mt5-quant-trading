# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-08-28

## Authoritative working branch

`agent/v54-production-readiness-hardening`

Accepted research parent remains V53 HEAD:

`4b7b5a348e9412d2d34c827f86eae37904ddc627`

`main` is stale for current V50–V55 work and must not be used as the recovery source.

## Project objective

`LIVE_RESEARCH_ALLOWED=1`

`LIVE_DEPLOYMENT_TARGET=1`

The project targets production/live deployment after sufficient technical and
operational evidence. Candidate research is frozen. Current work is production
readiness, not another alpha tournament.

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

### V53 natural broker-DEMO confirmation — CLOSED BY WAIVER

Accepted recovered ZIP SHA256:

`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

Formal classification:

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

This is not `DEMO_CONFIRMATION_PASS`. Do not force a signal or extend the waiting gate.

## V54 production-readiness hardening

V54 inherited the exact V53 candidate and V49/V50 broker execution architecture. It
added:

- stop-risk sizing cap;
- daily/session loss protection;
- peak-equity drawdown protection;
- spread guard;
- stale broker-tick and stale strategy-state guards;
- disconnect handling;
- repeated broker-reject halt;
- SL/TP presence validation;
- deterministic broker/virtual reconciliation;
- request/retcode/deal audit trail;
- MetaQuotes push notification path;
- immutable snapshot evidence ZIP;
- fail-closed rollback/runbook.

No alpha threshold was changed.

## V55 account-agnostic production runtime

V55 is now the implementation layer to use going forward. It is built as a thin
post-processing envelope over V54, so the candidate and execution mapping remain
unchanged.

Runtime identity:

- `XAUUSDm M15`;
- owned magic `550055`;
- maximum one owned strategy position;
- candidate `v52_b4_or_b3_trend_bos`;
- no Martingale;
- no grid;
- no doubling after loss.

Account model:

`V55_ACCOUNT_MODEL=DEMO_AND_REAL_SAME_BINARY`

DEMO is active by default. The same generated EA can be loaded on REAL. On REAL, new
risk is fail-closed unless both explicit arming inputs are present:

- `InpV55AllowRealAccount=true`;
- `InpV55RealArmCode=V55_REAL_ARMED`.

An unarmed REAL instance is `REAL_OBSERVE_ONLY`: it cannot open new positions. Account
login/mode are pinned at initialization; changing account while the EA remains running
forces a halt/restart requirement.

V55 also derives broker/account constraints at runtime:

- min/max/step volume;
- broker stop-distance level;
- freeze-level telemetry;
- leverage telemetry;
- loss-per-lot via `OrderCalcProfit`;
- required margin via `OrderCalcMargin`;
- available margin via `ACCOUNT_MARGIN_FREE`;
- inherited filling mode by symbol.

Daily-loss/peak-equity terminal globals are account-scoped so trial and REAL accounts do
not share protection state.

Canonical launcher:

`bash runtime/v55_account_agnostic/START_V55_ACCOUNT_AGNOSTIC_GIT_BASH.sh`

Default execution mode is DEMO. REAL mode uses the same source/EX5 and an explicit
startup preset; no account login/password/server credential is committed or injected by
the runner.

Authoritative long-term semantics: `docs/adr/ADR-057-account-agnostic-demo-real-runtime.md`.

## CI recovery

The old V53 workflow was blocked by an over-broad policy scanner and an unconditional
historical V29 `exit 86`. Those defects were repaired. Full pytest collection then
exposed historical dependency and recovery-contract drift; current work restores those
contracts rather than skipping tests.

Do not claim current HEAD CI PASS until the workflow concludes successfully.

## Current classification

`V50_EXECUTION_PIPELINE=PASS`

`V51_HIGHER_FREQUENCY=KEEP_BREADTH4`

`V52_SOURCE_AWARE=INVALID_DATA_CONTAMINATION`

`V52R_REAL_TICK_REPRO=PASS`

`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

`V54_PRODUCTION_READINESS=IMPLEMENTED`

`V55_ACCOUNT_AGNOSTIC_RUNTIME=IMPLEMENTED_PENDING_CI_WINDOWS_COMPILE`

## Next gate

1. require green GitHub CI on current HEAD;
2. run V55 on the currently logged DEMO/trial account using the default launcher;
3. require MetaEditor `0 errors, 0 warnings`, READY status and immutable startup ZIP;
4. exercise restart/reconciliation/notification fault paths;
5. retain `V53_NATURAL_MAPPING=NOT_OBSERVED` until a natural selected-candidate mapping
   is actually observed;
6. later REAL deployment uses the same V55 source/EX5 with explicit REAL arming, not a
   second strategy fork.

Do not reopen alpha research unless a real implementation defect invalidates the
selected candidate or its evidence.
