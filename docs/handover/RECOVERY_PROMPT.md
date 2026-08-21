# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Source of truth

`main` is stale. Continue from branch:

`agent/v39-selective-harvest`

V39 implementation parent:

`97223ae7459ee401651b8e36d53f725854c79d3e`

Accepted V39 evidence was generated from implementation head:

`399a8dede123da525fec6d5242ca78e6f33cf085`

Do not reconstruct state from memory when GitHub/docs/evidence disagree.

Windows recovery must use explicit refspec:

`git fetch --no-tags origin "+refs/heads/agent/v39-selective-harvest:refs/remotes/origin/agent/v39-selective-harvest"`

then:

`git checkout -B agent/v39-selective-harvest refs/remotes/origin/agent/v39-selective-harvest`

Do not use `git clean`; accepted runtime evidence and `.venv` may be untracked.

Runner fixes that must not regress:

- pytest optional with dependency-free static fallback;
- secret scan scans tracked working-tree source/config via `git ls-files -z`, not `.venv/site-packages` or generated outputs;
- V36 offline runner probes `numpy,pandas,torch,sklearn,scipy`, explicit `scikit-learn==1.8.0`, reuses existing `.venv`, and fail-fast checks imports before training.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Never remove tester/live guards.
- No Martingale, uncontrolled grid, or doubling after loss.
- Research stop-risk ceiling <=1.00%/trade.
- Do not raise risk or tune thresholds just to force 15% geometric/month.
- Exact-MT5/PAPER/DEMO promotion requires explicit gates; LIVE remains forbidden.

## Canonical evidence to preserve

V30 source SHA:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

V31.1 ZIP SHA:
`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:
`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

V34/V35 ZIP SHA:
`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted V34 source SHA:
`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

V36/V37 ZIP SHA:
`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

V38 exact-MT5 ZIP SHA:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

V39 Stage-A ZIP SHA:
`27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`

## Accepted baseline / V38

12-month baseline `adaptive_ewma_hl8_thr0`, continuous USD40:

- end $107.43;
- 8.58% geometric/month;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

V38 exact evidence: MetaEditor 0 errors/0 warnings, V34 control reproduction PASS, 1,104 monthly rows, 56,321 trades, summary↔ledger mismatch 0, 260,471 M1 telemetry rows, baseline M1 coverage 563/563.

Universal fast exits remain rejected. TP1R is close to baseline but cuts right-tail winners; +1R remains a decision zone only.

## V36 reproducibility

Accepted/recomputed Transformer48x2 Feb-Jul means:

- future-delta Spearman 0.040294;
- final-R Spearman 0.514812;
- Hold AUC 0.675683;
- Protect AUC 0.677066;
- both AUCs >0.5 in 6/6 months.

Accepted V39-run V36 predictions SHA:

`a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`

Preserve V36 as sequence/tail-state evidence; it is not PnL evidence.

## Accepted V39 Stage A result — HOLD

Bundle integrity: CRC PASS and 9/9 `bundle_manifest_sha256.txt` entries PASS.

Inputs: 129,311 filtered control M1 rows, 563 control trades, 563/563 M1 coverage, 29,514 +1R-zone rows, 283 +1R-zone trades.

Primary `fusion_v36_m1` lane:

- 6 folds;
- 17 first triggers;
- 14.655% coverage;
- 3/6 positive avoided-giveback months;
- mean monthly avoided giveback +0.120864R;
- mean monthly false-big-winner rate 32.0%;
- mean giveback AUC 0.5834;
- mean tail AUC 0.6117;
- final status: **STAGE_A_HOLD**.

Gate failures: trigger count <30, positive months <75% (needed 5/6), false-big-winner >20%.

Additional warning: pooled 17-trigger mean avoided giveback is -0.04524R and pooled false-big-winner rate 41.18%. Do not replace preregistered gate with this statistic; use it only as diagnosis.

`m1_only` also HOLD: 59 triggers, 38.31% coverage, mean monthly avoided -0.14491R, 2 positive months, false-big-winner 39.72%.

Full result document:

`docs/research/v39_selective_harvest_stage_a_result.md`

## Root-cause and next research contract

Do not promote V39 to exact-MT5 Stage B.

Do not sweep V39 score quantile, `p_hold`, source/direction filters, or risk on Jan-Jul 2026 to force PASS.

Observed failure pattern indicates target/action mismatch: V39 labels eventual giveback and future maximum separately, but an immediate exit decision needs first-passage event order from the current mark. Several false-big-winner triggers were eventually giveback-prone yet first extended strongly into the right tail.

Next research should be preregistered as a structural target redesign:

- decision zone stays current R >= +1R;
- model whether a protective giveback boundary is hit before a tail-extension boundary from each current state;
- use first-passage / competing-risk event ordering, not another threshold sweep on V39 labels;
- keep first-trigger-per-trade and explicit false-tail protection;
- distinguish retrospective feasibility on V39 development months from genuinely fresh prospective evidence;
- no risk increase.

Do not source-gate or direction-gate from the 17 V39 fusion triggers: SLOW_MOM/EMA and SHORT concentration is diagnostic only and sample is too small for production filtering.

## Decision stack

- Baseline: KEEP/control.
- DeepMLP keep60: KEEP frozen risk-efficiency evidence.
- V36 Transformer: KEEP.
- SMC: research-only specialist.
- V35 generic router: REJECT.
- V37 generic SMC gate: REJECT/redesign.
- V38 universal fast exits: REJECT.
- V39 selective harvest: HOLD/redesign target.
- 15% geometric/month: aspirational, not an acceptance override.

## One run -> one ZIP

Every important run must output one ZIP with `bundle_manifest_sha256.txt`. Verify outer SHA, CRC, internal manifest, evidence head/branch, and summary before accepting. Do not ask for screenshots when the bundle is sufficient.
