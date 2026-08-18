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

Controls: EMA H1 skip20; MACD H1 gap10; BOS/FVG H1 gap8; Trend20 H1 gap5; EMA+BOS8 router.

Slow-momentum controls: server 00:00/08:00 decisions; 16h+24h trailing-return directions agree; 8h timebox; stop2ATR; TP4R; with/without peak-lock.

Adaptive candidates: EWMA hl8 threshold 0; EWMA hl8/10/12 threshold +0.05R; fast5-vs-slow20 divergence >=0.30R change-severity probe with +0.05R minimum score.

Only normalized control-book realized R updates expert scores. Change severity alters adaptation speed only; mechanical experts own direction. Validated range ML remains context/telemetry, not a hard fixed router.

Stateful runner: 3 sequential six-month chunks Feb-2025→Jul-2026; independent monthly PnL/risk resets; adaptive state carried across chunks; retry restores exact pre-chunk state; checkpoint reuse requires matching fingerprint plus adaptive-state snapshot; bar-feature export off.

## V29.0 Windows compile incident — MUST NOT REPEAT
The first V29.0 kit is BROKEN and must not be run again. User Windows MetaEditor produced 100 errors / 50 warnings before Strategy Tester started.

Root cause: the adaptive refactor retained calls to five shared runtime utility helpers but dropped their definitions: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. `ReadOne` caused the first large compiler cascade. A separate runner bug used `$MyInvocation.MyCommand.Path` inside the diagnostic function, which became null and prevented diagnostic ZIP creation.

V29.1 fixes both root causes:
- restores all five helper implementations from the previously Windows-compiled V28 implementation;
- diagnostic and main runner root use stable `$PSScriptRoot`;
- diagnostic format is V29-specific;
- adds mandatory regression tests that runtime helper calls have definitions and that the diagnostic path does not depend on `$MyInvocation.MyCommand.Path`.

Release-gate lesson: delimiter balance, FileWrite limits and safety scans are NOT sufficient compile QA. Future MQL releases must include helper-definition consistency/static symbol regression checks before packaging. Do not represent static QA as Windows compile evidence.

V29.1 local QA:
- pytest 13/13 PASS;
- analyzer/tests py_compile PASS;
- MQL delimiter balance PASS;
- five required helper definitions each present exactly once;
- no called custom helper missing relative to the previously Windows-compiled V28 base;
- executable safety scan PASS;
- internal kit manifest 11/11 PASS;
- ZIP integrity PASS.

V29.1 release SHA-256: `b8176551870b218f47322bae72c7a78be2d0efde8eec7237dab91ab4f8aeb824`.
Hotfix patch SHA-256: `c5f999e546b3aa67dbe704e9dbc90bf62510e2134aea4e8c3c44e5d759c0b65c`, stored at `recovery/v29_1_compile_hotfix.patch`.
Windows MetaEditor 0/0 is still pending until the user runs V29.1.

## Next action after recovery
Never ask the user to rerun V29.0. Give/run only V29.1, then require compile 0 errors / 0 warnings before Strategy Tester evidence is accepted. If V29.1 compiles, run the single 18-month stateful batch and analyze robustness against controls. If it passes, proceed to PAPER/DEMO forward validation. REAL-MONEY LIVE TRADING remains forbidden.
