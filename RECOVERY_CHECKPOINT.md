# Recovery checkpoint — V21 Multi-Factor Edge Lab V1

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING vẫn bị cấm. Chỉ offline research / MT5 Strategy Tester / PAPER-DEMO sau safety gates. Không Martingale, uncontrolled grid, doubling after loss, không tăng stop-risk vượt ceiling 1.00%/trade và không commit secret.

## Bằng chứng mới nhất đã xác minh

Churn Control Lab V1 output ZIP SHA-256:
`2579e7806855bdb608cdc9f3987699ad625bf94dd9494467cea6e388ccd5a9ba`

- internal SHA-256: PASS 22/22;
- MetaEditor: 0 errors, 0 warnings;
- 18 tháng độc lập 2025-02 → 2026-07;
- tester-only virtual books; native/external broker orders = 0.

`ema_h1_control` USD40@1% vẫn là control mạnh nhất theo median monthly return: +6.3236%, positive 13/18, max MTM DD 9.0171%. Generic cooldown/re-arm giảm churn nhưng không cải thiện joint return/turnover/DD đủ để promote.

Sequence diagnostic: 50 trường hợp SHORT thứ ba sau hai SHORT thắng cùng hướng có loss-rate 52%; 41 trường hợp tái vào trong <=4 giờ có loss-rate ~53.7%, AvgR ~-0.109 và aggregate PnL âm. Đây là targeted exhaustion hypothesis của gate kế tiếp.

V21 one-click research kit SHA-256: `ecb0d2acee3c30a2b5e61e79372f48b831a7a293b2957ee63717d74e88cf4c79` (17/17 internal kit manifest entries PASS).

Remote clean-clone recovery payload: `recovery/v21_impl_payload.zip`, SHA-256 `3be6159fa9600820f46d8a025c30d0704482a75d456a01adb9c3db43dc710c7f`. Root `RUN_MULTI_FACTOR_EDGE_LAB_V1.cmd` tự giải nén payload khi source/scripts chưa materialize.

## Next gate

**Multi-Factor Edge Lab V1**:

- 8 signal families;
- 4 bounded filter variants/family;
- 32 candidates × 4 books = 128 virtual books;
- 18 independent monthly resets trong 3 generated-Every-Tick chunks;
- một runner → một ZIP;
- exit đóng băng: 2 ATR initial stop, TP4R, sau +1R bảo vệ 50% peak R;
- stop-risk ceiling 1.00%.

Các family: EMA H1, Trend20 H1, RSI2 H1, MACD H1, Donchian55 H1, Bollinger+RSI range reversion, liquidity sweep H1, BOS+FVG H1. ICT/SMC được chuyển thành rule OHLC cơ học, không coi tên phương pháp là evidence edge.

V21 source/runner/analyzer đã qua static QA và pytest cục bộ; **chưa được phép ghi Windows MetaEditor/runtime PASS cho V21 trước khi user chạy kit trên MT5**.

## Recovery rule

Đọc `docs/handover/CURRENT_STATE.md`, `docs/handover/RECOVERY_PROMPT.md`, `docs/research/RESEARCH_OPERATING_MODEL.md`, ADR và workflow trước khi thay đổi code. Sau run quan trọng, chỉ cần upload ZIP do runner tạo; verify manifest/hash trước khi phân tích.
