# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-21.

## Safety invariants

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Research stop-risk ceiling <=1.00%/trade; no Martingale/grid/doubling.
- Do not remove tester/live guards.
- V41 Stage A is offline/read-only; no MT5/MetaEditor launch and no broker-order path.

## Source of truth

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

Current branch: `agent/v41-baseline-stack-action-value`.

V41 base is the accepted V40 evidence/handover commit:

`cb034e23ef9bf231fc1e1369295098854dcd77d0`.

Do not use `main` for current research. Windows recovery uses explicit refspec and must not use `git clean`, because accepted V36/V38 evidence and Python environments may be untracked.

## Exact baseline / target

Accepted control: `adaptive_ewma_hl8_thr0`, `usd40_r1p0_cent_continuous`.

12-month exact-MT5:

- $40 -> $107.43;
- +168.6% total;
- 8.58% geometric/month;
- max DD 9.90%;
- 563 trades;
- AvgR 0.215R;
- PF 1.501.

15% geometric/month would imply about $214.01 after 12 months from $40. It remains unmet.

## Baseline architecture

`adaptive_ewma_hl8_thr0` is not a neural network. It is a causal performance-weighted mixture of rule-based experts:

- EMA skip20;
- MACD gap10;
- BOS/FVG gap8;
- Trend20 gap5;
- Slow Momentum 16h+24h.

Normalized control-book realized R updates EWMA expert scores with half-life 8; router threshold = 0. The selected expert owns direction. Core strengths are adaptation and breadth. Gaps are delayed realized-R feedback, no direct opportunity-value estimate, no explicit sequence/churn layer, no V36 state integration, and no direct incremental action-value exit controller.

## Accepted evidence stack

- V30 source SHA `4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`; feature availability must be bar timestamp +15m. Expected-R targets beat win/loss but universal/common-state gates were not confirmed.
- V31.1 ZIP `7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`.
- V32 ZIP `3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`; DeepMLP keep60 is frozen risk-efficiency evidence: geo 7.6193% vs baseline 7.6807% on Feb-Jul, DD 7.3639% vs10.8159%, 153 vs222 trades, AvgR .325 vs.240, PF1.833 vs1.558.
- V36/V37 ZIP `7ff4b4b44af6e526f67392361ebcc1268e57352a20f32e3d132c0a9636b4133a`; Transformer Hold AUC .6757, Protect AUC .6771, final-R Spearman .5148, reproducible.
- V38 exact ZIP `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`; universal fast exits rejected.
- V39 ZIP `27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b`; HOLD, eventual-giveback target rejected.
- V40 ZIP `e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2`; HOLD: 65 triggers, coverage42.21%, AUC.5264, static-protect shadow7.55%/month and -14.01R. First-passage alone is not action value.

## V41 contract

V41 keeps the baseline core and evaluates layers independently before integration:

1. Entry expected-R HGB regressor, fixed 60% calibration keep target.
2. Causal sequence/churn features from completed prior trades; targeted rules remain diagnostic only.
3. Accepted V36 probabilities chronology-calibrated and used as in-trade state features; V36 itself not retrained.
4. Direct action-value HGB regression + classification for static protect and selective trail, targeting realized delta R versus baseline.
5. Integrated stack only if component economics justify it.

No test-month threshold tuning. No keep-rate/action-coverage sweep after results. No risk increase.

Full plan: `docs/research/v41_baseline_stack_action_value_plan.md`. Durable decision: `docs/adr/ADR-041-baseline-stack-direct-action-value.md`.

## One run -> one ZIP

Run `runtime/v41_baseline_stack/BOOTSTRAP_V41_BASELINE_STACK_ONE_SHOT_GIT_BASH.sh` or the direct runner. Upload only:

`runtime/v41_baseline_stack/OUTPUT_V41_STAGE_A/v41_baseline_stack_action_value_stage_a.zip`

Bundle must contain manifest, V41 evidence, summary, entry/action folds, action candidates/triggers, stack shadow/metrics, layer audits, source/direction segments, V36 calibration diagnostic, code and tests.

On upload: verify outer SHA, CRC, all manifest hashes, HEAD/branch/input SHA; report exact baseline, every shadow lane, target gap and promotion gate separately. Shadow is never exact-MT5 PnL.
