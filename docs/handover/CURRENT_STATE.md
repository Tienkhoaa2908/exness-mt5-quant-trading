# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-16.

## Safety invariant

REAL-MONEY LIVE TRADING = FORBIDDEN.

Không Martingale, uncontrolled grid, doubling after loss. Stop-risk research ceiling hiện tại 1.00%/trade. Virtual lab không được deploy trực tiếp.

## Broker / tester

- Broker research: Exness Technologies Ltd.
- Symbol: `XAUUSDm`.
- Main timeframe: M15.
- Windows MT5 + MetaEditor hoạt động.
- Long screening dùng generated Every Tick; real-tick fidelity gate tách riêng khi coverage phù hợp.
- Current observed account mode có constraint Netting nếu sau này native partial exit.

## Milestones

### Profit Protection Lab V1

Peak-lock virtual exit control:
- initial stop 2 ATR;
- TP4R;
- sau +1R protect 50% peak R.

EMA USD40@1% median monthly return ~+6.32%, max MTM DD ~9.02%.

### Opportunity Fusion Lab V1

Không promote. Fusion tăng turnover/churn mạnh nhưng giảm robust monthly return.

### Churn Control Lab V1

Bundle SHA-256 `2579e7806855bdb608cdc9f3987699ad625bf94dd9494467cea6e388ccd5a9ba`.
Integrity 22/22 PASS. MetaEditor 0 errors / 0 warnings. Generic cooldown/re-arm không beat EMA control.

### Multi-Factor Edge Lab V1 — COMPLETE

Bundle SHA-256: `c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`.

Evidence:
- integrity 22/22 PASS;
- MetaEditor 0 errors / 0 warnings;
- 3 chunks, 18 independent calendar months;
- 32 candidates × 4 books;
- tester-only, native/external broker orders = 0.

USD40@1%:
- `ema_h1_base`: median +6.32%, positive 13/18, worst -4.59%, max MTM DD 9.02%;
- `macd_h1_base`: median +4.65%, positive 13/18, >=15% 3/18, worst -13.09%, max MTM DD 15.77%;
- `trend20_h1_base`: median +3.78%;
- `bos_fvg_h1_base`: median +1.84%.

No candidate robustly reaches 15–20% monthly.

Hard quality conjunction over-filtered. EMA quality increased median PF to ~1.68 and reduced turnover/DD, but median return fell to ~2.31%.

V21 streak variants produced zero `streak_guard_reject`; `quality_streak` equaled `quality`. Vì vậy V21 guard là no-op trong observed sample, không phải bằng chứng exhaustion concept thất bại.

BB+RSI produced zero raw signals; classify as untested.

## Failure mode / diagnosis

EMA base:
- 607 USD40@1% trades, AvgR ~+0.170;
- 155 third entries after two immediately preceding same-direction winners;
- 50 SHORT third entries: ~52% loss rate, average R approximately flat;
- 40 rapid SHORT third entries <=4h: ~52.5% loss rate, average ~-0.086R.

The failure is conditional/asymmetric. Global third-trade blocking would over-filter because MACD and Trend third-entry sequences remain positive on average.

Rank stability between 2025 and 2026 is weak (Spearman ~0.24). Multiple-testing control remains mandatory.

## Gate kế tiếp — Signal Intelligence Lab V1

Mục tiêu: cải thiện khả năng phân biệt tín hiệu thay vì mở thêm một broad indicator zoo.

Các family giữ lại:
1. EMA H1;
2. MACD H1;
3. Trend20 H1;
4. BOS+FVG H1;
5. RSI2 H1 diagnostic.

Sáu variants mỗi family:
- base;
- score>=3;
- score>=4;
- score>=3 + exhaustion V2;
- score>=3 + adaptive exit;
- score>=3 + exhaustion V2 + adaptive exit.

30 candidates × 4 books = 120 virtual books per tick stream.

Entry telemetry includes ADX/DI, ATR ratio, candle body, close location, EMA200 distance, RSI2/RSI14, MACD histogram, H1 EMA gap, server hour, prior streak state and bars since exit.

Exhaustion V2:
- count consecutive same-direction profitable exits regardless of whether the second was rapid;
- after count>=2, next same-direction entry within 8h needs 1.00 ATR adverse reset;
- rejects are explicitly counted.

Adaptive exit có giới hạn:
- base remains 50%-of-peak lock after +1R / TP4R;
- only non-RSI2 entries with score>=4 and ADX>=25 use 0.75R peak-distance trail after +1R, TP remains 4R.

## V22 evidence status

Local static QA:
- Python analyzer `py_compile` PASS;
- pytest 9/9 PASS;
- MQL delimiter balance PASS;
- tester guard PASS;
- template `AllowLiveTrading=0` PASS;
- order-path scan PASS;
- secret scan PASS;
- PowerShell parser unavailable in current Linux environment, so runtime parse is not claimed.

**Windows MetaEditor compile/runtime V22 chưa PASS** until user runs the one-click kit. Không fabricated evidence.

## Recovery

GitHub remains the material milestone checkpoint. Do not claim full historical local Git mirroring unless explicitly verified.

## V22 one-click kit

- File: `mt5_quant_v22_signal_intelligence_lab_one_click.zip`
- SHA-256: `aec1cd45168a671c63183dcbf832dbf768f89de896a5264638d2cf1c2cfcaae0`
- Internal kit manifest: 20/20 PASS.
- Windows MetaEditor/runtime V22 vẫn chưa được claim cho đến khi user chạy kit.
