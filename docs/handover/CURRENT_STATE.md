# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-19.

## Safety invariant
REAL-MONEY LIVE TRADING = FORBIDDEN. Không Martingale/grid/doubling. Stop-risk research ceiling 1.00%/trade. Không native broker orders trong research labs.

## User-facing requirement — MUST PRESERVE
Không hiển thị Python nội bộ, scratch/artifact-packaging code, tool payload hoặc implementation plumbing nếu user không yêu cầu. Tooling chạy âm thầm; user-visible chỉ cần kết luận/evidence/file/SHA/thao tác/lỗi/bước tiếp theo.

## V28 closed
Calendar extraction is CLOSED. Frozen cross-asset range prediction generalizes, but fixed scalar `range -> family` mapping and incremental calendar uplift fail later confirmation. Do NOT run the old V28 replay kit.

## V29 gate
Frozen 12-candidate adaptive shadow-expert catalog remains unchanged. Slow 16h+24h momentum is an orthogonal expert; adaptive variants use causal realized-R EWMAs/change severity; validated range ML remains context only.

## V29.0 compile failure / V29.1 hotfix
V29.0 one-click release is BROKEN and must not be reused. User Windows MetaEditor failed before Strategy Tester with 100 errors / 50 warnings.

Root cause: five shared helper definitions were accidentally removed during refactor while calls remained: `MonthKey`, `MonthTagFromKey`, `NewBar`, `ReadOne`, `SecondsOfDay`. A second runner bug prevented diagnostic ZIP creation because `$MyInvocation.MyCommand.Path` was null inside the diagnostic function.

V29.1 restores the five helper bodies from the previously Windows-compiled V28 implementation and replaces diagnostic/main script path discovery with `$PSScriptRoot`.

Release gate was strengthened so future packaging must test required runtime helper definitions, not only delimiter/FileWrite/safety structure.

V29.1 static evidence:
- pytest 13/13 PASS;
- Python analyzer/tests compile PASS;
- MQL delimiter balance PASS;
- all five helper definitions present exactly once;
- custom-helper consistency check against V28 compiled base PASS;
- no `OrderSend`/`order_send`/`CTrade`/`AllowLiveTrading=1`;
- internal manifest 11/11 PASS;
- ZIP integrity PASS.

V29.1 release SHA-256: `b8176551870b218f47322bae72c7a78be2d0efde8eec7237dab91ab4f8aeb824`.
Patch: `recovery/v29_1_compile_hotfix.patch`, SHA-256 `c5f999e546b3aa67dbe704e9dbc90bf62510e2134aea4e8c3c44e5d759c0b65c`.

Windows MetaEditor/runtime for V29.1 is still pending. Static QA must never be described as compile evidence.

## Next gate
User runs only V29.1 in a fresh folder. Accept the batch only if MetaEditor reports 0 errors / 0 warnings. If compile passes, let the single stateful 18-month Strategy Tester batch complete. If robust gates pass, next endpoint is PAPER/DEMO forward validation. LIVE remains forbidden.
