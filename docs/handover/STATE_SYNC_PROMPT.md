# STATE-SYNC PROMPT — UPDATE GITHUB BEFORE HANDOFF

Dùng prompt dưới đây khi muốn buộc đoạn chat hiện tại tổng kết và cập nhật trạng thái dự
án lên GitHub trước khi kết thúc/chuyển đoạn chat.

---

Hãy thực hiện một **project state synchronization** đầy đủ cho repository:

`Tienkhoaa2908/exness-mt5-quant-trading`

Mục tiêu là để một cuộc trò chuyện mới có thể khôi phục chính xác trạng thái hiện tại mà
không cần tôi kể lại lịch sử.

## 1. Đọc lại nguồn sự thật trước khi cập nhật

Đọc/kiểm tra:

- current remote branch và exact HEAD;
- recent commits;
- exact-HEAD CI/workflow status;
- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- `docs/handover/TURN_SYNC.md`;
- code/runtime/evidence liên quan tới công việc vừa thực hiện.

Không tổng kết dựa vào trí nhớ cuộc trò chuyện nếu GitHub/evidence có thể xác minh.

## 2. Cập nhật canonical handover

Cập nhật tối thiểu:

### `docs/handover/CURRENT_STATE.md`

Phải phản ánh:

- active branch và cách lấy exact HEAD;
- candidate/strategy hiện hành;
- frozen evidence/SHAs quan trọng;
- current runtime/deployment mode;
- việc đã hoàn tất;
- blocker đang tồn tại;
- classification hiện tại;
- next gate chính xác.

### `docs/handover/KNOWN_FAILURES.md`

Thêm/sửa những lỗi mới phát hiện theo mẫu:

- symptom;
- root cause hoặc mức độ chắc chắn;
- evidence;
- fix đã làm;
- regression guard;
- điều tuyệt đối không được lặp lại.

Không ghi phỏng đoán như sự thật.

### `docs/handover/TURN_SYNC.md`

Overwrite bằng turn mới nhất, gồm:

- timestamp;
- user request;
- GitHub/evidence đã đọc;
- thay đổi code/docs;
- test/CI đã xác minh;
- runtime evidence mới;
- unresolved blocker;
- action tiếp theo cho operator.

## 3. Dọn tài liệu

Rà lại các tài liệu recovery/handoff cũ. Nếu tài liệu đã bị supersede và có thể gây nhầm
lẫn:

- chuyển các fact còn hữu ích sang canonical docs/ADR/research;
- xóa file stale/duplicate;
- không xóa ADR hoặc research evidence chỉ vì nó cũ nếu nó còn giá trị provenance.

Mục tiêu là chỉ có **một canonical recovery path** dưới `docs/handover/`.

## 4. Kiểm tra tính nhất quán

Đảm bảo không còn các lỗi tài liệu kiểu:

- active branch cũ;
- SHA cũ được mô tả là hiện tại;
- launcher đã supersede;
- trạng thái REAL/DEMO sai;
- historical replay bị gọi nhầm là independent holdout;
- harness failure bị mô tả nhầm thành strategy failure;
- CI được gọi PASS khi exact HEAD chưa xanh.

## 5. Commit và xác minh

Commit tất cả state-sync changes lên active branch.

Sau commit:

- fetch/verify remote branch HEAD;
- nếu code/runtime contract vừa thay đổi, kiểm relevant workflows trên exact HEAD;
- không đưa tôi lệnh chạy mới nếu exact HEAD/CI chưa đủ điều kiện.

## 6. Kết quả trả về

Trả lời ngắn gọn:

- branch;
- exact HEAD;
- files đã cập nhật/xóa;
- CI status;
- blocker hiện tại;
- next action;
- xác nhận repository đã đủ thông tin để chat mới recovery.

Không thay đổi REAL-money authorization trong quá trình state sync.

---
