# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety invariant
REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research labs.

## User-facing requirement — MUST PRESERVE
Không hiển thị Python nội bộ, scratch/artifact-packaging code, tool payload hoặc implementation plumbing nếu user không yêu cầu. Tooling chạy âm thầm; user-visible chỉ cần kết luận/evidence/file/SHA/thao tác/lỗi/bước tiếp theo.

## V28 closed
Calendar extraction is CLOSED. Latest combined/recovered calendar evidence showed the frozen cross-asset future-range model generalizes strongly in Mar-May 2026 (mean Spearman ~0.60263), while incremental calendar uplift does not confirm (~-0.00221).

The old V28 fixed low25 routing rule is rejected because later conditional expectancy reverses. Do NOT run the V28 event-regime replay kit. Direct direction ML and EMA trade meta-labeling remain too unstable.

## V29 current gate — adaptive shadow experts
V29 no longer maps a scalar range percentile directly to one family. It tracks independent shadow experts causally and adapts to nonstationarity via realized-R EWMAs.

Frozen 12-candidate catalog:
- `ema_h1_skip20`;
- `macd_h1_gap10`;
- `bos_fvg_h1_gap8`;
- `trend20_h1_gap5`;
- `router_ema_bos8`;
- `slow_mom_16h24h_timebox8h`;
- `slow_mom_16h24h_peaklock_timebox8h`;
- `adaptive_ewma_hl8_thr0`;
- `adaptive_ewma_hl8_thr0p05`;
- `adaptive_ewma_hl10_thr0p05`;
- `adaptive_ewma_hl12_thr0p05`;
- `adaptive_cp_fast5_slow20_thr0p30`.

Slow momentum is an orthogonal expert: server 00:00/08:00 decisions, 16h+24h return-direction agreement, 8h timebox, stop2ATR, TP4R. It is not assumed always-on because long history shows regime dependence.

Adaptive score state is updated only from normalized control-book realized R and is carried sequentially across the 3×6-month tester chunks. Retry restores the exact pre-chunk state. Existing cross-asset range ML remains market-state telemetry; it is not another hard family gate in this replay.

## V29 release evidence
- 12 candidates × 4 books = 48 virtual books;
- 18 monthly accounting resets, Feb-2025 → Jul-2026;
- bar feature export disabled for runtime efficiency;
- pytest 11/11 PASS;
- analyzer py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- monthly-summary header/row field-count PASS;
- all MQL FileWrite calls under 63-parameter limit;
- executable safety scan PASS;
- internal kit manifest 11/11 PASS;
- ZIP integrity PASS;
- release SHA-256 `a0a859b42052dca6592c04274b33bccf85ae986f0f235212458fc76eec0ded69`;
- Windows MetaEditor/runtime still pending.

Recovery copy: `recovery/v29_adaptive_expert_lab_one_click.zip.b64` (base64 decode to the release ZIP).
Research freeze: `docs/research/2026-08-19_v29_adaptive_expert_lab_freeze.md`.

## Next gate
User runs exactly one V29 Strategy Tester batch and uploads the single result ZIP. Evaluate median/mean return, positive months, worst month, max MTM DD, AvgR, turnover, slow-momentum stability, adaptive source mix and early-vs-late stability. A robust finalist proceeds to PAPER/DEMO forward validation only. REAL-MONEY LIVE TRADING remains forbidden.
