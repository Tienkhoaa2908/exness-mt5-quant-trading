# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Cập nhật: 2026-08-16.

## Safety invariant

REAL-MONEY LIVE TRADING = FORBIDDEN.

Không Martingale, uncontrolled grid, doubling after loss. Stop-risk research ceiling 1.00%/trade. Virtual lab không deploy trực tiếp.

## Research environment

- Broker research: Exness Technologies Ltd.
- Symbol: `XAUUSDm`.
- Main timeframe: M15.
- Long screening: generated Every Tick; real-tick fidelity gate tách riêng khi coverage phù hợp.
- 18 full monthly resets: 2025-02 đến 2026-07.
- Account-mode constraint Netting vẫn cần xử lý nếu sau này native partial exit.

## Milestone evidence

### Profit Protection V1
EMA peak-lock 50% peak sau +1R, TP4R: median USD40@1% khoảng +6.32%/tháng, max MTM DD khoảng 9.02%.

### Opportunity Fusion V1
Không promote. Fusion tăng turnover/churn nhanh hơn expectancy.

### Churn Control V1
Generic cooldown/rearm không beat EMA control.

### Multi-Factor Edge V1
Không có family mới vượt EMA robustly; hard quality gates over-filter. BB+RSI zero-signal và streak guard V21 không exercise đúng hypothesis.

### Signal Intelligence V1 / V22 — COMPLETE
ZIP runtime SHA-256 `abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`, 22/22 internal hashes PASS, MetaEditor 0 errors/0 warnings, 18 months complete, tester-only và external broker orders = 0.

EMA base vẫn median +6.3236%, 13/18 tháng dương, worst -4.5875%, max MTM DD 9.0171%.

V22 conclusions:
- score3/score4 không discriminate đủ;
- global exhaustion guard đã exercise nhưng làm EMA median giảm;
- meta-labeling LR/GBDT trên telemetry không generalize (AUC gần 0.5);
- regime shift 2025->2026 là vấn đề chính;
- EMA server-hour 20-23 là pathology ổn định;
- H1 EMA50-EMA200 separation đáng test như family-specific regime proxy cho MACD/Trend/BOS.

Chi tiết evidence: `docs/research/2026-08-16_signal_intelligence_lab_v1_analysis.md`.

## Gate kế tiếp — V23

`Regime Router Lab V1`:
- 26 candidates;
- 4 books/candidate = 104 virtual books;
- 18 monthly resets;
- 3 x six-month chunks;
- một output ZIP.

Grid: EMA session + targeted short-exhaustion; MACD gap8/10; Trend gap3/5/8; BOS gap4/8/10; EMA+one và selective loose/balanced/strict routers.

V23 hiện chỉ có static QA. Windows MetaEditor/runtime V23 **chưa PASS** cho đến khi one-click kit chạy trên máy user.
