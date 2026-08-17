# V24.1 — MT5 data enrichment release

Ngày: 2026-08-17.

## Mục tiêu

Tận dụng thêm dữ liệu MT5 trong cùng một Strategy Tester run để tăng information density cho ML/DL, không bắt user chạy lại tester cho từng model.

## Thay đổi data layer

Feature lake được mở rộng từ schema V24 ban đầu lên `bar_features_v2_mt5_microstructure_mtf`.

Tick microstructure được aggregate causal theo từng M15 bar từ `OnTick`:
- tick count;
- bid/ask change count;
- up/down mid-price imbalance;
- spread mean/std/min/max;
- mid-price range, absolute path và net move chuẩn hóa ATR;
- inter-arrival time mean/std.

Multi-timeframe context chỉ dùng bar đã đóng:
- M1: return 5/15 phút, realized volatility 15 phút, path efficiency, up fraction, range/ATR;
- M5: ba sub-bar returns, realized volatility, range/ATR;
- H1: return 1h/4h, range/ATR, body ratio, close location.

Có `tick_agg_ready` và `mtf_ready` để phân biệt missing history với giá trị 0 thật. Future labels vẫn không được ghi trong EA; chỉ tạo offline sau bundle upload.

Không dump toàn bộ generated ticks 18 tháng mặc định vì dung lượng lớn và generated ticks không trở thành real broker ticks chỉ vì được export. Real broker tick history sẽ là fidelity dataset riêng nếu terminal có coverage phù hợp.

## Offline ML/DL

Các feature mới được đưa trực tiếp vào tournament tabular/sequence, không chỉ export để quan sát.

## Static QA

- pytest 10/10 PASS;
- analyzer/trainer `py_compile` PASS;
- MQL delimiter balance PASS;
- `bar_features` header/data 97/97 fields, tương ứng 96 feature columns cộng timestamp/month/bar sequence;
- safety scan giữ nguyên tester-only, không `OrderSend`, không `CTrade`, không Martingale/grid/doubling;
- local release kit manifest 26/26 PASS;
- local recovery payload SHA-256 `91f690b78c50bea250c5028867f3ffb87d65b6245f436ee101340f165559efb8`;
- local one-click release SHA-256 `c761a0fef7818dd431039daa3c3d8af46966bb025df709078a6b602463b4016b`.

Windows MetaEditor/runtime cho V24.1 chưa được claim cho đến khi user chạy kit và upload output ZIP.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Stop-risk research ceiling vẫn 1.00%/trade. ML/DL output không được deploy trực tiếp.
