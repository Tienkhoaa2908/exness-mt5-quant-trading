# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, doubling after loss, or risk escalation above the documented ceiling.

## Canonical local history

Latest local Git commit: `b6ea68c576fc823eb21d34a165da29d87d93158a` — `research: switch H1 validation to monthly horizon`.

Complete Git bundle SHA-256: `d0c4225f39e3fce53dba9424414bbfcb815ed140477361dcec952b9bd7af4eb5`.
Source snapshot SHA-256: `3d474356902db21b46fcad68f3371a65e6e8722980c24ad85dd6f196428a8d9c`.
Next research kit SHA-256: `f1d3444cbd0487cb45cea0bcf186ca01366eb7524540e5b7df056c39c4882d8a`.

## Accepted prior evidence

QualityExitLabV1 completed with integrity PASS. H1 trend alignment was the strongest robust improvement among the pre-registered quality/exit challengers.

Virtual USD 40 / 1.00% research-ceiling results from that lab:
- `ema_h1_2atr_2r`: median +17.27%, positive 6/7, >=15% in 4/7, worst -3.33%, max MTM DD 12.33%.
- `trend_h1_2atr_2r`: median +14.84%, positive 7/7, >=15% in 3/7, worst +2.27%, max MTM DD 15.64%.

These are candidate-selection results, not native deployment evidence.

## Canonical practical horizon — one month

The practical USD 40 decision horizon is now one **full calendar month**. Do not use a three-month aggregate as the primary profitability unit and do not divide a three-month PnL by three as a proxy for monthly performance.

The pending 1–3 month H1 finalist native gate is superseded by `Monthly H1 Native V1`.

Frozen finalists:
- `trend_h1_2atr_2r`;
- `ema_h1_2atr_2r`.

No parameter changes in this gate: 2 ATR stop, 2R TP, closed-H1 EMA trend alignment, dynamic session preflight.

## Monthly H1 Native V1

Batch: 18 full calendar months (2025-02 through 2026-07) x 2 finalists = 36 native MT5 Strategy Tester runs.

Tester contract:
- XAUUSDm / M15;
- generated Every Tick (`Model=0`);
- zero execution delay;
- normalized USD 10,000 deposit;
- native risk-at-stop 0.50%;
- tester leverage 1:200;
- tester-only CTrade;
- external broker orders = 0.

After upload, translate every monthly native ledger to USD 40 strict-target books at 0.50%, 0.75%, and 1.00% stop-risk.

The 15–20% monthly figure is an aspiration/hit-rate metric, not a guarantee and not an optimizer target. Required reporting: positive-month ratio, >=15% hit rate, >=20% hit rate, median/mean/worst/best monthly return, USD profit, participation, native win rate/PF/MTM DD/costs/rejections.

Risk above 1.00% remains outside the current research phase. Higher leverage must not be used as a substitute for expectancy.

## Reliability

The monthly runner uses a persistent LocalAppData checkpoint. Completed month/candidate artifacts are validated and reused after interruption so a late infrastructure error does not force all 36 tests to rerun. Diagnostic packaging includes the checkpoint when present.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The V16 source snapshot + complete Git bundle remain the complete-history recovery layer until full local history mirroring on remote is explicitly verified.