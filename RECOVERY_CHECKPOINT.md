# Recovery checkpoint — V29 Adaptive Change-Point + Multi-Horizon Expert

Ngày: 2026-08-19.

REAL-MONEY LIVE TRADING = FORBIDDEN. Stop-risk research ceiling 1.00%/trade. No native broker orders.

## User-facing requirement
Không hiển thị code Python/tooling nội bộ nếu user không yêu cầu. Tooling chạy âm thầm; user-visible tập trung vào evidence, artifact, hash, thao tác, lỗi và bước tiếp theo.

## V28 final decision
Latest V3 diagnostic SHA-256 `02f020d470276b971acec89b61e5c05ff79116f9f6a343280eef96e3a3cdff9a`. Calendar extraction is CLOSED. Do not ask user for more calendar/data exports.

Later Mar-May 2026 without retuning:
- frozen cross-asset range score mean Spearman ~0.60263;
- event-aware ~0.60042; incremental calendar uplift ~-0.00221.

Core range prediction generalizes, but fixed scalar `range -> family` mapping fails. The old V28 low25 router is rejected and must NOT be run. Direction ML / trade meta-labeling remain unstable.

## V29 frozen replay catalog
12 candidates × 4 virtual books × 18 monthly accounting resets (Feb-2025 → Jul-2026):
- controls: EMA skip20, MACD gap10, BOS/FVG gap8, Trend gap5, EMA+BOS8;
- slow multi-horizon: 16h+24h agreement at server 00:00/08:00, 8h timebox, stop2ATR, TP4R, with/without peak-lock;
- adaptive: EWMA hl8 threshold 0; hl8/10/12 threshold +0.05R; fast5-vs-slow20 divergence >=0.30R change-severity probe.

Adaptive expert score updates use only normalized control-book realized R. State carries causally across all three six-month chunks. Runner retry restores the exact pre-chunk state; checkpoint reuse requires matching source/template/chunk fingerprint plus `adaptive_state_after.csv`.

Validated cross-asset range ML remains telemetry/state context but is not used as another hard fixed family gate in V29.

Static QA: pytest 11/11 PASS; analyzer py_compile PASS; delimiter/header/FileWrite-limit checks PASS; executable safety scan PASS. Windows MetaEditor/runtime pending.

One-click release SHA-256: `a0a859b42052dca6592c04274b33bccf85ae986f0f235212458fc76eec0ded69`.
Internal kit manifest 11/11 PASS; ZIP integrity PASS; no cache artifacts.
Recovery copy is stored as `recovery/v29_adaptive_expert_lab_one_click.zip.b64` and can be base64-decoded back to the release ZIP.

## Next action
User runs exactly one V29 Strategy Tester batch and uploads one result ZIP. If the replay gates pass, next endpoint is PAPER/DEMO forward validation. LIVE remains forbidden.

Full research freeze: `docs/research/2026-08-19_v29_adaptive_expert_lab_freeze.md`.
