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

## Current project gate
V27 — MT5 Economic Calendar / event-aware ML-DL data gate.

Trạng thái hiện tại:
- V26 historical MT5 export đã cung cấp cross-asset bars + 17.7M XAU broker ticks.
- V26A cross-asset M30 range model có signal ổn định; direction chỉ modest.
- V1.3 low-TF top-up lấy được M5/M15 nhưng không tạo stable direction alpha; không tiếp tục M1 nếu chưa có evidence mới.
- V27 chuyển sang Economic Calendar vì schedule/event timing là data orthogonal hơn cho XAU.

## V27 recovery COMPLETE

Recovery V2 user upload SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, internal manifest 5/5 PASS, 24,085 calendar rows (~5.72 MB).

CSV defect: 68 rows có `event_name` chứa comma nhưng exporter chưa CSV-escape đúng, tạo 28 fields thay vì 27. Offline parser repair bằng cách nối lại split `event_name`; không drop data. Nếu sửa exporter sau này phải quote/escape string fields.

Calendar coverage partial do historical timeout; event-aware modeling chỉ dùng continuous major-currency segment mid-2024 → Feb-2026.

## V27 event-aware ML evidence

Chronological expanding walk-forward, purge 16h, test Aug-2025 → Feb-2026:
- baseline price/cross-asset range Spearman ~0.5028;
- combined price + calendar ~0.5285;
- uplift ~+0.0257, combined beat baseline 7/7 months;
- calendar-only ~0.3676 and positive 7/7.

Ablation is decisive for research direction:
- baseline + all schedule/proximity ~0.5269;
- baseline + USD schedule/proximity only ~0.5278;
- baseline + non-USD schedule ~0.5004;
- baseline + actual/forecast surprise ~0.5008.

Interpretation: **USD high-impact event schedule/proximity is useful as a future-range/regime clock. Actual-vs-forecast surprise does not add stable range value here.**

Direction remains weak:
- baseline direction AUC ~0.5246;
- combined calendar AUC ~0.5171.
Do not let ML/calendar own Buy/Sell direction.

Trade-ledger join is screening only and rejects a global news blackout. Family behavior differs; calendar score should route/abstain family-specifically.

Full report: `docs/research/2026-08-18_v27_event_aware_calendar_analysis.md`.

## Next research rule
- Freeze event-aware range/regime architecture around USD event schedule/proximity.
- Do not add surprise-heavy macro features just because they are available.
- Do not promote same-sample percentile/quintile thresholds.
- Next meaningful test is later-period event-aware replay with thresholds frozen before evaluation, then MT5 tick-level replay of any finalist.

## ML validation discipline
- chronological walk-forward;
- không random CV;
- partial Aug-2026 đã inspect trong prior V26 work nên không còn pristine để tune;
- ML/DL không được sở hữu direct Buy/Sell nếu chưa có stable OOS evidence;
- model/routing finalist phải quay lại MT5 tick-level replay trước promotion;
- LIVE vẫn forbidden.
