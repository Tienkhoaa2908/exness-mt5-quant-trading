# Exness / MetaTrader 5 Quant Trading System

**MỤC TIÊU DÀI HẠN: HƯỚNG TỚI PRODUCTION/LIVE TRADING BẰNG VỐN THẬT SAU KHI HỆ THỐNG ĐƯỢC ĐÁNH GIÁ ĐỦ READINESS.**

Kho nghiên cứu/engineering quant cho MT5/Exness. Không Martingale, uncontrolled grid hoặc doubling after loss.

## Frozen strategy

Primary: `v46_hl10_thr0p05_breadth4`.

Historical/alpha evidence từ V45/V46 và deterministic V48 parent được kế thừa; V49 không mở lại cùng sample để tối ưu breadth/HL/threshold.

Frozen V48 parent SHA256:
`ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.

## Current runtime

Một V48 DEMO-paper observer đã startup thành công trên Windows và có thể vẫn đang chạy. Không chuyển campaign khi V48 primary virtual position đang OPEN.

## Active engineering milestone — V49 One-Shot DEMO Production Rehearsal

Branch:
`agent/v49-one-shot-demo-rehearsal`

V49 gom các bước post-paper thành **một campaign duy nhất** thay vì nhiều gate/run tách rời:

`frozen virtual intent -> native Exness DEMO entry/exit -> OnTradeTransaction reconciliation -> push notification -> execution logging -> finite final verdict -> one ZIP`

V49 tập trung vào hệ thống tự động vận hành trôi chảy, không phải thêm một vòng research alpha.

### V49 scope

- Exness DEMO native broker orders;
- XAUUSDm M15;
- dedicated magic `490049`;
- tự mở và đóng broker DEMO theo primary virtual intent;
- SL/TP request từ frozen strategy;
- không quản lý manual/foreign positions;
- log server retcode/order/deal và transaction events;
- push START / OPEN / CLOSE / HALT / FINAL khi MetaQuotes notifications đã được cấu hình;
- detached supervisor đóng gói một ZIP cuối.

REAL/non-DEMO account bị hard-refuse trong V49 trước broker request. V49 không phải real-money execution build.

### Simplified acceptance

Minimum useful sample:
- >=3 distinct market-active XAUUSD dates;
- >=3 completed native broker-DEMO round trips.

Hard stop: 14 calendar days.

Một clean rehearsal có thể kết luận `LIVE_CANDIDATE_READY`; nếu không đủ sample ở hard stop thì `INSUFFICIENT_EXECUTION_SAMPLE`; execution/reconciliation critical failure thì `HOLD`.

Không chạy lại V45/V46 historical campaigns trong V49.

## One user action

Canonical V49 starter:

`bash runtime/v49_demo_rehearsal/START_V49_ONE_SHOT_GIT_BASH.sh`

Sau START PASS, Git Bash có thể đóng. Giữ PC + Internet + MT5 chạy. Detached supervisor sẽ tạo một ZIP cuối tại:

`runtime/v49_demo_rehearsal/OUTPUT_V49/`

Bundle có `bundle_manifest_sha256.txt`.

## Authority

Đọc theo thứ tự:
1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/RECOVERY_PROMPT.md`
3. `docs/adr/ADR-048-v49-one-shot-production-rehearsal.md`
4. `docs/research/v49_one_shot_demo_rehearsal_plan.md`
5. `docs/adr/ADR-047-production-live-target-and-promotion-gates.md`
6. `docs/windows_mt5_exness_setup.md`
