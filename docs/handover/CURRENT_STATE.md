# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Research stop-risk ceiling: <=1.00%/trade.
- PAPER/DEMO chỉ được xem xét sau safety/economic gates; LIVE vẫn cấm.
- Nếu combine agents trên cùng symbol, aggregate stop-risk phải <=1.00%.

## Repository recovery

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

`main` là historical/stale line. V39 implementation parent:

`97223ae7459ee401651b8e36d53f725854c79d3e` — `research: define V39 selective-harvest controller gate`.

Canonical research branch hiện tại: `agent/v39-selective-harvest`.

Windows recovery phải dùng explicit refspec vì một số clone không materialize non-default remote branch:

`git fetch --no-tags origin "+refs/heads/agent/v39-selective-harvest:refs/remotes/origin/agent/v39-selective-harvest"`

sau đó `git checkout -B agent/v39-selective-harvest refs/remotes/origin/agent/v39-selective-harvest`.

Không dùng `git clean`: accepted V36/V38 runtime evidence và `.venv` có thể là untracked local data.

Windows runner lessons đã fix và phải giữ:

- pytest optional; nếu thiếu thì chạy dependency-free static test trực tiếp;
- secret scan dùng `git ls-files -z`, scan tracked working-tree source/config, không quét `.venv/site-packages` hoặc generated runtime outputs;
- V36 offline runner probe đủ `numpy,pandas,torch,sklearn,scipy`; explicit `scikit-learn==1.8.0`; reuse `.venv` và package đã cài; fail-fast trước training.

## Accepted canonical evidence

### V30 feature lake

Accepted source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

35,344 unique M15 rows, 2025-02-01→2026-07-31, 136 raw fields, 0 duplicate timestamps. Causal availability:

`feature_available_time = bar_features.time + 15 minutes`

### V31.1 / V32

V31.1 ZIP SHA:
`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP SHA:
`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Feb-Jul 2026 continuous USD40:

- baseline: end $62.3573, 7.6807% geo/month, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579;
- DeepMLP keep60: end $62.1444, 7.6193% geo/month, DD 7.3639%, 153 trades, AvgR 0.3250R, PF 1.8326.

DeepMLP keep60 remains frozen risk-efficiency evidence; do not retune Feb-Jul 2026.

### V34 / V35

V34/V35 ZIP SHA:
`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted generated V34 source SHA:
`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

12-month continuous USD40 baseline: end $107.43, 8.58% geo/month, max DD 9.90%, 563 trades, AvgR 0.215R, PF 1.501.

V35 generic all-expert router is rejected. SMC remains weak/high-turnover research-only specialist.

### V36 sequence-DL

V36/V37 ZIP SHA:
`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Accepted Transformer48x2 Feb-Jul means:

- future-delta Spearman +0.040294;
- final-R Spearman +0.514812;
- Hold AUC 0.675683;
- Protect AUC 0.677066;
- both AUC heads >0.5 in 6/6 months.

V39 recovery recomputed these metrics essentially exactly. New V36 predictions SHA in accepted V39 run:

`a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`

V36 remains sequence/tail-state evidence, not PnL evidence.

### V38 exact-MT5

Accepted ZIP SHA-256:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Integrity: MetaEditor 0 errors/0 warnings, V34 control reproduction PASS, 1,104 monthly rows, 56,321 trades, summary↔ledger mismatch 0, 260,471 M1 telemetry rows, baseline USD40 M1 coverage 563/563.

Primary continuous-USD40 results:

- Baseline: $107.43, 8.58% geo/month, DD 9.90%, 563 trades, AvgR 0.215R, median hold 157.7m;
- TP0.50R: $65.09, 4.14%, DD 8.50%, 1,069 trades;
- TP0.75R: $90.13, 7.00%, DD 9.42%, 880 trades;
- TP1R: $104.42, 8.32%, DD 10.23%, 750 trades;
- giveback0.25 after0.75R: $96.65, 7.63%, DD 10.11%, 831 trades;
- velocity: $83.41, 6.32%, DD 9.89%, 979 trades;
- timebox30m: $54.25, 2.57%, DD 12.92%, 1,388 trades.

Universal fast exits remain rejected. +1R is a decision zone, not a universal TP.

## Accepted V39 Stage A evidence — HOLD

Accepted uploaded V39 ZIP SHA-256:

`27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`

Bundle CRC PASS; 9/9 internal manifest entries PASS. Evidence head:

`399a8dede123da525fec6d5242ca78e6f33cf085`

V39 inputs: 129,311 filtered control M1 rows, 563 control trades, M1 coverage 563/563, 29,514 +1R-zone rows, 283 +1R-zone trades.

Primary `fusion_v36_m1` lane:

- folds: 6 — PASS gate >=4;
- triggers: 17 — FAIL gate >=30;
- coverage: 14.655% — PASS 3%-35%;
- positive avoided-giveback months: 3/6 — FAIL required >=5/6;
- mean monthly avoided giveback: +0.120864R — PASS >0;
- mean monthly false-big-winner rate: 32.0% — FAIL <=20%;
- mean giveback AUC: 0.5834;
- mean tail AUC: 0.6117;
- status: **STAGE_A_HOLD**.

Important secondary diagnostic: pooled 17-trigger avoided giveback is -0.04524R and pooled false-big-winner rate is 41.18%. This is not the preregistered gate, but shows the positive monthly mean is not broad-based.

Fusion monthly avoided-giveback: Feb +0.9231R (2 triggers), Mar +0.4012R (1), Apr 0 triggers, May +0.1045R (6), Jun -0.5850R (5), Jul -0.2395R (3).

Trigger concentration: SLOW_MOM 9/17, EMA 7/17, MACD 1/17; SHORT 12/17, LONG 5/17. Sample is too small to justify source/direction filtering.

`m1_only` is also HOLD: 59 triggers, 38.31% coverage, 2 positive months, mean monthly avoided -0.14491R, false-big-winner 39.72%.

Full result: `docs/research/v39_selective_harvest_stage_a_result.md`.

## V39 decision / next research

- Do NOT promote V39 to exact-MT5 Stage B.
- Do NOT sweep score quantile, `p_hold`, source/direction filters or risk on the same sample to force PASS.
- Keep baseline and V36 Transformer evidence.
- Root issue is target/action mismatch: V39 predicts eventual giveback and future max separately, while the action needs to know event order from the current mark.
- Next research direction is a preregistered first-passage / competing-risk formulation: from +1R, estimate whether a protective giveback boundary is hit before a tail-extension boundary. This is a structural target redesign, not a threshold tweak.
- V39 Jan-Jul observations become development evidence for that redesign; any future promotion must clearly distinguish retrospective feasibility from fresh prospective evidence.

## Decision stack

- Baseline `adaptive_ewma_hl8_thr0`: KEEP / control.
- DeepMLP keep60: KEEP frozen risk-efficiency evidence.
- V36 Transformer: KEEP sequence/tail-state evidence.
- SMC: KEEP research-only specialist lane.
- V35 generic router: REJECT.
- V37 generic SMC quality gate: REJECT / redesign.
- V38 universal fast exits: REJECT.
- V39 selective harvest: HOLD / redesign target.
- 15% geometric/month: aspirational and unmet; never increase risk or curve-fit to force it.

## One run -> one ZIP

Important runs must produce one ZIP containing `bundle_manifest_sha256.txt`; verify CRC and hashes before acceptance. If bundle evidence is sufficient, do not request screenshots separately.
