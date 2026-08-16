# ADR-028 — Một lần chạy Multi-Factor Edge Lab trước mọi quyết định tăng risk

## Trạng thái

Accepted for research implementation — 2026-08-16.

## Bối cảnh

Churn Control Lab V1 xác nhận rapid same-direction re-entry sau profitable exits là failure mode có thật, nhưng các cooldown/re-arm tổng quát không đánh bại EMA H1 peak-lock control theo robust monthly return. Failure mode mạnh hơn nằm ở điều kiện cụ thể: sau hai profitable exits cùng hướng, trade thứ ba vào lại quá nhanh có expectancy rất thấp hoặc âm, đặc biệt ở subset SHORT đã quan sát.

Đồng thời, yêu cầu vận hành là phải nghiên cứu rộng hơn nhưng giảm tối đa số lần người dùng phải tự chạy MT5.

## Quyết định

1. REAL-MONEY LIVE TRADING tiếp tục bị cấm.
2. Giữ stop-risk research ceiling ở 1.00%/trade.
3. Đóng băng peak-lock exit hiện tại để gate mới nghiên cứu entry quality và signal family, không mở thêm vòng tối ưu exit.
4. Chạy tám signal families đã pre-register trên cùng tick stream: EMA, trend breakout, RSI2, MACD, Donchian55, BB+RSI range reversion, liquidity sweep, BOS+FVG.
5. Test bốn filter variants/family: base, multi-factor quality, quality + targeted two-profit exhaustion guard, và late-session ablation.
6. ICT/SMC phải được chuyển thành định nghĩa cơ học đo được. Không xem tên gọi ICT là bằng chứng alpha.
7. Tất cả orders trong lab là virtual. Virtual finalist phải quay về native MT5.
8. Đánh giá 18 calendar months độc lập và bốn capital/risk books trong cùng ba MT5 chunks.
9. Catalog 32 candidates được xem là pre-registered. Không thêm parameter sau khi đã xem output trên cùng sample; thay đổi mới phải thành experiment version mới hoặc forward gate mới.

## Lý do

Thiết kế này tăng độ rộng nghiên cứu nhưng giảm thao tác thủ công. Nó cũng xử lý đúng observed failure mode bằng conditional state thay vì cooldown đại trà. Pre-registration và family-level ablation giúp giảm, nhưng không loại bỏ hoàn toàn, multiple-testing risk.

## License

GitHub/MQL5 bên ngoài chỉ là research reference. Không copy GPL code. Repo `joshyattridge/smart-money-concepts` có MIT license, nhưng lab này vẫn tự triển khai các định nghĩa OHLC nhỏ, không sao chép code của repo. Repo không có license tương thích rõ ràng sẽ không được copy vào core.

## Hệ quả

Candidate chỉ được promote nếu improvement tồn tại qua independent monthly resets, split 2025/2026, turnover/drawdown constraints và native parity/cost stress sau đó. Một tháng đạt 15–20% không đủ để kết luận.
