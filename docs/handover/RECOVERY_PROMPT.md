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
- Không trình bày code nội bộ chỉ vì tool đã chạy. Chỉ hiện code khi user chủ động yêu cầu xem code.
- Phần trả lời user phải ưu tiên: DONE / EVIDENCE / DECISIONS / ISSUES / NEXT khi phù hợp; file tải/chạy; SHA-256; hướng dẫn thao tác; chẩn đoán cụ thể.
- Tooling nội bộ phải chạy âm thầm. Không biến private/internal implementation details thành output user-facing.
- Đây là yêu cầu trực tiếp của user ngày 2026-08-18 và phải được giữ sau mọi recovery.

## Current gate — V28 event-aware regime router
V27 recovery complete: user ZIP SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, manifest 5/5 PASS, 24,085 calendar rows. Calendar signal is mainly USD high-impact schedule/proximity for future range, not surprise-heavy direction.

V28 event-aware range model evidence:
- 13 OOS months Feb-2025 → Feb-2026;
- LightGBM 2h+4h range score mean Spearman ~0.5493, positive 13/13;
- paired base ~0.5376 vs event-aware ~0.5497, uplift +0.01210, bootstrap 95% CI above zero;
- XGBoost/CatBoost similar but not better enough to justify complexity;
- TCN event-aware improves over price-only TCN but stays below trees;
- PatchTransformer rejected at current sample scale.

Only natural low-range quartile 0.25 is pre-registered for stateful replay. Do not tune more bands on the same sample.

Trade-ledger screening:
- EMA skip20 low25 near-zero/negative in early and later partitions;
- MACD gap10 low25 stays positive in both partitions.
- Hypothesis: low predicted range routes away from EMA toward MACD; high/mid regimes retain EMA/BOS family logic.

V28 replay kit static QA 6/6 PASS; Windows runtime pending.

## USD calendar later-confirmation top-up
V1 runtime ZIP SHA-256 `e7ca5d14200f89a3c11d8b49144ddd33c9f9d69654e55bf84912472a91fda337`:
- internal bundle hashes 6/6 PASS;
- MetaEditor 0 errors / 0 warnings;
- requested 2026-03-01 → 2026-08-18;
- only 304 rows, coverage 2026-03-02 → 2026-03-31;
- only 1/6 chunks succeeded;
- 5 chunks timed out with MQL5 ERR_CALENDAR_TIMEOUT=5401;
- status `partial`, therefore do NOT treat V1 as Mar-Jul confirmation.

V2 hotfix:
- resume at 2026-04-01;
- 1 day per CalendarValueHistory request;
- up to 5 bounded retries/day;
- hard watchdog 45 minutes, idle watchdog 5 minutes;
- runner must reject partial output unless `currency_coverage.status=ok`, `chunks_failed=0`, and metadata `failed_chunks=0`;
- authoritative output stays in local `OUTPUT` next to CMD;
- release SHA-256 `e3aaa4d09dc2a23480006426c3ce86fd802c05853ae72eb71a47bb6969f34de6`;
- local static QA 6/6 PASS.

When V2 output arrives, merge March V1 + Apr-now V2, dedupe by value_id/event_id/time, then score Mar-Jul later period **without retuning threshold 0.25 first**. Only after that should V28 stateful MT5 replay run.

## ML validation discipline
- chronological walk-forward;
- no random CV;
- do not let ML/calendar own direct Buy/Sell without stable OOS evidence;
- partial Aug-2026 has already been inspected and is not pristine for tuning;
- any finalist must return to MT5 tick-level replay before promotion;
- LIVE remains forbidden.
