# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-18.

## Safety invariant

REAL-MONEY LIVE TRADING = FORBIDDEN.

Không Martingale, uncontrolled grid, doubling after loss. Stop-risk research ceiling 1.00%/trade. Virtual lab/ML prediction không được deploy trực tiếp.

## User-facing interaction requirement — MUST PRESERVE

- Không hiển thị code Python nội bộ, code dùng để đóng gói artifact, tool-call payload, scratch code hoặc implementation plumbing trước/sau câu trả lời nếu user không yêu cầu xem code.
- Phần user-visible chỉ nên đưa: kết luận, evidence, file tải/chạy, SHA-256, hướng dẫn thao tác, lỗi cần xử lý và bước tiếp theo.
- Khi cần dùng Python/tool để tạo artifact, chạy âm thầm bằng tool; không biến code nội bộ đó thành nội dung hữu ích giả cho user.
- Yêu cầu này phải được giữ ở mọi phiên recovery sau.

## Current data/ML gate — V27 Economic Calendar

V26/V27 research đã đi qua các mốc chính:
- V26 MT5 data export runtime integrity PASS; 876k+ bars và 17.7M XAUUSDm broker ticks đã thu được.
- Cross-asset M30 LightGBM range-regime signal ổn định; direct direction vẫn chỉ modest.
- V1.3 low-TF top-up lấy được XAU M5/M15 + context M5; low-TF tăng range-regime information nhưng không tạo stable direction alpha; không tiếp tục xin thêm M1 lúc này.
- Chuyển sang MT5 Economic Calendar vì đây là data orthogonal hơn cho XAU.

## V27.2 calendar runtime / recovery state

Economic Calendar exporter V27.2 compile PASS 0 errors / 0 warnings và progress thực sự chạy qua nhiều currencies/chunks.

Run dài bị hard watchdog trước khi hoàn tất toàn bộ lịch sử. Diagnostic gần nhất cho thấy đã tới CNY với khoảng 24k rows và 80 chunks, last_error=0. Đây là timeout của runner chứ không phải Calendar API failure.

Partial recovery đầu tiên đọc đúng run và báo `calendar_values.csv` ~5.72 MB nhưng primary ZIP được ghi vào OneDrive Desktop và user không tìm thấy file sau đó. Vì vậy Desktop/OneDrive Desktop không còn được coi là authoritative output path.

Recovery V2 đã thành công. User upload SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, internal manifest 5/5 PASS, recovered 24,085 calendar rows.

CSV QA: 68 rows có dấu phẩy chưa được escape trong `event_name`, tạo 28 fields thay vì 27. Đã repair deterministically offline bằng cách nối lại field `event_name`; không drop row. Future exporter phải quote/escape text field đúng chuẩn CSV.

## V27 event-aware ML result

Dùng continuous major-currency calendar region từ mid-2024, chronological expanding walk-forward, purge 16h, test Aug-2025 → Feb-2026 (7 monthly folds):

- price/cross-asset baseline range Spearman ~0.5028;
- calendar-only ~0.3676, dương 7/7 tháng;
- combined price + calendar ~0.5285, dương 7/7;
- mean uplift vs baseline ~+0.0257 Spearman; combined beat baseline 7/7 months;
- paired t-test p ~0.0106, Wilcoxon p ~0.0156, nhưng n=7 và đây vẫn là screening.

Ablation:
- baseline + all schedule/proximity ~0.5269;
- baseline + **USD schedule/proximity only** ~0.5278;
- baseline + non-USD schedule ~0.5004;
- baseline + actual/forecast surprise block ~0.5008.

Kết luận: giá trị calendar chủ yếu nằm ở **USD high-impact event clock** (`minutes to/since`, event counts upcoming), không nằm ở surprise-heavy macro direction.

Direction không được cải thiện:
- baseline AUC ~0.5246;
- combined ~0.5171.

Do đó mechanical strategy family vẫn sở hữu Long/Short; calendar/ML chỉ làm range-regime routing/abstention.

Trade-ledger screening cho thấy không dùng blanket `no trade near news`: EMA/BOS/Trend phản ứng khác nhau theo regime/event timing. Any quintile/threshold derived from this sample is hypothesis-only until later replay.

Full analysis: `docs/research/2026-08-18_v27_event_aware_calendar_analysis.md`.

## Latest completed strategy runtime — V25 ML Regime Replay

Output ZIP SHA-256 `baff90eccfaac70abaa15b30d6132c535160e2b8ab96b65fd290cba968754078`.

V25 xác nhận ML range score có giá trị chủ yếu như regime/abstention layer: cải thiện AvgR, DD và turnover nhưng chưa tạo return uplift statistically decisive. Không dùng ML trực tiếp làm Buy/Sell owner.

## Validation discipline

- Chronological walk-forward; không random CV.
- Không gọi same-sample threshold tuning là confirmation.
- Partial Aug-2026 đã được nhìn thấy trong V26 screening, nên không còn pristine để tune tiếp.
- Bất kỳ model/routing mới nào vẫn phải quay lại MT5 tick-level replay trước promotion.
- Không merge research branches vào `main` cho tới khi gate tương ứng đạt evidence cần thiết.
