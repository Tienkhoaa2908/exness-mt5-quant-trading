# Windows MT5 / Exness — setup nghiên cứu hiện tại

- MT5 + MetaEditor đã hoạt động.
- Broker: Exness Technologies Ltd.
- Symbol: `XAUUSDm`.
- Timeframe: M15.
- REAL-MONEY LIVE TRADING = FORBIDDEN.

## V29.3 workflow

Chỉ dùng verified CI artifact `v29_3_distribution_hardening`. Xóa/để riêng các folder V29.0/V29.1/V29.2 cũ để không double-click nhầm.

1. Giải nén V29.3 vào fresh folder.
2. Double-click root `RUN_ADAPTIVE_EXPERT_LAB_V1.cmd`.
3. Wrapper verify toàn payload bằng SHA-256 manifest và chặn stale `.minute`.
4. Inner V29.2 runner tiếp tục source preflight trước MetaEditor.
5. MetaEditor phải 0 errors / 0 warnings.
6. Nếu compile PASS, runner chạy single stateful 18-month batch.
7. Upload duy nhất ZIP output/diagnostic được chỉ định.

Không chuyển sang live/manual order để test khi lỗi. Không hard-code login/password/token/secret. Stop-risk ceiling 1%.
