# ADR-046 — V48 failed-init state recovery and terminal trading permission

Date: 2026-08-22
Status: Accepted; project-wide live policy superseded by ADR-049

## Context

V48 is a DEMO-feed observer using the frozen `v46_hl10_thr0p05_breadth4` internal virtual USD40 paper book. **For V48 specifically**, broker-order execution and real-account execution are disabled by design.

This is a V48 runtime contract, not a permanent project-wide prohibition on researching or preparing production/live trading. Project-wide live policy is now defined by ADR-049 with `LIVE_RESEARCH_ALLOWED=1` and `LIVE_DEPLOYMENT_TARGET=1`.

Windows evidence on 2026-08-22 showed that MT5 consumed the V48 startup config and loaded `V48DemoPaperObserver` successfully, but MQL `OnInit` observed `TERMINAL_TRADE_ALLOWED=1` and refused initialization. MT5 then invoked `OnDeinit(REASON_INITFAILED=8)`.

The inherited V48 `OnDeinit` path saves adaptive state and writes status/latest metadata even after failed initialization. This rewrote the paper state while leaving `run_id` blank, creating an orphan non-seed state despite no accepted V48 session.

The previous launcher treated any non-seed orphan state as ambiguous and failed closed, which was safe but forced manual recovery.

## Decision

1. Keep the frozen V48 MQL strategy source unchanged for this operational fix.
2. Keep the V48 MQL `OnInit` gates authoritative: DEMO account required, `TERMINAL_TRADE_ALLOWED=0`, `TERMINAL_DLLS_ALLOWED=0`.
3. V48 startup V2 requests both `AllowLiveTrading=0` and `Enabled=0`, plus `AllowDllImport=0`, because empirical evidence showed the previous `Enabled=1` startup left terminal trading permission enabled.
4. Automatically recover non-seed paper state only when there is exact failed-init evidence: INIT `stage=STOPPED`, `reason=8`, `broker_orders=0`, `live_authorized=0`, XAUUSDm M15, and no non-empty run id in LATEST or STATUS.
5. Preserve all failed-init artifacts by moving them into a timestamped forensic archive before reseeding the exact accepted V46 state.
6. Any other non-seed orphan state remains fail-closed.
7. If a subsequent startup fails before a valid run id exists, archive its artifacts and automatically restore the exact accepted V46 seed so the next attempt is not poisoned by `OnDeinit(REASON_INITFAILED=8)`.
8. A non-empty run id always wins over recovery logic and blocks a second V48 session.

## Consequences

- The user no longer needs to manually delete or move failed-init state files.
- Failed startup attempts remain auditable.
- State continuity remains conservative: only one narrowly defined failure pattern is auto-recovered.
- Strategy/alpha/risk behavior is unchanged; V48 generated MQL SHA remains `ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa`.
- V48 startup remains fail-closed if its analytical-only terminal permission contract is not satisfied.

## Historical V48 safety contract

No `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, DLL import, or external broker-order path is introduced in V48.

V48 itself remains DEMO/paper-only. This restriction does not apply as a permanent project policy to later milestones. See ADR-049 for current live-trading research/readiness semantics.
