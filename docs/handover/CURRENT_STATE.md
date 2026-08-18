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

Recovery V2 hiện là bản phải dùng:
- primary ZIP luôn được tạo trong `OUTPUT` ngay cạnh bộ recovery đã giải nén;
- script bắt buộc verify file tồn tại, size > 0, ZIP mở được và SHA-256 tính được trước khi báo PASS;
- ghi `OUTPUT_LOCATION.txt` cạnh CMD;
- chỉ thử copy phụ sang Downloads/Desktop/OneDrive Desktop sau khi primary PASS;
- Explorer mở thẳng primary artifact.

Recovery V2 release SHA-256: `04ef083f3600023d1ca0f929612590dd0925270950cd14b83add1ab2f279690f`.

## Latest completed strategy runtime — V25 ML Regime Replay

Output ZIP SHA-256 `baff90eccfaac70abaa15b30d6132c535160e2b8ab96b65fd290cba968754078`.

V25 xác nhận ML range score có giá trị chủ yếu như regime/abstention layer: cải thiện AvgR, DD và turnover nhưng chưa tạo return uplift statistically decisive. Không dùng ML trực tiếp làm Buy/Sell owner.

## Validation discipline

- Chronological walk-forward; không random CV.
- Không gọi same-sample threshold tuning là confirmation.
- Partial Aug-2026 đã được nhìn thấy trong V26 screening, nên không còn pristine để tune tiếp.
- Bất kỳ model/routing mới nào vẫn phải quay lại MT5 tick-level replay trước promotion.
- Không merge research branches vào `main` cho tới khi gate tương ứng đạt evidence cần thiết.
