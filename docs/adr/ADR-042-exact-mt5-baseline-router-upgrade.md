# ADR-042 — Upgrade the baseline router under exact MT5

Date: 2026-08-21
Status: Accepted for development research

## Context

The exact 12-month control `adaptive_ewma_hl8_thr0` remains stronger than V39-V41 exit/ML overlays. V41 Stage A was materially negative. Router changes are path-dependent: accepting/rejecting a direction changes realized-R feedback, future expert scores, flat time and later opportunities. Offline shadow PnL is therefore insufficient as the primary judge.

V29/V38 already contain bounded half-life/threshold/change-proxy variants, so V42 must not rerun identical ideas under new names.

A first V42 run exposed a source-provenance problem before MT5 launched: the current V34 builder deterministically produced a different byte SHA than an older V34 acceptance constant. Silently replacing that hash would weaken provenance.

Subsequent Windows attempts exposed runner-only defects before Strategy Tester: CP1252 vs UTF-8 test decoding, Bash `ERR`-trap interaction with `set +e`, and finally a MetaEditor artifact timing race. In the latest attempt MetaEditor rc was 1, but diagnostic listing immediately showed the expected V42 `.mq5`, `.log`, and `.ex5`; therefore compile had completed and the failure was the runner's fixed-deadline postcondition.

## Decision — research mechanism

V42 runs one exact-MT5 batch on 2025-08-01 through 2026-08-01 and appends six router challengers only: HL8 threshold0 with 15m and one 30m sensitivity arm; HL8/10/12 threshold0.05 with 15m; and fast5/slow20 change-proxy with 15m.

The immutable parent is the accepted V38 exact-MT5 ZIP with SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`. The V42 runner verifies its SHA and ZIP CRC, extracts exactly one `V38FastHarvestLab.base.a.mq5`, validates release/tester/router markers, and double-builds V42 from those accepted bytes. V42 must not reconstruct its parent through historical V34/V38 source-builder scripts.

The builder clones exact frozen `SetupAdaptiveRouter(...)` arguments from that accepted V38 parent. V42 changes no expert signal, stop/TP geometry, capital model or stop-risk. The only new mechanism is bounded direction-switch hysteresis. V38 M1/M15 telemetry is disabled to reduce runtime while monthly summary, trade ledger and manifest remain mandatory. The V34 specialist tape and frozen adaptive state are still hash-verified runtime dependencies.

## Decision — Windows execution architecture

Use the same direct tracked-runner shape as successful V32/V34/V38. Runtime shell patch generation/self-modification is rejected and the V42 Python shell patcher is removed.

For a clean full run:

- bootstrap syntax-checks and executes the tracked direct runner;
- existing compile artifacts are checked before deletion;
- compile success is defined by exact V42 source identity + final `Result: 0 errors, 0 warnings` + non-empty EX5, not MetaEditor launcher rc;
- fresh compilation polls the combined log/Result/EX5 postcondition rather than a fixed log-file deadline;
- Windows process rc is captured in Bash conditional context; `set +e` under the global ERR trap is forbidden;
- MT5 success is defined by a new `LATEST` run plus complete manifested outputs, not launcher rc alone.

For the current machine state, because exact V42 compile artifacts already exist, use `RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`. Resume never launches MetaEditor. It requires installed source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`, compiler 0/0 evidence and EX5, then proceeds directly to exact Strategy Tester.

## Gate

A challenger may only be frozen for fresh chronological confirmation if all pass: >=5% ending-equity uplift, >=0.50pp/month geometric uplift, DD <= control+1pp, improved return/DD, >=10 positive months, beats control in >=7 months, worst month >=-5%, turnover <=control+10%, and >=75% control trade breadth.

No post-result retuning on the same 12 months. A pass is not production approval and never authorizes live trading.

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Strategy Tester only; `AllowLiveTrading=0`, no native/external broker-order path, risk ceiling <=1.00% per trade.
