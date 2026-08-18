# Recovery checkpoint — V29 Adaptive Change-Point + Multi-Horizon Expert

Ngày: 2026-08-19.

REAL-MONEY LIVE TRADING = FORBIDDEN. Stop-risk research ceiling 1.00%/trade. No native broker orders.

## User-facing requirement
Không hiển thị code Python/tooling nội bộ nếu user không yêu cầu. Tooling chạy âm thầm; user-visible tập trung vào evidence, artifact, hash, thao tác, lỗi và bước tiếp theo.

## V28 final decision
Latest V3 diagnostic SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a` contains V2 partial 671 rows + V3 partial 38 rows; last_error=0. Calendar extraction is CLOSED. Do not ask the user to export more calendar data.

Later Mar-May 2026 confirmation without retuning:
- base range Spearman mean ~0.60263;
- event-aware ~0.60042;
- incremental event uplift ~-0.00221.

Core ML range prediction survives strongly, but fixed scalar range->family routing does not.

The old V28 low25 mapping is rejected because later data reverses the conditional expectancy: EMA/router low25 is positive while high25 is negative. **Do not run the existing V28 replay kit.**

Direction ML and trade meta-labeling remain too unstable for direct routing.

## V29 discovery
New slow multi-horizon expert screening:
- server 00:00 / 08:00 decisions;
- 16h + 24h momentum direction agreement;
- max hold 8h;
- 2 ATR stop; TP4R;
- M15 AvgR ~0.112 / 0.161 / 0.147 for 2024 / 2025 / 2026.

Long M30 history shows regime dependence, including negative 2022 behavior. Treat as a shadow expert, not an always-on replacement.

V29 should combine:
- continuous cross-asset range state;
- slow multi-horizon momentum expert;
- existing EMA/BOS/MACD/Trend shadow experts;
- changepoint severity controlling adaptation/forgetting rate;
- nonstationary online expert allocation with switching/turnover/downside penalty.

Generic fast-reversion or fixed CPD direction rules are not promoted.

## Next action
No user action/data collection now. Finish V29 offline catalog and static QA first. Only then provide one MT5 Strategy Tester replay batch. Keep research branches draft/unmerged until evidence gates pass.

Full analysis: `docs/research/2026-08-19_v28_later_confirmation_router_rejection_v29_direction.md`.