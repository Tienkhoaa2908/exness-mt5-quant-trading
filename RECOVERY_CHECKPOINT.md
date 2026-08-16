# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, doubling after loss, or risk escalation above the documented ceiling.

## Canonical local history

Latest local Git commit: `32860fab4064dec44dba321d7fc0e3d96d793074` — `research: add profit-protection exit lab and bounded runner`.

Complete Git bundle SHA-256: `f2d5197b05fdc0722db9bb314465dd8fe34dcdcc29dcc0fcc103530baa418440`.
Source snapshot SHA-256: `8cda02266c091ee7d4d87c9398c448ce6ec398fb541962feba99ffbd6da3735d`.
Next research kit SHA-256: `72c951242b4399b303452ce83c501e8e81df73c9d0dfb033d837a0098f21a92a`.
Uploaded Monthly Quality/Exit diagnostic ZIP SHA-256: `1248ea05553b71f484d186cc640323a918ec715a8b1324c18f17966da0897fc4`.

## Monthly objective

Canonical practical horizon remains one full calendar month. USD 40 is the maximum intended first-deposit research balance. The 15–20% monthly figure is an aspiration/hit-rate metric, not a guarantee or a reason to increase risk blindly. Approved stop-risk research ceiling remains 1.00% per trade.

## Monthly rescreen stall — root cause

The old monthly Quality/Exit runner did not hang because strategy calculations inherently required unlimited time. It completed `2025_02` through `2025_09`, generally in about 1–2 minutes per month. At `2025_10`, terminal logs recorded Exness Trial `Service is not available`, then tester `not synchronized with trade server`; the old runner used unbounded `Start-Process -Wait`, so it could appear frozen while no fresh research artifact was produced.

The old diagnostic packager also failed to preserve checkpoint data correctly and searched an obsolete Common Files path. V18 supersedes both weaknesses.

## Profit-giveback problem

The current H1 designs mostly use static 2 ATR initial stop / 2R TP geometry. A trade can therefore reach meaningful unrealized profit and later give back much of it before the fixed exit fires. This is now measured explicitly instead of inferred visually.

## Next gate — Profit Protection Lab V1

Run `scripts/run_profit_protection_lab_v1.cmd` from the V18 one-click kit.

The lab keeps the two H1-aligned entry families fixed and varies exit/profit protection only. Two families x eight pre-registered exit policies = 16 candidates, each with four independent books: normalized USD10k @0.50%, and USD40 @0.50%, @0.75%, @1.00%.

Exit policies include fixed 2R control, early break-even, fixed profit locks, stepped locks, peak-distance trailing, percentage-of-peak lock and partial-profit logic. Initial stop remains 2 ATR for all candidates.

Per-trade path evidence includes MFE, MAE, realized R, MFE-to-exit giveback, capture efficiency and the count of trades that reached >=+1R but finished <=0R.

Runtime is reduced to three six-month MT5 starts while the EA performs 18 independent monthly resets internally. The runner adds 30-second heartbeat, bounded watchdog, broker-unavailable detection, one retry, checkpoint reuse and recovery from validated Common Files artifacts. Diagnostic packaging now captures the checkpoint and correct `mt5_quant/runs` paths.

This is tester-only virtual screening with no CTrade/native broker orders. Any finalist must return to native MT5 dynamic-stop/partial-close validation before promotion.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The V18 source snapshot + complete Git bundle remain the complete-history recovery layer until full local history mirroring on remote is explicitly verified. Never claim full remote history sync without verification.