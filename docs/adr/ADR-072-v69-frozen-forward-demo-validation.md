# ADR-072 — Validation prospective DEMO cho V69 đã đóng băng

Ngày: 2026-08-31

## Quyết định

V69 LONG được đóng băng. Không mở V70 để tiếp tục tune strategy từ kết quả development replay của V69.

Cửa bằng chứng tiếp theo là validation prospective forward trên tài khoản Exness/MetaTrader 5 DEMO, dùng đúng semantics của V69 LONG đã đóng băng. SHORT tiếp tục bị loại/vô hiệu hóa. REAL-money authorization tiếp tục là `false`.

## Vì sao không còn historical holdout độc lập

V67 đã sử dụng các cửa sổ tháng 6, 7 và 8/2026, bao gồm các tuần đến 2026-08-29. V68 sau đó dùng Sep/2025–May/2026 làm holdout tương đối so với chuỗi calibration V67. V69 được thiết kế sau khi đã xem kết quả V68.

Do đó không được lấy lại các khoảng lịch sử này rồi gọi là untouched/independent validation cho V69. Bằng chứng độc lập đầu tiên bắt đầu từ dữ liệu thị trường phát sinh sau khi V69 đã freeze.

## Candidate đã đóng băng

V69 research head được chấp nhận:

`0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

V69 evidence ZIP SHA256 được chấp nhận:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Contract LONG cố định:

- symbol: `XAUUSDm`;
- timeframe: `M15`;
- direction: LONG only;
- fixed lot: `0.01`;
- planned structural risk: `$0.85–$1.10`;
- emergency cash-loss guard: khoảng `$1.20` best effort;
- target: `+$3.50`;
- risk/spread `>=4`;
- closed-M1 reclaim không được order ngay;
- favorable post-confirm separation `>= $1.30` tính từ fixed stop;
- tick separation không được order;
- bắt buộc có later retest trở lại cash-risk zone không đổi;
- confirmation age `>=30s`;
- structural stop cố định, không widening và không clamp.

Không threshold nào ở trên được thay đổi trong prospective gate.

## Môi trường forward

Harness phải fail-closed nếu generated source không có strict DEMO-account guard hoặc nếu có bất kỳ dấu hiệu REAL-money authorization được bật.

Bước chuẩn bị được phép:

- build exact V69 LONG source từ frozen builder;
- compile/install source vào MT5 Experts directory;
- archive telemetry V69 forward cũ trước khi bắt đầu sample mới;
- ghi provenance/start metadata;
- package compile/preparation evidence.

Bước chuẩn bị không được phép:

- thay signal, risk, stop, target, reclaim, separation hoặc retest threshold;
- bật SHORT;
- cho phép REAL-money trading;
- dùng `git clean`;
- dùng `stash pop`;
- fallback im lặng sang binary cũ hoặc Python interpreter đã hỏng.

## Cách diễn giải kết quả

Gate này chỉ là independent prospective validation nếu V69 giữ nguyên hoàn toàn trong suốt sample. Có thể xem kết quả giữa kỳ để kiểm execution, nhưng không được chỉnh parameter rồi tính phần dữ liệu sau chỉnh sửa vào cùng sample độc lập.

Nếu forward evidence đạt yêu cầu, V69 LONG được chuyển sang DEMO/paper execution candidate. Nếu thất bại, đóng kiến trúc micro-entry V64–V69 thay vì tiếp tục tune từng threshold.
