# Trạng thái khôi phục V69 Forward

- V69 research base head: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
- V69 LONG đã **đóng băng**; trong cửa validation forward này không được chỉnh signal, threshold, stop, target, reclaim, separation hay retest.
- SHORT tiếp tục **vô hiệu hóa / rejected**.
- Bằng chứng tiếp theo phải là **prospective forward** trên tài khoản Exness DEMO; không được gọi lại dữ liệu lịch sử đã dùng là untouched holdout.
- REAL-money authorization tiếp tục là **false**.
- Các cửa sổ tháng 6–8/2026 đã được V67 sử dụng; Sep/2025–May/2026 đã được V68/V69 sử dụng làm bằng chứng development. Vì vậy dữ liệu độc lập thật sự cho V69 bắt đầu sau thời điểm strategy được freeze và EA forward khởi tạo thành công trên DEMO.
- Forward candidate: `V69FrozenForwardDemoLong`, `XAUUSDm`, `M15`, fixed lot `0.01`.
- Contract giữ nguyên: planned risk `$0.85–$1.10`, emergency cash-loss guard khoảng `$1.20` best effort, target `+$3.50`, risk/spread `>=4`, separation `>= $1.30`, confirmation age `>=30s`, structural stop cố định, không widening/clamp.
- Harness forward chỉ thay **môi trường thực thi** từ tester-only sang DEMO-only và cô lập telemetry; state machine V69 LONG phải giữ nguyên.
- Không tạo V70 để tune tiếp. Nếu forward evidence thất bại, đóng nhánh kiến trúc V64–V69 thay vì chỉnh tiếp threshold.
