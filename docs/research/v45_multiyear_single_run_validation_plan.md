# V45 Multi-year Single-run Validation Plan

## Objective

Test whether the V44 baseline family remains profitable and stable across older
market regimes without parameter retuning. V45 uses **one** exact MT5 Strategy
Tester invocation and retains monthly outputs for offline month/year/rolling
analysis.

## Frozen candidates

1. `adaptive_ewma_hl10_thr0p05` — primary deployment-validation candidate.
2. `adaptive_ewma_hl8_thr0p05` — annual-return shadow.
3. `adaptive_ewma_hl8_thr0` — accepted control.

No parameter changes are permitted after seeing V45 results.

## Historical protocol

- Symbol: XAUUSDm.
- Timeframe: M15.
- Model: 0, exact MT5 Strategy Tester path used by accepted V38/V44.
- Deposit: $40 USD.
- Leverage: 1:200.
- From: 2022-01-01.
- To: 2026-08-01 (last complete month before the current partial August 2026).
- Exactly one tester invocation.
- The EA writes `monthly_summary.csv`, `trades.csv`, and `manifest.txt` for the
  entire continuous run.

## State protocol — critical anti-look-ahead rule

V44's accepted 2025-08 state MUST NOT be injected into a historical run starting
in 2022. V45 backs up any Common Files adaptive state, deletes the state before
launch, and therefore starts cold. After the tester exits, the pre-V45 state is
restored. The first six observed months are warm-up and are excluded from
readiness metrics.

`LoadAdaptiveState()` in the accepted V38 source first resets adaptive scores;
if the state file is absent it returns false, while `OnInit()` continues. Thus
state-file removal is the intended cold-start semantics, not a guessed shortcut.

## Frozen source

Accepted V38 parent source SHA256:
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

Generated V45 source SHA256:
`36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.

V45 changes release/output/validation markers and disables expensive telemetry
only. Candidate catalog, signals, entry/exit geometry, sizing and risk are unchanged.

## Evaluation

Analyzer reports:

- every monthly return and trade count;
- calendar-year returns and PF;
- rolling 3/6/12-month returns;
- positive-month ratio;
- full-year stability;
- worst month/year/rolling-12m period;
- max MTM DD;
- AvgR / SumR / PF;
- top-10 winner concentration;
- additional 0.02R and 0.05R per-trade friction stress.

Primary HL10 threshold0.05 passes the V45 multiyear gate only if, after warmup:

- >=42 evaluation months;
- >=60% positive months;
- >=3 full calendar years;
- >=75% of full years positive;
- worst full year >=-15%;
- >=75% of rolling 12-month windows positive;
- worst rolling 12-month return >=-15%;
- max MTM DD <=20%;
- PF >=1.20;
- worst month >=-15%;
- net SumR remains positive after subtracting 0.05R per trade.

## Runtime/recovery

The long run has two expensive-stage checkpoints:

- `MT5_DONE.json`: tester finished and run folder identity is known; collection
  can resume without rerunning MT5.
- `DONE.txt`: required tester artifacts were collected; analysis/package can
  resume without rerunning MT5.

Final packaging uses the portable Python SHA256 manifest packager. Packaging
failure never justifies rerunning the multi-year tester.

## Safety

Strategy Tester only. `AllowLiveTrading=0`, `AllowDllImport=0`, no native or
external broker orders, risk unchanged, `LIVE_AUTHORIZED=0`.

A V45 pass advances paper/demo deployment validation. It does not authorize
real-money capital.
