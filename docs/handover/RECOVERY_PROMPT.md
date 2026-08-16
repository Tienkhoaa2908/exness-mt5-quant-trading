# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository mục tiêu: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật bắt buộc

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không gửi lệnh tiền thật hoặc tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Stop-risk research ceiling 1.00%/trade.
- Không commit password/token/secret.
- Repo `Tienkhoaa2908/vn-quant-system` chỉ là reference architecture.

## Khôi phục

1. Đọc `README.md`.
2. Đọc `RECOVERY_CHECKPOINT.md`.
3. Đọc `docs/handover/CURRENT_STATE.md` và file này.
4. Đọc `docs/research/2026-08-16_signal_intelligence_lab_v1_analysis.md`.
5. Đọc `docs/research/NEXT_EXPERIMENT.md` và `RESEARCH_OPERATING_MODEL.md`.
6. Đọc `docs/windows_mt5_exness_setup.md`, toàn bộ ADR/workflow/source/scripts/experiments/tests.
7. Đối chiếu Git HEAD/history/branches/PR/status.
8. Chạy Python compile/tests/static safety scan nếu source hiện có.
9. Không gọi `order_send`/native broker order để test.

## Latest completed evidence — V22

Signal Intelligence Lab V1 runtime bundle SHA-256:
`abd57669020f2e30c0811b7cc27a21779f32c60e0af35f56d8de32e2a54ccd03`

- internal hashes 22/22 PASS;
- Windows MetaEditor 0 errors/0 warnings;
- 18 tháng 2025-02 → 2026-07 hoàn tất;
- tester-only, native/external broker orders = 0;
- EMA base median USD40@1% +6.3236%, 13/18 tháng dương, max MTM DD 9.0171%;
- score3/score4, global exhaustion guard và telemetry meta-labeling không được promote;
- regime shift 2025→2026 là vấn đề chính.

## Gate kế tiếp — V23

`Regime Router Lab V1` re-simulate family-specific hypotheses:
- EMA late-session ablation + targeted SHORT exhaustion;
- MACD/Trend/BOS H1 trend-separation gates;
- selective one-position-at-time routers;
- 26 candidates × 4 books = 104 virtual books;
- 18 monthly resets, 3 six-month chunks, một output ZIP.

Conditional filtering trên V22 trade ledger chỉ là hypothesis discovery, không được gọi là backtest.

Nếu V23 chưa có Windows output, chỉ được claim static QA. Nếu có output ZIP, verify bundle manifest/hash trước rồi mới đọc results.

Workflow: research → implementation → static tests → Windows runtime evidence → bundle integrity → analysis → docs/handover → clean GitHub checkpoint.

Sau milestone báo `DONE / EVIDENCE / DECISIONS / ISSUES / NEXT`. Không fabricated evidence.
