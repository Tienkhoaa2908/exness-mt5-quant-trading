# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid hoặc doubling after loss.
- Research stop-risk ceiling <=1.00%/trade.
- PAPER/DEMO chỉ sau explicit safety/economic gates; LIVE vẫn cấm.
- V40 Stage A offline/read-only; không launch MT5/MetaEditor; không broker-order path.

## Repository recovery

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

`main` là stale/historical. Current research branch:

`agent/v40-upgrade-campaign`

V40 branch base là accepted V39 acceptance commit:

`a28146448c4cf8020e6fa1147e39d97506fa08e6`

Windows recovery dùng explicit refspec:

`git fetch --no-tags origin "+refs/heads/agent/v40-upgrade-campaign:refs/remotes/origin/agent/v40-upgrade-campaign"`

sau đó:

`git checkout -B agent/v40-upgrade-campaign refs/remotes/origin/agent/v40-upgrade-campaign`

Không dùng `git clean`; accepted runtime evidence và `.venv` có thể là untracked.

Runner hardening phải giữ:

- pytest optional với dependency-free static fallback;
- secret scan chỉ tracked working-tree source/config qua `git ls-files -z`;
- V36 offline runner probe `numpy,pandas,torch,sklearn,scipy`, explicit `scikit-learn==1.8.0`, reuse `.venv`, fail-fast trước training.

## Accepted evidence stack

### V30 / V31 / V32

V30 accepted source SHA:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

V31.1 ZIP:
`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

V32 ZIP:
`3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`

Frozen V32 risk-efficiency evidence, Feb-Jul 2026:

- baseline: 7.6807% geo/month, DD 10.8159%, 222 trades, AvgR 0.2401R, PF 1.5579;
- DeepMLP keep60: 7.6193% geo/month, DD 7.3639%, 153 trades, AvgR 0.3250R, PF 1.8326.

Decision: KEEP as frozen benchmark; do not retune the same window.

### V34 / V35

V34/V35 ZIP:
`ccffc5b9684821602275e63c3548e95e250a18062a6daa40a46c77178b13c789`

Accepted V34 source:
`8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`

V35 generic router rejected. SMC remains research-only specialist.

### V36

V36/V37 ZIP:
`7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`

Accepted/recomputed Transformer48x2 Feb-Jul:

- future-delta Spearman 0.040294;
- final-R Spearman 0.514812;
- Hold AUC 0.675683;
- Protect AUC 0.677066;
- both AUCs >0.5 in 6/6 months.

V39-run V36 predictions SHA:
`a82d07a81e6ddc9f82d95f37e9bbe4641d1683301b8a31ccbffa99d7b5baf335`

Decision: KEEP as sequence-state evidence; not PnL evidence.

### V38 exact-MT5

Accepted ZIP:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

12-month control `adaptive_ewma_hl8_thr0`, continuous USD40:

- start $40;
- end $107.43;
- total return +168.6%;
- geometric/month 8.58%;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

Universal fast exits rejected:

- TP0.50R 4.14% geo/month;
- TP0.75R 7.00%;
- TP1.00R 8.32%;
- giveback0.25 after0.75R 7.63%;
- velocity 6.32%;
- timebox30m 2.57%.

+1R remains a decision zone, not a universal TP.

### V39 accepted HOLD

Accepted V39 ZIP:
`27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`

Evidence head:
`399a8dede123da525fec6d5242ca78e6f33cf085`

Primary fusion lane:

- 6 folds;
- 17 triggers;
- 14.655% coverage;
- 3/6 positive avoided-giveback months;
- mean monthly avoided giveback +0.120864R;
- mean monthly false-big-winner 32.0%;
- giveback AUC 0.5834;
- tail AUC 0.6117;
- status `STAGE_A_HOLD`.

Pooled warning: mean trigger-minus-final -0.04524R, false-big-winner 41.18%.

Root cause: target/action mismatch. Eventual giveback does not answer which event happens first from current +1R state.

## Current milestone — V40 Upgrade Campaign

V40 is a preregistered structural redesign, not a V39 threshold sweep.

Primary first-passage target from each `unrealized_r >= +1R` state:

- `GIVEBACK_FIRST`: hit `current_R - 0.25R` before tail;
- `TAIL_FIRST`: hit `max(current_R + 0.75R, +2R)` before giveback;
- `CENSORED`: neither before baseline exit.

Primary model:
`HistGradientBoostingClassifier` on causal M1 features.

Chronology:

- train on resolved states fully exited before calibration;
- calibration = trailing 2 calendar months;
- test = next calendar month;
- fixed score threshold = calibration 80th percentile;
- no test-month threshold tuning.

Windows data-schema hardening after first V40 attempt:

- accepted V38 `trades.csv` may already contain `signal_sources`;
- V40 must not blindly merge the M15 `signal_sources` column and create pandas `_x/_y` suffixes;
- canonical entry preserves any non-empty source already present and uses the first M15 source only as fallback;
- regression test explicitly covers this schema and requires no `signal_sources_x` / `signal_sources_y`;
- canonical entry `scripts/v40_upgrade_campaign_stage_a.py` delegates frozen research logic to `scripts/v40_upgrade_campaign_stage_a_core.py` and packages that core into evidence output.

Actions:

- primary `STATIC_PROTECT_0.25R`;
- secondary `SELECTIVE_TRAIL_0.25R`;
- `IMMEDIATE` diagnostic only;
- zero extra entries;
- no initial-risk increase.

Stage-A promotion gate:

- >=5 folds;
- >=30 unique triggers;
- 5%-35% coverage;
- mean AUC >=0.60;
- GIVEBACK_FIRST trigger rate >=60%;
- TAIL_FIRST trigger rate <=25%;
- static-protect shadow delta positive in >=4 test months;
- total static-protect delta R >0.

If PASS: only permission to design frozen exact-MT5 Stage B.
If HOLD: redesign structurally; do not sweep score/barrier/source/risk on same sample.

## Profit reporting contract

Always report separately:

1. exact accepted baseline: $40 -> $107.43, 8.58% geo/month, DD 9.90%;
2. V40 calibrated shadow result: diagnostic only, anchored so baseline shadow reproduces $107.43;
3. target: 15% geo/month, equivalent 12-month $40 -> about $214.01.

15% remains aspirational and unmet until exact-MT5 evidence proves it. Never increase risk or curve-fit merely to force the target.

## Current files

- `scripts/v40_upgrade_campaign_stage_a.py` — canonical Windows entry/schema adapter;
- `scripts/v40_upgrade_campaign_stage_a_core.py` — frozen V40 research core;
- `tests/test_v40_upgrade_campaign_static.py`;
- `runtime/v40_upgrade_campaign/RUN_V40_UPGRADE_CAMPAIGN_STAGE_A_GIT_BASH.sh`;
- `runtime/v40_upgrade_campaign/BOOTSTRAP_V40_UPGRADE_CAMPAIGN_ONE_SHOT_GIT_BASH.sh`;
- `docs/research/v40_upgrade_campaign_plan.md`;
- `docs/adr/ADR-040-first-passage-target-before-exact-mt5.md`;
- `scripts/analyze_mt5_research_bundle.py`.

## One run -> one ZIP

Important V40 run must output only:

`runtime/v40_upgrade_campaign/OUTPUT_V40_STAGE_A/v40_upgrade_campaign_stage_a.zip`

Bundle must include `bundle_manifest_sha256.txt`, summary, fold metrics, first triggers, trade shadow, action/monthly metrics, segment metrics, V36 calibration and `V40_EVIDENCE.txt`.
