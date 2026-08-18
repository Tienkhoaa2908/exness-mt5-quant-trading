# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-18.

## Safety invariant
REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research labs.

## User-facing requirement — MUST PRESERVE
Không hiển thị Python nội bộ, scratch/artifact-packaging code, tool payload hoặc implementation plumbing nếu user không yêu cầu. Tooling chạy âm thầm; user-visible chỉ cần kết luận/evidence/file/SHA/thao tác/lỗi/bước tiếp theo.

## Current gate — V28 event-aware regime router
V26 đã thu cross-asset bars + 17.7M XAU broker ticks. Low-TF M5/M15 và raw ticks hữu ích cho range/execution state nhưng không tạo stable direction alpha.

V27 Economic Calendar recovery thành công: SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, manifest 5/5 PASS, 24,085 rows. Calendar alpha chính là USD high-impact event timing/proximity; surprise-heavy direct direction bị reject.

## V28 deep ML result
Event-aware M30 price/cross-asset + USD event-family clocks, expanding walk-forward with 16h purge:
- 13 OOS months Feb-2025 → Feb-2026;
- 2h+4h LightGBM range score mean Spearman ~0.5493;
- 13/13 months positive, worst ~0.3827;
- paired base ~0.5376 vs event-aware ~0.5497;
- paired uplift +0.01210; bootstrap 95% CI ~[+0.00455,+0.01923].

Model benchmark on matched 4h task:
- LightGBM ~0.5534 mean, min ~0.4020;
- XGBoost ~0.5521;
- CatBoost ~0.5470.
Tree ensembles add only small statistically inconclusive uplift. Keep LightGBM primary.

DL screening: event-aware TCN improves versus price-only TCN but remains below LightGBM; PatchTransformer underperforms. Do not scale DL blindly.

Macro surprise event study shows a separate short post-release impulse for selected growth/labor releases, mainly 15–60m, but sample sizes per event code are too small to promote into trading logic.

## V28 stateful replay hypothesis
Only natural low-range quartile 0.25 is pre-registered.

Trade-ledger screening:
- EMA skip20 score<25% AvgR early ~-0.0365, later ~-0.0056;
- EMA kept >=25% AvgR early ~+0.184, later ~+0.362;
- MACD gap10 low quartile remains positive early ~+0.662 and later ~+0.286.

Hard five-band family winner routing overfits and is rejected.

Pre-registered controls: ema_h1_base, ema_h1_skip20, router_ema_bos8, router_ema_macd10, macd_h1_gap10, bos_fvg_h1_gap8.
Event routes: event_ema_skip20_low25_veto, event_low25_macd10_else_ema, event_low25_bos8_else_ema, event_low25_macd10_else_ema_bos8.

Local V28 replay kit static QA 6/6 PASS; ZIP SHA-256 `c9797419fce3b212e85061bd6652d8972589037f2b38c07fe26c4278a62cd829`. Windows runtime pending.

## Fresh data action
Recovered USD calendar ends around 2026-03-10 while V26 price data continues through Aug. A lightweight USD-only calendar top-up from 2026-03-01 onward is prepared; static QA 4/4 PASS; ZIP SHA-256 `81d2743c7ae10df21e8b807f2d90c935ef36e965bee28898b84d6a42a96920c2`.

Use Mar-Jul later period to validate event-aware model without retuning the frozen 0.25 routing threshold first.

## Validation discipline
Chronological walk-forward only; no random CV; no same-sample threshold promotion; direct Buy/Sell ML rejected; any finalist must return to stateful MT5 replay; research branches stay unmerged until gates pass.