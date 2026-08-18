# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety invariant
REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research labs.

## User-facing requirement — MUST PRESERVE
Không hiển thị Python nội bộ, scratch/artifact-packaging code, tool payload hoặc implementation plumbing nếu user không yêu cầu. Tooling chạy âm thầm; user-visible chỉ cần kết luận/evidence/file/SHA/thao tác/lỗi/bước tiếp theo.

## Data state
- V26: cross-asset bars + 17.7M XAU broker ticks.
- Low-TF M5/M15 and raw ticks add range/execution information but no stable direct-direction alpha.
- V27 Economic Calendar recovery: SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`, 24,085 rows.
- V28 USD top-ups are partial but sufficient for later confirmation; calendar extraction is now CLOSED.
- Latest V3 diagnostic SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`: V2 partial 671 rows + V3 partial 38 rows, `last_error=0`.
- Combined/deduped calendar: 25,017 values; USD coverage reaches 2026-06-15.
- Do NOT request another calendar exporter from the user.

## V28 later confirmation
Frozen-through-Feb cross-asset range model scored Mar-May 2026 without retuning the 0.25 threshold.

Mean monthly future-range Spearman:
- base price/cross-asset ~0.60263;
- event-aware ~0.60042;
- incremental calendar uplift ~-0.00221.

Conclusion: **range prediction generalizes strongly; incremental calendar uplift does not confirm in Mar-May.**

The fixed V28 low25 family mapping fails later confirmation:
- `ema_h1_skip20` low25 AvgR ~+0.2704 vs high25 ~-0.3137;
- `router_ema_bos8` low25 ~+0.3213 vs high25 ~-0.2445.
This reverses the earlier low25->MACD premise.

**V28 fixed low25 replay is REJECTED. Do not ask the user to run `mt5_quant_v28_event_regime_replay_lab_one_click.zip`.**

Direction ML remains modest (~0.529 / 0.514 / 0.520 AUC Mar/Apr/May) and family vetoes are unstable. EMA trade meta-labeler also fails confirmation (~0.516 combined AUC). ML must not own direct Buy/Sell.

Full report: `docs/research/2026-08-19_v28_later_confirmation_router_rejection_v29_direction.md`.

## V29 orthogonal-alpha discovery
A new slow multi-horizon expert has promising screening evidence from existing MT5 bars:
- server decisions at 00:00 and 08:00 only;
- 16h + 24h trailing-return direction agreement;
- 8h maximum hold;
- 2 ATR stop; TP4R.

M15 screening AvgR:
- 2024 ~+0.112R;
- 2025 ~+0.161R;
- 2026 ~+0.147R.

But longer M30 history proves regime dependence: stressed raw expectancy is negative in 2022-2023 and positive from 2024 onward. It is an orthogonal expert, not an always-on replacement.

## Current gate — V29 Adaptive Change-Point + Multi-Horizon Expert
Do not collect more user data now.

Architecture direction:
1. keep ML range score continuous;
2. add slow 16h/24h momentum expert;
3. keep EMA/BOS/MACD/Trend as shadow experts;
4. use change-point severity to alter forgetting/adaptation speed, not hard direction;
5. use nonstationary online expert allocation with switching/turnover/downside penalties;
6. fast-reversion remains experimental because generic shock fading is nonstationary;
7. freeze candidate catalog offline, then give user one MT5 replay batch only.

## Validation discipline
- chronological walk-forward only; no random CV;
- no same-sample threshold promotion;
- partial Aug-2026 was already inspected and is not pristine for tuning;
- new V29 signals are screening until Strategy Tester/tick-level replay;
- do not merge research branches into `main` until corresponding evidence gate passes.