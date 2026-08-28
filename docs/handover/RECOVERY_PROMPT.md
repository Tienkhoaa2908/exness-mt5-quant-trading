# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Current branch

Authoritative production-readiness branch:

`agent/v54-production-readiness-hardening`

Base accepted V53 HEAD:

`4b7b5a348e9412d2d34c827f86eae37904ddc627`

Do not recover from stale `main`.

## Read first

1. `docs/handover/CURRENT_STATE.md`
2. `docs/adr/ADR-056-v54-production-readiness-safety-envelope.md`
3. `docs/runbooks/V54_PRODUCTION_READINESS_RUNBOOK.md`
4. `docs/research/v52r_real_tick_results_2026-08-26.md`
5. `docs/research/v53_timebox_waiver_results_2026-08-28.md`
6. `docs/adr/ADR-053-real-tick-reproducibility-gate.md`
7. `docs/adr/ADR-054-v53-selected-candidate-demo-confirmation.md`
8. `docs/adr/ADR-055-immutable-snapshot-evidence-packaging.md`

## Frozen evidence

`V50_EXECUTION_PIPELINE=PASS`

Accepted V50 recovered ZIP SHA256:

`587cc102e85f6565b9ad880a757a9bd1ffc901c90d7f9d86c7cdadd0841b7e72`

`V52R_REAL_TICK_REPRO=PASS`

Accepted V52R ZIP SHA256:

`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

Selected candidate:

`RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos`

Historical real-tick comparison:

- breadth4: 819 trades, PF 1.2894, annualized 21.47%, max DD 16.60%;
- TREND+BOS: 951 trades, PF 1.2649, annualized 22.17%, max DD 16.10%;
- frequency uplift: +16.12%.

Generated-tick V52 is invalid because of data contamination. Never use it as promotion
evidence.

Accepted V53 recovered ZIP SHA256:

`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

V53 classification:

`V53_GATE=V53_NO_SIGNAL_TIMEBOX_WAIVER`

`V53_NATURAL_MAPPING=NOT_OBSERVED`

Do not relabel it `DEMO_CONFIRMATION_PASS`, do not wait for another forced timebox and
do not rerun V50 probes.

## V54 engineering contract

V54 wraps the exact V53 candidate and inherited V49 execution adapter. It adds only
production safety/operations hardening:

- one symbol `XAUUSDm`;
- M15;
- magic `540054`;
- max one owned position;
- risk-cap sizing, never scaling above inherited virtual volume;
- daily/session and peak-equity loss protection;
- spread, stale tick and stale strategy-state guards;
- disconnect handling;
- broker reject limit;
- SL/TP validation;
- restart/reconciliation gating on fresh strategy state;
- retcode/deal/transaction audit;
- phone notification path;
- immutable snapshot evidence package;
- rollback runbook.

No Martingale, no grid, no doubling after loss.

Activation semantics on this branch:

`PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE`

`real_money_authorized=0`

The EA retains `ACCOUNT_TRADE_MODE_DEMO`. Do not remove that guard merely to turn a
technical readiness test into a real-money transaction.

## CI recovery fact

V53 HEAD's last `quality` workflow was failure. The policy scanner failed first and an
unconditional historical V29 `exit 86` would have failed later. V54 repairs those
global CI defects without changing historical evidence files.

Do not claim V54 CI PASS until GitHub Actions for the V54 commit is actually green.

## Windows gate

Canonical entrypoint:

`bash runtime/v54_production_readiness/START_V54_PRODUCTION_READINESS_GIT_BASH.sh`

The runner must fail closed on wrong branch, dirty tree, deterministic parent mismatch,
static-test failure, secret-scan failure, MetaEditor compile failure, non-DEMO account,
wrong symbol/timeframe, DLL permission, ownership ambiguity or startup halt.

A successful Windows start must produce an immutable startup ZIP under:

`runtime/v54_production_readiness/OUTPUT_V54/`

Compile/runtime PASS must come from actual Windows output; never fabricate it.

## Next task after recovery

Continue production-readiness verification and operations engineering. Do not reopen
alpha tuning. If a technical defect is found, fix the smallest layer that owns it and
preserve the candidate/provenance chain.
