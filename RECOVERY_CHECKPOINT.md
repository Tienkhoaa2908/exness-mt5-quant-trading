# Recovery checkpoint — V22 Signal Intelligence Lab V1

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Safety

REAL-MONEY LIVE TRADING vẫn bị cấm. Chỉ offline research / MT5 Strategy Tester; PAPER/DEMO chỉ sau các safety gate riêng. Không Martingale, uncontrolled grid, doubling after loss, không tháo LIVE/tester guard, không tăng stop-risk vượt ceiling 1.00%/trade và không commit password/token/secret.

## Bằng chứng hoàn tất gần nhất — Multi-Factor Edge Lab V1 (V21)

Output ZIP SHA-256:
`c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`

- internal SHA-256: PASS 22/22;
- Windows MetaEditor: 0 errors, 0 warnings;
- 3 chunk hoàn tất, 18 tháng độc lập 2025-02 → 2026-07;
- 32 candidates × 4 books = 2,304 monthly rows;
- 29,472 executed virtual trades;
- `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`.

`ema_h1_base` USD40@1% vẫn là control mạnh nhất theo median monthly return: +6.3236%, positive 13/18, max MTM DD 9.0171%. Chưa có candidate nào hỗ trợ claim robust 15–20%/tháng.

Các kết luận thiết kế chính:
- hard quality conjunction over-filter: EMA PF/DD tốt hơn nhưng median return giảm ~6.32% → ~2.31%;
- V21 `quality_streak` là no-op trong observed sample: `streak_guard_reject=0`, nên không được gọi là exhaustion hypothesis đã fail;
- rapid SHORT third-entry sau hai same-direction winners vẫn là subset đáng ngờ; global third-trade block sẽ over-filter;
- rank stability 2025 vs 2026 yếu, nên phải siết multiple-testing discipline.

## Gate hiện tại — Signal Intelligence Lab V1 (V22)

Một lần chạy:
- 5 retained families: EMA H1, MACD H1, Trend20 H1, BOS+FVG H1, RSI2 H1 diagnostic;
- 6 pre-registered variants/family;
- 30 candidates × 4 books = 120 virtual books trên cùng tick stream;
- 18 independent monthly resets trong 3 generated-Every-Tick chunks;
- một runner → một ZIP.

Variants:
- `base`;
- `score3`;
- `score4`;
- `score3_exhaust`;
- `score3_adaptive`;
- `score3_exhaust_adaptive`.

Entry telemetry ghi ADX/DI, ATR ratio, candle body, direction-adjusted close location, EMA200 distance, RSI2/RSI14, MACD histogram, H1 EMA gap, server hour, prior profit-streak state, bars since exit và adaptive mode.

Exhaustion V2:
- count consecutive profitable exits cùng hướng dù trade trước có rapid hay không;
- sau streak >=2, same-direction re-entry trong 32 M15 bars (8h) cần ít nhất 1.00 ATR adverse reset;
- reject được đếm riêng bằng `streak_guard_reject`.

Adaptive exit là bounded ablation:
- default vẫn initial stop 2 ATR, TP4R, sau +1R protect 50% peak R;
- chỉ non-RSI2 entry có score>=4 và ADX>=25 dùng 0.75R peak-distance trail sau +1R; TP vẫn 4R.

## V22 evidence status trước Windows run

Static QA hiện tại:
- Python analyzer `py_compile` PASS;
- pytest 9/9 PASS;
- MQL delimiter balance PASS;
- trade/summary CSV argument-count QA PASS;
- tester guard PASS;
- `AllowLiveTrading=0`, `AllowDllImport=0` PASS;
- order-path scan PASS: không `OrderSend`, không `CTrade`, không native/external broker order path;
- secret scan PASS;
- PowerShell parser không có trong Linux environment nên không claim parser/runtime PASS.

**Windows MetaEditor compile/runtime V22 chưa được xác nhận** cho đến khi one-click kit chạy trên máy user. Không fabricated evidence.

## Recovery rule

Đọc `docs/handover/CURRENT_STATE.md`, `docs/handover/RECOVERY_PROMPT.md`, `docs/research/RESEARCH_OPERATING_MODEL.md`, ADR và workflow trước khi thay đổi code. Sau run quan trọng, user chỉ upload ZIP do runner tạo; phải verify manifest/hash trước khi phân tích.

## V22 one-click kit

- File: `mt5_quant_v22_signal_intelligence_lab_one_click.zip`
- SHA-256: `aec1cd45168a671c63183dcbf832dbf768f89de896a5264638d2cf1c2cfcaae0`
- Internal kit manifest: 20/20 PASS.
- Windows MetaEditor/runtime V22 vẫn chưa được claim cho đến khi user chạy kit.
