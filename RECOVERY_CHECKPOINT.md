# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, doubling after loss, or risk escalation above the documented ceiling.

## Canonical local history

Latest local Git commit: `35e325ba293601ce48c98ee6de0077c11994f846` — `research: promote H1 finalists to native rolling gate`.

Complete Git bundle SHA-256: `505f0b6c49c12c6b5de25ab0d0427cea8776aab93e59df98af5b2fcda2fca3a2`.
Source snapshot SHA-256: `3b1f1b34719156b31287839a3d4a5481e9ce71db6c77c8af19f0b2847729d325`.
Next research kit SHA-256: `7c9801fcc7b18e441b0e397dabd0d00e48f7c6ffe99f3cdd4cc11318ccc65e46`.
QualityExitLab uploaded bundle SHA-256: `81832a5917c96f323837e20d9f498c84e401d8e5ab72c6ea690f4910a1757b7d`.

## Accepted prior state

Session preflight remains accepted. The practical decision horizon remains repeated non-overlapping 1–3 month windows. Canonical small-capital analysis uses USD 40 as the maximum initial deposit, with USD 20/30 retained as sensitivity references.

## Quality / Exit Lab V1 — COMPLETE

Integrity: PASS; 34 internal hashes matched. Windows MetaEditor compile: 0 errors / 0 warnings.

Sixteen pre-registered variants x four independent books were evaluated over seven non-overlapping 1–3 month windows. The strongest robust improvement came from H1 trend alignment, not from simply widening TP or tightening SL.

USD 40 / 1.00% virtual research-ceiling results:
- `ema_h1_2atr_2r`: median +17.27%; positive 6/7; >=15% in 4/7; worst -3.33%; best +31.79%; max MTM DD 12.33%; median PF 1.345.
- `trend_h1_2atr_2r`: median +14.84%; positive 7/7; >=15% in 3/7; worst +2.27%; best +23.87%; max MTM DD 15.64%; median PF 1.359.
- `trend_tight_1p5atr_2r`: median +15.64% but worst -6.38% and max MTM DD 20.28%; not promoted.
- `trend_quality_2atr_2r`: positive 7/7, worst +4.80%, but median only +10.58%; stable control, not return finalist.

The virtual H1 books have very low exact entry-time+direction overlap (Jaccard about 0.009) but moderate daily realized-PnL correlation (~0.52). This supports a future shared-risk portfolio test but does not prove diversification.

Important limitation: the virtual QualityExitLab baseline did not reproduce every native rolling cash result exactly. No lab candidate is promoted directly to capital deployment.

## Risk / leverage decision

- 0.50% stop-risk = baseline.
- 0.75% = moderate research overlay.
- 1.00% = aggressive research ceiling only.
- No >1.00% stop-risk research in the current phase.

Higher leverage lowers margin required but does not reduce minimum-lot loss-at-stop. Previous native rolling runs had zero margin rejects, so leverage was not the binding constraint. Do not use leverage as a substitute for expectancy.

## Next gate — H1 Finalist Native V1

Run `scripts/run_h1_finalist_native_v1.cmd` from the V15 one-click kit.

Finalists only:
- `trend_h1_2atr_2r` — stability finalist.
- `ema_h1_2atr_2r` — return finalist.

Keep stop = 2 ATR and TP = 2R frozen. Batch: 2 finalists x 7 non-overlapping 1–3 month windows = 14 native MT5 Strategy Tester runs, XAUUSDm/M15, generated Every Tick, ExecutionMode=0, normalized USD 10,000 risk 0.50%, tester leverage 1:200, dynamic broker-session preflight, tester-only CTrade, external broker orders=0.

After upload, translate native ledgers to USD 40 strict-target books at 0.50%, 0.75%, and 1.00%. If native H1 evidence survives, next research is a shared-risk Trend+EMA portfolio/adaptive-risk overlay rather than a wider parameter grid.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The local source snapshot + complete Git bundle remain the complete-history recovery layer until full source/history mirroring on remote is verified. Never claim remote history sync is complete without verification.