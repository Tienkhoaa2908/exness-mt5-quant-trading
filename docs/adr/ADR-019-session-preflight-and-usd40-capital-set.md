# ADR-019 — Broker-session preflight and USD 20/30/40 capital set

Status: Accepted for research validation, 2026-08-15.

The ~19-month native Tier-A validation produced 15 order failures, all retcode 10018 MARKET_CLOSED near the XAUUSDm daily break. MQL5 exposes broker-defined trading sessions through `SymbolInfoSessionTrade`; dynamic session metadata is preferred to a hard-coded clock-hour filter.

Decision:
1. Preflight broker trading-session availability before native order requests.
2. Session-closed signals are logged as research evidence and are not sent to CTrade.
3. Promotion requires all previously observed MARKET_CLOSED timestamps in targeted windows to become session skips and native `order_fail=0`.
4. Canonical tiny-capital comparison balances are USD 20, USD 30 and USD 40.
5. Default sizing remains strict 0.50% target risk, 1.00% hard cap, floor-only quantization; no upward rounding.
6. USD 40 is mechanically preferred among the three only if cent-specific and OOS gates pass. This ADR does not authorize live trading.

The targeted regression is intentionally shorter than the full 19-month run to reduce iteration time. After PASS, promote the session filter and continue extended-history/OOS plus cent-specific cost/spec validation.