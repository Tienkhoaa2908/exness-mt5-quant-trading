# Windows MT5 / Exness — V54 Production Readiness

Updated: 2026-08-28

## Fixed runtime

- branch: `agent/v54-production-readiness-hardening`
- candidate: `v52_b4_or_b3_trend_bos`
- symbol: `XAUUSDm`
- timeframe: M15
- magic: `540054`
- maximum owned strategy positions: 1
- DLL imports: disabled
- production activation: `DISABLED_DEMO_SAFE`
- real-money authorization in this build: `0`

The project target remains production/live deployment under ADR-049. V54 itself keeps
a DEMO account guard so technical readiness evidence cannot be confused with an
already-executed real-money cutover.

## Canonical start

From Git Bash at the repository:

`bash runtime/v54_production_readiness/START_V54_PRODUCTION_READINESS_GIT_BASH.sh`

The starter resets the checkout to the authoritative remote V54 branch and requires a
clean tree. The Python runner then performs the remaining fail-closed checks.

## Prestart checks

The runner must complete:

1. Python compile of V54 scripts/tests;
2. V54 static safety contract;
3. repository secret scan;
4. Exness MT5 location discovery;
5. deterministic canonical V48 parent reconstruction;
6. V53 selected-candidate build inheritance;
7. V54 production-hardening transformation;
8. MetaEditor compile with `0 errors, 0 warnings`;
9. EX5 existence;
10. MT5 controlled startup with `AllowDllImport=0`;
11. DEMO account, `XAUUSDm`, M15 and owned-magic checks;
12. V54 READY status verification;
13. immutable startup evidence ZIP generation.

Any failure stops the startup path.

## Risk defaults

- maximum stop-risk cap: 0.50% equity;
- hard runtime configuration ceiling: 1.00%;
- daily/session equity loss stop: 2.00%;
- peak-equity drawdown stop: 6.00%;
- maximum spread: 150 points;
- maximum broker tick age: 15 seconds;
- maximum strategy-state age: 30 seconds;
- maximum consecutive broker rejects: 3.

V54 never scales broker volume above inherited virtual volume. If broker minimum lot
would exceed the risk budget, entry is refused.

## Restart and broker ownership

The runtime uses only symbol + magic ownership. It fails closed on:

- more than one owned position;
- foreign same-symbol position ambiguity;
- an owned position without SL and TP;
- open/close confirmation timeout;
- virtual/broker direction mismatch;
- repeated broker rejects.

A seeded strategy state cannot open a new order until V54 processes a fresh strategy
tick after startup. Daily start equity and peak equity persist in terminal Global
Variables by server day so restart does not reset the day's loss protection.

## Disconnect/stale behavior

Disconnect, stale tick, stale strategy state or excessive spread blocks new entries.
Existing server-side SL/TP remains the first protection while disconnected. After
reconnect, broker reconciliation runs before another entry is eligible.

## Phone notifications

V54 inherits `SendNotification()` lifecycle notifications from the V49 adapter.
Configure MetaQuotes ID in the local MT5 terminal only. Do not store it in Git.

Notification failure is logged and must never trigger a duplicate trade.

## Evidence output

Startup evidence is written under:

`runtime/v54_production_readiness/OUTPUT_V54/`

The evidence packager copies live files into a staging snapshot first, then hashes and
zips only the snapshot. It verifies ZIP CRC and every manifest hash before declaring
the bundle complete.

## Rollback

Do not terminate MT5 merely to stop the strategy while an owned position exists.

Before rollback require:

`owned_positions=0`

`open_pending=0`

`close_pending=0`

Then create a final V54 evidence snapshot and only afterwards stop MT5/check out an
older branch.

Full procedure:

`docs/runbooks/V54_PRODUCTION_READINESS_RUNBOOK.md`
