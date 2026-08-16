# Multi-Factor Edge Lab V1 — runtime analysis

Ngày: 2026-08-16

## Bundle integrity

- Uploaded ZIP SHA-256: `c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`.
- `bundle_manifest_sha256.txt`: 22/22 hashes PASS.
- MetaEditor compile log: `0 errors, 0 warnings`.
- 3 chunks, 18 independent months, 32 candidates, 4 books/candidate.
- Total trade-ledger rows: 29,472.
- Tester-native orders: 0; external broker orders: 0.

## Kết quả chính — USD40 @ 1% research ceiling

### 1. EMA base vẫn là control tốt nhất

`ema_h1_base`:
- median monthly return: +6.3236%;
- positive months: 13/18;
- worst month: -4.5875%;
- best month: +14.7376%;
- max MTM DD: 9.0171%;
- median PF: 1.47645;
- median trades/month: 34.5;
- median turnover proxy: 149.29x initial capital.

Không candidate nào đạt robust 15–20%/tháng.

### 2. MACD và Trend có alpha nhưng không vượt control

`macd_h1_base`:
- median +4.6544%;
- positive 13/18;
- >=15%: 3/18;
- worst -13.0893%;
- max MTM DD 15.7730%;
- turnover ~195.26x.

`trend20_h1_base`:
- median +3.7755%;
- positive 13/18;
- worst -6.3219%;
- max MTM DD 11.2983%.

Year split cho thấy regime decay mạnh:
- EMA base median 2025 +6.6108%, 2026 +4.9074%;
- MACD base median 2025 +7.0074%, 2026 +1.5381%;
- Trend20 base median 2025 +6.8954%, 2026 +0.0298%.

### 3. Quality filter hiện tại lọc quá tay

EMA quality:
- median chỉ +2.30865%;
- positive 14/18;
- max DD giảm xuống 7.2898%;
- median turnover giảm mạnh còn ~53.38x.

Tức quality layer cải thiện sparsity/turnover/DD nhưng mất quá nhiều expectancy. Không promote quality filter hiện tại.

### 4. Streak guard V21 không được exercise

Mọi `quality_streak` candidate có kết quả và số trades giống hệt `quality` candidate; `streak_guard_reject=0` toàn bộ sample.

Root cause trong source:
- `profit_streak_count` chỉ tăng khi trade thắng kế tiếp bản thân đã được entry trong <=16 bars sau profitable exit trước;
- đồng thời `rearm_satisfied` có thể được reset trước khi đủ điều kiện guard;
- pre-registered failure mode cần guard sau hai profitable exits cùng hướng rồi đánh giá third-entry, nhưng implementation hiện tại đã thêm điều kiện rapid vào quá sớm.

Do đó V21 không phải test hợp lệ của targeted two-win → third-entry exhaustion guard.

### 5. Sequence evidence vẫn xác nhận vấn đề SHORT exhaustion

Với `ema_h1_base`, xét trade thứ ba khi hai trade liền trước cùng hướng đều profitable:
- SHORT third-entry: 50 cases, loss-rate 52.0%, average R xấp xỉ 0;
- rapid SHORT third-entry <=4h: 40 cases, loss-rate 52.5%, average R -0.0863R;
- LONG third-entry: 105 cases, loss-rate 46.7%, average R +0.0910R;
- rapid LONG third-entry <=4h: 61 cases, loss-rate 42.6%, average R +0.1795R.

Failure mode vì vậy có tính direction/regime-specific, không nên dùng cooldown đối xứng cho LONG/SHORT.

### 6. BB+RSI branch không được exercise

Toàn bộ `bb_rsi_*` có 0 raw signals, 0 trades trong 18 tháng. Đây không được tính là strategy failure; branch phải được instrument/debug lại với component counters để biết condition nào làm signal collapse.

### 7. ICT/SMC-style branches chưa chứng minh edge

`bos_fvg_h1_base`:
- median +1.83735%;
- positive 13/18;
- worst -8.6898%;
- max DD 10.9850%.

`liq_sweep_h1_base`:
- median -2.24015%;
- positive 8/18;
- worst -7.7775%;
- max DD 10.9661%.

Không promote liquidity sweep hiện tại. BOS/FVG chỉ giữ làm exploratory component, chưa phải standalone alpha finalist.

### 8. Late-session filter không có hiệu ứng thống nhất

So `quality_streak` với `quality_streak_late20`:
- EMA median giảm ~0.376 điểm %;
- RSI2 tăng ~0.579 điểm %;
- MACD tăng ~0.309 điểm %;
- Trend gần như không đổi.

Kết luận: hour-of-day cần family/direction conditional model, không hard-code global cutoff.

## Decision

Không promote candidate mới từ V21. Giữ `ema_h1_base + peak-lock` làm control research.

Gate kế tiếp phải là **Focused Entry State Lab V2** thay vì mở rộng thêm hàng loạt strategy labels:
1. sửa streak-state machine đúng pre-registered failure mode;
2. tách LONG/SHORT exhaustion;
3. instrument quality components thay vì một boolean gate;
4. debug BB+RSI bằng counters và test threshold ladder hữu hạn;
5. xây score-based entry thay vì all-or-nothing quality gate;
6. thêm regime features: ADX bucket, ATR percentile/ratio, EMA slope, distance-from-regime, candle impulse, session bucket, prior-trade state;
7. giữ EMA/MACD/Trend/BOS-FVG làm main families; liquidity sweep standalone bị demote;
8. frozen exit policy và risk <=1%;
9. one-click, one output ZIP, bounded candidate grid; không optimizer mở vô hạn;
10. finalist sau screening phải quay lại native MT5 + real-tick fidelity gate khi coverage cho phép.

## Safety

REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale, uncontrolled grid, loss doubling hay risk escalation để ép target return.
