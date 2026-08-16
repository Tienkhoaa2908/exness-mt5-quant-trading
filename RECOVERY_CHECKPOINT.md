# Recovery checkpoint — 2026-08-16

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Current work is offline research and MT5 Strategy Tester/demo only. No Martingale, uncontrolled grid, doubling after loss, or risk escalation above the documented ceiling.

## Canonical local history

Latest local Git commit: `5c6a992f9c1ebed3034367b6d666bfbe6bef4fe6` — `docs: checkpoint opportunity fusion kit`.

Complete Git bundle SHA-256: `a52b51b035aae82d776165e3d7ccbebad95fe6dc0543cfe3ba45e48610514e28`.
Source snapshot SHA-256: `9cad96fee4ea443e96d135d866516f4f7a93e6591f565c3135e499c79f59c157`.
Next research kit SHA-256: `6a1ea07e320ca57747337b4f07da9e45ebd1faa4998286d44d62bf058b6de3ad`.
Uploaded Profit Protection Lab V1 ZIP SHA-256: `13b61b630046fde11ed05b252781cc08f8cc90e56041cdccd284722300345731`.

## Monthly objective

Canonical practical horizon remains one full calendar month. USD 40 is the maximum intended first-deposit research balance. The 15–20% monthly figure is an aspiration/hit-rate metric, not a guarantee or a reason to raise risk blindly. Approved stop-risk research ceiling remains 1.00% per trade.

## Profit Protection Lab V1 — COMPLETE

Integrity: 22/22 internal hashes PASS. Windows MetaEditor compile: 0 errors / 0 warnings. Three six-month chunks covered 18 independent months from 2025-02 through 2026-07. The lab remained tester-only with virtual books and `external_broker_orders=0`.

Best practical exit candidate at USD40 / 1.00% research ceiling:
- `ema_h1_lock_50pct_peak_after_1r_tp4r`;
- median monthly return +6.32% (~+$2.53 on USD40);
- positive 13/18 months;
- >=15%: 0/18; >=20%: 0/18;
- worst -4.59%; best +14.74%;
- max MTM DD 9.02%; median PF ~1.476.

The user's observed profit-giveback failure mode was confirmed quantitatively. EMA fixed-2R control had 71/271 trades that reached at least +1R and later finished non-positive; the EMA peak-lock candidate reduced this count to zero. Trend fixed-2R had 83/298 such cases; peak-lock likewise reduced it to zero.

Profit protection materially improves capital capture but still does not robustly meet the 15–20% monthly aspiration. Exit micro-optimization alone is therefore not the next step.

## Opportunity / risk decision

- 0.50% stop-risk = baseline;
- 0.75% = moderate research overlay;
- 1.00% = aggressive research ceiling;
- do not raise the ceiling merely to chase return;
- leverage is not a substitute for expectancy.

The remaining bottleneck is opportunity-adjusted alpha: more independent positive-expectancy opportunities per month without stacking risk.

## Next gate — Opportunity Fusion Lab V1

Run `scripts/run_opportunity_fusion_lab_v1.cmd` from the V19 one-click kit.

Ten candidates x four books, evaluated over 18 independent calendar months using three six-month MT5 generated-tick chunks.

Standalone signal sources:
- EMA H1 pullback/reclaim;
- RSI2 trend reversion regime;
- RSI2 + H1 alignment;
- MACD 8/21/5 regime;
- MACD + H1 alignment;
- Trend H1 breakout.

Fusion candidates combine EMA with RSI2-H1 and/or MACD-H1, plus an all-H1 fusion. All candidates use the same frozen exit champion: initial stop 2 ATR, TP 4R, and after +1R protect 50% of peak R.

Fusion is one-position-at-a-time on XAUUSD. Same-bar same-direction sources become one entry with a source mask; opposite same-bar sources are skipped as conflicts. This prevents same-symbol risk stacking and aligns the virtual design with future Netting execution.

Books:
- normalized USD10k @0.50%;
- USD40 @0.50%;
- USD40 @0.75%;
- USD40 @1.00%.

The new MQL is static-QA PASS locally but is not Windows MetaEditor runtime-PASS until the user's machine compiles/runs it. Any virtual winner must return to native MT5 validation before promotion.

## Netting execution constraint

The current MT5 account header shows Netting. Any future native partial exit or multi-source implementation must detect `ACCOUNT_MARGIN_MODE`, use netting-compatible position-volume reduction, and validate all trade-server retcodes. Do not blindly use hedging-oriented partial-close helpers.

## Reliability

The V19 runner inherits bounded watchdog, 30-second heartbeat, broker-unavailable detection, one retry, LocalAppData checkpoint reuse, and Common Files artifact recovery. A broker synchronization failure must not create an unbounded wait.

## Recovery rule

GitHub is a required checkpoint after every material milestone. The V19 source snapshot + complete Git bundle remain the complete-history recovery layer until full local history mirroring on remote is explicitly verified. Never claim full remote history sync without verification.