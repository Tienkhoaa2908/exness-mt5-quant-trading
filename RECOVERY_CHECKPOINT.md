# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, loss-doubling, or risk escalation above the documented ceiling.

## Canonical local milestone

Implementation commit: `581ccd26cee29f9faca478b8fd9ecf61d68417b8` — `research: add churn-control gate after fusion turnover`.

V20 recovery artifacts generated from that commit:
- one-click Churn Control kit SHA-256: `e42d4a225cc845b58084d0bc6099d8a4ac1c73b1b913adba04ef956f77b9cf55`;
- source snapshot SHA-256: `9b68dc458ca81e7f4108745bc28a4d5298d5f4ce25391c59aa8dd8301707b281`;
- complete Git bundle SHA-256: `7ae504893c16ce01dbbff946e4c7d86b50ae210c8ee8ec19fa98efc915f47706`.

Uploaded Opportunity Fusion Lab V1 ZIP SHA-256: `1cf1dd45bfe5ee93658f65dec59e72229942a9494f3519a70ace9698b8a7445c`.

## Opportunity Fusion Lab V1 — COMPLETE

Integrity: 22/22 internal SHA-256 entries PASS. Three chunks covered 18 independent calendar months. Tester-only virtual books; no native/external broker orders.

USD 40 @1.00% stop-risk research ceiling:
- `ema_h1_peaklock`: median +6.32%/month, positive 13/18, worst -4.59%, best +14.74%, max MTM DD 9.02%, median 34.5 trades/month.
- `fusion_all_h1_peaklock`: median only +1.41%, positive 10/18, worst -16.16%, max MTM DD 17.41%, median 65.5 trades/month.
- No fusion candidate robustly beat standalone EMA H1.

Sequence-level churn evidence on EMA USD40/1%:
- 607 trades; 589 within-month consecutive pairs;
- 161 winner -> next-trade loser pairs;
- 102 winner -> loser re-entries occurred within four hours;
- all 102 were same-direction re-entries;
- 94/102 followed a profitable `PROTECT_STOP`;
- median gap for that protected-profit -> rapid-loss subset was about 83 minutes.

Turnover proxy (gross entry+exit notional / USD40 starting capital): EMA median ~149x/month; fusion-all ~294x/month. This is turnover intensity, not a fee estimate.

Decision: do not promote Opportunity Fusion. More opportunities increased churn faster than expectancy.

## Next gate — Churn Control Lab V1

Run `scripts/run_churn_control_lab_v1.cmd` from the V20 one-click kit.

Two entry families are retained as controls: EMA H1 pullback/reclaim and Trend H1 breakout. Exit is frozen to initial 2 ATR stop, TP4R, and 50%-of-peak R protection after +1R.

Ten bounded re-entry policies per family (20 candidates total):
- control;
- cooldown after any exit: 4 / 8 / 16 M15 bars;
- cooldown after profitable exit: 8 / 16 bars;
- same-direction re-arm after 0.25 / 0.50 ATR adverse move from a profitable exit;
- 8-bar profit cooldown + 0.25 ATR re-arm;
- max 2 entries/day + 8-bar profit cooldown.

Four books: normalized USD10k @0.50%; USD40 @0.50%, @0.75%, @1.00%. Risk ceiling stays 1.00%. Margin stress stays 1:200.

Required metrics include return, PF, MTM DD, trades/month, gross-notional turnover/start-capital, rapid re-entries, rapid post-profit losses, churn rejects, volume/margin rejects, and monthly hit rates. A rule is not promoted merely for reducing trades; it must improve the return/turnover/drawdown trade-off.

The V20 runner uses three six-month starts, heartbeat, bounded 20-minute watchdog per chunk, broker-unavailable detection, one retry, LocalAppData checkpoint reuse, Common Files recovery, and diagnostic ZIP packaging.

The new MQL is static-QA PASS locally but is not Windows MetaEditor runtime-PASS until the user's machine compiles/runs it. Any virtual finalist must return to native MT5 validation.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The V20 source snapshot + complete Git bundle remain the complete-history recovery layer until full local history mirroring on remote is explicitly verified.