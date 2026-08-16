# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository mục tiêu: `Tienkhoaa2908/exness-mt5-quant-trading`.

## Luật bắt buộc

- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Không gửi lệnh tiền thật.
- Không tháo tester/live guards.
- Không Martingale, uncontrolled grid, doubling after loss.
- Không commit password/token/secret.
- Repo `Tienkhoaa2908/vn-quant-system` chỉ là reference architecture.

## Khôi phục

1. Đọc `README.md`.
2. Đọc `docs/handover/CURRENT_STATE.md`.
3. Đọc file này.
4. Đọc `docs/research/RESEARCH_OPERATING_MODEL.md`.
5. Đọc `docs/windows_mt5_exness_setup.md`.
6. Đọc toàn bộ `docs/adr/`, `docs/research/`, `mql5/`, `scripts/`, `experiments/` nếu đã materialize.
7. Nếu clean clone chưa có V21 source/scripts, dùng root `RUN_MULTI_FACTOR_EDGE_LAB_V1.cmd` hoặc giải nén `recovery/v21_impl_payload.zip`.
8. Đối chiếu Git HEAD/history/branches/PR/status.
9. Chạy Python compile/tests/static safety scan nếu source hiện có.
10. Không gọi `order_send`/native broker order để test.

## Trạng thái research cần giữ

Churn Control Lab V1 đã hoàn thành và generic cooldown bị reject.

Next gate là `Multi-Factor Edge Lab V1`:
- 8 signal families;
- 32 candidates;
- 4 virtual books/candidate;
- 18 monthly resets;
- one-click runner;
- one run -> one ZIP.

Target 15–20%/tháng là research aspiration, không phải guarantee. Không tăng risk trên 1% để ép target.

Peak-lock exit được frozen cho gate:
- 2 ATR initial stop;
- TP4R;
- sau +1R protect 50% peak R.

Targeted anti-fake-entry rule:
- chỉ sau hai rapid profitable exits cùng hướng;
- third same-direction re-entry trong <=4h cần 0.50 ATR adverse reset hoặc hết 4h.

ICT/SMC chỉ được dùng dưới dạng mechanical OHLC hypotheses như liquidity sweep và BOS+FVG; không claim edge trước evidence.

## Workflow

research → implementation → static tests → Windows runtime evidence → bundle integrity → analysis → docs/handover → clean GitHub checkpoint.

Sau milestone báo:
`DONE / EVIDENCE / DECISIONS / ISSUES / NEXT`.

Không fabricated evidence.
