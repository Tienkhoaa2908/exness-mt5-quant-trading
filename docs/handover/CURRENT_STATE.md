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
- Current observed account mode có constraint Netting cần xử lý nếu sau này native partial exit.

## Milestone đã hoàn thành

### Profit Protection Lab V1

Peak-lock exit virtual champion:
- initial stop 2 ATR;
- TP4R;
- sau +1R bảo vệ 50% peak R.

EMA USD40@1% median monthly return ~+6.32%, max MTM DD ~9.02%, và loại bỏ failure mode MFE>=1R nhưng realized<=0R trong sample.

### Opportunity Fusion Lab V1

Không promote. Fusion tăng turnover/churn mạnh nhưng giảm robust monthly return.

### Churn Control Lab V1

Uploaded ZIP SHA-256: `2579e7806855bdb608cdc9f3987699ad625bf94dd9494467cea6e388ccd5a9ba`.
Integrity 22/22 PASS. MetaEditor 0 errors / 0 warnings. 18 months complete.

Không có generic cooldown/re-arm nào beat `ema_h1_control` median +6.3236%.

Failure mode mới được định nghĩa rõ:
- sau hai profitable trades cùng hướng, trade cùng hướng thứ ba yếu hơn;
- riêng rapid SHORT third-entry <=4h có loss-rate ~53.7% và average R âm;
- do đó generic cooldown bị thay bằng targeted streak-exhaustion guard.

## Gate kế tiếp

`Multi-Factor Edge Lab V1`.

Một lần chạy:
- 8 signal families;
- 4 filter variants/family;
- 32 candidates;
- 4 books/candidate;
- 128 virtual books trên cùng tick stream;
- 18 independent monthly resets;
- 3 x six-month chunks;
- một output ZIP.

Families:
EMA H1, Trend20 H1, RSI2 H1, MACD H1, Donchian55 H1, BB+RSI range reversion, liquidity sweep H1, BOS+FVG H1.

Variants:
base, quality, quality+targeted streak guard, quality+streak+late-session ablation.

## Evidence status của V21

Source/runner/analyzer đã static-QA trong milestone này:
- Python analyzer py_compile PASS;
- pytest 7/7 PASS;
- MQL brace/parenthesis balance PASS;
- tester guard present;
- không `OrderSend`, không `CTrade`;
- 32-candidate catalog present;
- 8 signal families present.

**Windows MetaEditor compile/runtime V21 chưa PASS** cho đến khi user chạy one-click kit. Không fabricated evidence.

## Recovery

Remote GitHub trước milestone này là recovery mirror chưa chứa full local historical implementation. V21 clean-clone checkpoint lưu implementation tại `recovery/v21_impl_payload.zip`; root CMD tự materialize payload nếu `mql5/scripts` chưa có. Không claim full historical Git sync.

## V21 one-click kit

SHA-256: `ecb0d2acee3c30a2b5e61e79372f48b831a7a293b2957ee63717d74e88cf4c79`. Internal kit manifest: 17/17 PASS.
