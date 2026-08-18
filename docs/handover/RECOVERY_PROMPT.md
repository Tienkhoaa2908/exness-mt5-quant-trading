# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật an toàn
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Luật giao tiếp với user — MUST READ / MUST PRESERVE
- User không muốn thấy code Python nội bộ, scratch code, code đóng gói artifact, tool payload hoặc implementation plumbing xuất hiện trước/sau câu trả lời.
- Chỉ hiện code khi user chủ động yêu cầu xem code.
- Tooling nội bộ chạy âm thầm; user-visible ưu tiên DONE / EVIDENCE / DECISIONS / ISSUES / NEXT, file, SHA-256, thao tác và chẩn đoán.
- Yêu cầu này phải được giữ sau mọi recovery.

## Current gate — V28 event-aware regime router
V26 historical data: cross-asset bars + 17.7M XAU broker ticks. Low-TF M5/M15 giúp range state nhưng không tạo stable direction alpha.

V27 recovered Economic Calendar bundle SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, manifest 5/5 PASS, 24,085 rows. Calendar signal hữu ích chủ yếu là USD high-impact schedule/proximity, không phải surprise-heavy direct direction.

## V28 deep evidence
Event-aware LightGBM range model, chronological expanding walk-forward, purge 16h:
- 13 OOS months Feb-2025 → Feb-2026;
- 2h+4h score mean Spearman ~0.5493;
- 13/13 months positive, worst ~0.3827;
- paired price/cross-asset base ~0.5376 vs event-aware ~0.5497;
- paired uplift +0.01210; bootstrap 95% CI ~[+0.00455,+0.01923].

Matched model benchmark: LightGBM ~0.5534 mean 4h Spearman, XGBoost ~0.5521, CatBoost ~0.5470. Ensembles give only small statistically inconclusive uplift; keep LightGBM primary.

DL: event-aware TCN improves over price-only TCN but remains below tree model; PatchTransformer underperforms. Do not scale DL blindly.

Trade-ledger screening: `ema_h1_skip20` score<25th percentile is near-zero/negative expectancy in both early and later partitions, while `macd_h1_gap10` remains positive. Only the natural 0.25 threshold is pre-registered for replay; broad optimized threshold grids are forbidden.

Full report: `docs/research/2026-08-18_v28_event_regime_deep_research.md`.
ADR: `docs/adr/ADR-034-v28-event-aware-low-quartile-router.md`.

## Pre-registered V28 MT5 replay catalog
Controls: ema_h1_base, ema_h1_skip20, router_ema_bos8, router_ema_macd10, macd_h1_gap10, bos_fvg_h1_gap8.
Event routes: event_ema_skip20_low25_veto, event_low25_macd10_else_ema, event_low25_bos8_else_ema, event_low25_macd10_else_ema_bos8.

Replay is tester-only, 10 candidates × 4 books × 13 monthly resets, frozen peak-lock exit. Local V28 kit static QA 6/6 PASS; release SHA-256 `c9797419fce3b212e85061bd6652d8972589037f2b38c07fe26c4278a62cd829`. Windows MetaEditor/runtime is still pending.

## Fresh calendar action before final V28 confirmation
Existing USD calendar coverage ends around 2026-03-10 while price data extends into Aug-2026. A narrow USD-only top-up from 2026-03-01 onward has been prepared. Release SHA-256 `81d2743c7ae10df21e8b807f2d90c935ef36e965bee28898b84d6a42a96920c2`, static QA 4/4 PASS. Use Mar-Jul as later confirmation without retuning 0.25 first.

## Validation discipline
- chronological walk-forward; no random CV;
- no same-sample threshold promotion;
- direct Buy/Sell ML remains rejected;
- model/router finalist must return to stateful MT5 replay;
- LIVE remains forbidden.