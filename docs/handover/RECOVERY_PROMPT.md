# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật an toàn
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit secret.
- Không gọi `order_send`/native broker order để test.
- Stop-risk research ceiling 1.00%/trade.

## Luật giao tiếp với user — MUST READ / MUST PRESERVE
- User không muốn thấy code Python nội bộ, scratch code, code đóng gói artifact, tool payload hoặc implementation plumbing xuất hiện trước/sau câu trả lời.
- Không trình bày code nội bộ chỉ vì tool đã chạy. Chỉ hiện code khi user chủ động yêu cầu xem code.
- Phần trả lời user ưu tiên DONE / EVIDENCE / DECISIONS / ISSUES / NEXT khi phù hợp; file, SHA-256, thao tác và chẩn đoán.
- Tooling nội bộ phải chạy âm thầm.
- Yêu cầu này phải được giữ sau mọi recovery.

## V28 is CLOSED as a fixed-router hypothesis
Latest V3 diagnostic SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`:
- V2 partial recovered: 671 rows;
- V3 partial: 38 rows;
- last_error=0;
- combined calendar with prior V27/V1 data: 25,017 deduped values, USD coverage through 2026-06-15.

Do NOT ask the user for another Economic Calendar export. Enough data exists for later confirmation.

Later Mar-May confirmation, without retuning 0.25:
- base range model mean Spearman ~0.60263;
- event-aware ~0.60042;
- calendar incremental uplift ~-0.00221.

Interpretation: the core cross-asset range model generalizes; incremental calendar uplift does not persist.

Fixed low25 V28 routing is REJECTED:
- EMA skip20 low25 later AvgR ~+0.2704, high25 ~-0.3137;
- router EMA+BOS8 low25 ~+0.3213, high25 ~-0.2445.
This reverses the earlier low25->MACD hypothesis.

**Do not run or ask the user to run `mt5_quant_v28_event_regime_replay_lab_one_click.zip`.**

Direction classifier remains modest and family veto unstable. EMA meta-labeler also fails later confirmation. ML/calendar do not own direct Buy/Sell.

Full report: `docs/research/2026-08-19_v28_later_confirmation_router_rejection_v29_direction.md`.

## Current gate — V29 Adaptive Change-Point + Multi-Horizon Expert
No more user data collection now. Work offline until a single replay catalog is frozen.

Promising new expert screening:
- decisions at server 00:00 and 08:00;
- 16h and 24h trailing-return directions agree;
- 8h maximum hold;
- 2 ATR stop; TP4R;
- M15 AvgR ~+0.112R in 2024, +0.161R in 2025, +0.147R in 2026.

Longer M30 history shows this expert is regime-dependent: negative in 2022, near flat in 2023, stronger from 2024 onward. Never promote it as always-on from screening alone.

V29 architecture:
1. validated continuous ML range score remains state/context only;
2. add slow multi-horizon momentum as a separate shadow expert;
3. EMA/BOS/MACD/Trend remain shadow experts;
4. changepoint severity should control forgetting/adaptation speed, not hard direction;
5. use online expert tracking / switching-cost-aware allocation and downside/turnover penalties;
6. generic fast shock reversion is not stable enough and remains experimental;
7. perform offline screening first, then one Strategy Tester replay batch.

Literature direction: Wood/Roberts/Zohren slow-momentum/fast-reversion + CPD; Adams/MacKay online changepoint detection; fixed-share/tracking-best-expert online learning; Deep Momentum Networks/Momentum Transformer. These are architecture references, not XAU performance evidence.

## Validation discipline
- chronological walk-forward only;
- no random CV;
- no same-sample threshold promotion;
- partial Aug-2026 already inspected, not pristine;
- final V29 candidate must return to MT5 tick-level replay before promotion;
- LIVE remains forbidden.