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
6. Đọc toàn bộ `docs/adr/`, `docs/research/`, `mql5/`, `scripts/`, `experiments/`.
7. Đối chiếu Git HEAD/history/branches/PR/status.
8. Chạy Python compile/tests/static safety scan nếu source hiện có.
9. Không gọi `order_send`/native broker order để test.

## Latest completed evidence

`Multi-Factor Edge Lab V1`:
- bundle SHA-256 `c539c2be6ce3b134c78b5e4a1f20cdecaccc268a7fb44c46a81a12ae938489c0`;
- integrity 22/22 PASS;
- Windows MetaEditor 0 errors / 0 warnings;
- 18 monthly resets;
- tester-only, native/external broker orders 0.

EMA H1 base remains the strongest robust control at median ~+6.32%/month on USD40@1%. No V21 candidate robustly meets 15–20%/month.

Hard quality conjunction over-filtered. The V21 streak guard produced zero rejects and therefore must not be described as a validated failure/success.

## Next gate

`Signal Intelligence Lab V1`.

Một lần chạy:
- 5 retained signal families;
- 6 bounded variants/family;
- 30 candidates;
- 4 books/candidate;
- 120 virtual books;
- 18 monthly resets;
- 3 six-month chunks;
- one output ZIP.

Variants:
`base`, `score3`, `score4`, `score3_exhaust`, `score3_adaptive`, `score3_exhaust_adaptive`.

Exhaustion V2:
- consecutive profitable exits same direction build streak independent of rapid-entry status;
- third same-direction entry within 8h requires 1.00 ATR adverse reset.

Adaptive exit được giới hạn:
- default peak-lock after +1R / TP4R;
- strong non-RSI2 state (score>=4, ADX>=25) may use 0.75R peak-distance trail / TP4R.

Risk remains <=1.00%/trade. Target 15–20%/month is a research aspiration, never a guarantee or reason to increase risk.

## Workflow

research → implementation → static tests → Windows runtime evidence → bundle integrity → analysis → docs/handover → clean GitHub checkpoint.

Sau milestone báo:
`DONE / EVIDENCE / DECISIONS / ISSUES / NEXT`.

Không fabricated evidence.

## V22 one-click kit đã phát hành

SHA-256: `aec1cd45168a671c63183dcbf832dbf768f89de896a5264638d2cf1c2cfcaae0`. Internal kit manifest: 20/20 PASS. Runtime/MetaEditor V22 chỉ được xác nhận sau khi user chạy kit và upload output ZIP.
