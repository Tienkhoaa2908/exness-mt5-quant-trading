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
- Tooling nội bộ phải chạy âm thầm. Yêu cầu này phải được giữ sau mọi recovery.

## V28 is closed
Calendar extraction is CLOSED; do not request more data exports. Latest V3 diagnostic SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`.

Frozen-through-Feb cross-asset range model later Mar-May mean Spearman ~0.60263; event-aware ~0.60042, so incremental calendar uplift does not confirm. Core range model survives as continuous context.

Fixed V28 low25 family routing is rejected because later expectancy reverses. Do NOT run `mt5_quant_v28_event_regime_replay_lab_one_click.zip`. Direct direction ML and EMA trade meta-labeling remain unstable.

Full rejection report: `docs/research/2026-08-19_v28_later_confirmation_router_rejection_v29_direction.md`.

## Current gate — V29 Adaptive Change-Point + Multi-Horizon Expert Lab
No more user data collection. Frozen replay catalog has 12 candidates × 4 books × 18 months.

Controls:
- EMA H1 skip20;
- MACD H1 gap10;
- BOS/FVG H1 gap8;
- Trend20 H1 gap5;
- EMA+BOS8 router.

Slow-momentum controls:
- server 00:00/08:00 decisions;
- 16h+24h trailing-return directions must agree;
- 8h timebox;
- stop2ATR, TP4R;
- no-peak-lock and peak-lock variants.

Adaptive shadow-expert candidates:
- EWMA hl8 threshold 0;
- EWMA hl8 threshold +0.05R;
- EWMA hl10 threshold +0.05R;
- EWMA hl12 threshold +0.05R;
- fast5-vs-slow20 divergence >=0.30R change-severity probe with +0.05R minimum score.

Only normalized control-book realized R updates expert scores. Change severity alters adaptation speed only; mechanical experts still own trade direction. Existing validated range ML remains context/telemetry and is not another fixed hard routing rule.

Stateful runner requirements:
- 3 sequential six-month chunks from Feb-2025 through Jul-2026;
- independent monthly PnL/risk resets;
- adaptive state carried across chunks;
- every retry restores exact pre-chunk state;
- reusable checkpoint must match source/template/chunk fingerprint and have adaptive-state snapshot;
- bar-feature export off for speed.

Static QA: pytest 11/11 PASS; analyzer py_compile PASS; delimiter/header/FileWrite-limit/safety checks PASS. Internal kit manifest 11/11 PASS; ZIP integrity PASS. Windows MetaEditor/runtime pending.

Release SHA-256: `a0a859b42052dca6592c04274b33bccf85ae986f0f235212458fc76eec0ded69`.
Recovery artifact: `recovery/v29_adaptive_expert_lab_one_click.zip.b64`; base64-decode to restore the exact release ZIP.
Research freeze: `docs/research/2026-08-19_v29_adaptive_expert_lab_freeze.md`.

## Next action after recovery
Ask user to run only the V29 one-click Strategy Tester kit and upload its single output ZIP. Do not ask for more exporter runs. Analyze robustness against controls: return distribution, positive months, worst month, MTM DD, AvgR, turnover, source mix, slow-momentum yearly stability and early-vs-late adaptive stability.

If V29 passes, proceed to PAPER/DEMO forward validation. REAL-MONEY LIVE TRADING remains forbidden.
