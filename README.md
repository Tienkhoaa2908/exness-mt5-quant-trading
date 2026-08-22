# Exness / MetaTrader 5 Quant Trading System

**MỤC TIÊU DÀI HẠN: HƯỚNG TỚI PRODUCTION/LIVE TRADING BẰNG VỐN THẬT SAU KHI VƯỢT ĐỦ CÁC GATE XÁC NHẬN.**

Kho nghiên cứu quant cho MT5/Exness. Không Martingale, uncontrolled grid hoặc doubling after loss.

## Project objective

Dự án không dừng ở paper trading. Mục tiêu cuối là xây một hệ thống đủ correctness, safety, reproducibility, execution integrity, risk control và observability để có thể được đánh giá là `LIVE_CANDIDATE_READY` cho production trading trên tài khoản Exness real.

Điều này không có nghĩa một campaign paper/demo đang chạy được phép tự động chuyển sang real. Mỗi bước promotion phải có evidence riêng, không được bỏ qua native broker-DEMO parity, execution-cost/slippage stress, restart/reconciliation và risk-control gates.

## Active milestone — V48 DEMO paper forward

Frozen primary:
`v46_hl10_thr0p05_breadth4`

Formal V46 historical result remains `HOLD`; không relabel thành PASS/profitable winner. V48 dùng cơ chế breadth4 đã freeze để chạy finite forward operational validation trên `XAUUSDm` M15 của Exness DEMO.

V48 là:
- real-time DEMO feed;
- internal virtual USD40 paper book;
- không broker demo order;
- không real-money order;
- terminal trading permission phải OFF;
- DLL permission phải OFF;
- generated MQL không có broker-order API.

Các hạn chế trên là **scope của V48 hiện tại**, không phải tuyên bố rằng toàn bộ dự án sẽ mãi mãi không hướng tới vốn thật.

Frozen V48 source SHA256:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`

Accepted V46 adaptive-state SHA256:
`36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3`

## Promotion path toward production/live

Đường promotion mục tiêu:

`V48 virtual paper -> native Exness DEMO-order parity -> execution/slippage/delay stress -> restart/reconciliation/fault tests -> independent risk/kill-switch review -> LIVE_CANDIDATE_READY / NOT_READY`

Không promote chỉ vì vài ngày hoặc một tuần có PnL dương. Calendar time, trade count, regime coverage, execution quality và operational integrity đều phải được xem xét.

## Current Windows startup workflow

Canonical branch:
`agent/v48-demo-paper-forward`

Canonical Git Bash start:
`bash runtime/v48_demo_paper/START_V48_DEMO_PAPER_GIT_BASH.sh`

The current launcher is hardened V2. It handles the verified 2026-08-22 failure mode where MT5 loaded the V48 Expert successfully but `TERMINAL_TRADE_ALLOWED=1` caused `OnInit` refusal, followed by `OnDeinit(REASON_INITFAILED=8)` rewriting paper state despite no accepted session.

Hardened V2:
- requests terminal AutoTrading OFF at startup;
- requires MQL proof `TERMINAL_TRADE_ALLOWED=0` before READY;
- auto-recovers only the exact reason-8 blank-run-id failed-init debris pattern;
- archives evidence before reseeding accepted V46 state;
- rolls state back automatically after another failed pre-session start;
- uses launch-scoped diagnostics;
- verifies the 30-second timer/status loop even while XAU is closed.

## Finite V48 gate

Review when both are true:
- >=10 actual XAUUSD trading days;
- >=20 closed breadth4 paper trades.

Hard maximum: 30 calendar days. Không auto-extend.

A clean result may be labeled `PAPER_OPERATIONAL_PASS`. Đây chỉ là gate để xét promotion sang native broker-DEMO execution, không phải auto-authorization cho tài khoản real.

## One run -> one ZIP

Sau run quan trọng dùng ZIP mà runner in ra hoặc `scripts/package_mt5_research.cmd`. Bundle chuẩn phải có `bundle_manifest_sha256.txt`; kiểm tra bằng `scripts/analyze_mt5_research_bundle.py`.

## Recovery / authority

Đọc theo thứ tự:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/RECOVERY_PROMPT.md`
3. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`
4. `docs/adr/ADR-046-v48-failed-init-state-and-terminal-permission.md`
5. `docs/research/v48_hardened_attach_launcher.md`
6. `docs/windows_mt5_exness_setup.md`
