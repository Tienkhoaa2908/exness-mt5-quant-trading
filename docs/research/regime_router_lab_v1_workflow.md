# Regime Router Lab V1 — workflow

## Mục tiêu

Kiểm tra liệu family-specific regime gating và selective routing có nâng expectancy/robust monthly return so với EMA control mà không tăng risk >1% hay tái tạo churn của Opportunity Fusion.

## Catalog

26 candidates, 4 books/candidate, 104 virtual books.

### EMA
- `ema_h1_base`
- `ema_h1_adaptive`
- `ema_h1_skip20`
- `ema_h1_skip22`
- `ema_h1_skip20_short3_r0p5`
- `ema_h1_skip20_short3_r1p0`

### MACD
- base
- H1 gap >=8 ATR
- H1 gap >=10 ATR

### Trend20
- base
- H1 gap >=3 / 5 / 8 ATR

### BOS+FVG
- base
- H1 gap >=4 / 8 / 10 ATR

### Router ablations
- EMA + MACD gap10
- EMA + Trend gap5
- EMA + BOS gap8
- loose
- balanced
- strict
- balanced + adaptive
- balanced + targeted EMA-short exhaustion
- balanced + targeted exhaustion + adaptive

Router cùng hướng sẽ coalesce source; signal đối nghịch cùng bar thì abstain. Một virtual position/book, không stacked risk.

## Books

- normalized 10k @0.5% continuous sizing;
- USD40 @0.5%;
- USD40 @0.75%;
- USD40 @1.0% research ceiling.

## Window

18 tháng: 2025-02 đến 2026-07, reset độc lập từng tháng, 3 chunk sáu tháng.

## Decision metrics

Median/mean monthly return, positive months, >=10/15/20%, worst month, max MTM DD, PF, AvgR, trades, turnover, streak rejects, regime/session rejects, router source mix, 2025 vs 2026 stability.

Không chọn theo best month đơn lẻ. Multiple-testing phải được ghi nhận vì có threshold grid.

## Evidence rule

Các H1-gap/session threshold xuất phát từ V22 trade-ledger conditional diagnostics nên chỉ là hypothesis discovery. V23 phải re-simulate trong Strategy Tester trước khi dùng làm performance claim.
