# IMMEDIATE REAL-READINESS PLAN — V69

Updated: 2026-09-03 (+07)

This plan replaces passive waiting for a natural V69 trade as the next operational diagnostic.
It does **not** authorize REAL money.

## Why the gate changed

The frozen V69 DEMO runtime already proved:

- exact EA compiled and attached;
- live ticks and telemetry are active;
- `XAUUSDm M15` is correct;
- broker accepts a 0.01 BUY request in dry-run `OrderCheck`;
- broker health is stable READY.

After roughly one day with no natural V69 fill, continuing to wait does not efficiently distinguish
between a very selective strategy and a live signal/order-path defect.

## Immediate diagnostic sequence

Use `runtime/v69_real_readiness_probe/START_V69_REAL_READINESS_PROBE_GIT_BASH.sh`.

The one-shot will:

1. require MT5 and MetaEditor to be closed once;
2. snapshot the already-collected frozen V69 telemetry;
3. build a signal funnel from `V64_EVENTS.csv` / `V64_DEALS.csv`;
4. report the furthest V69 stage reached:
   - `POST_ZONE_REVERSAL_CONFIRM`;
   - `POST_CONFIRM_SEPARATION`;
   - `POST_CONFIRM_RETEST_READY`;
   - `POST_CONFIRM_ENTRY_READY`;
5. compile and launch an isolated **DEMO-only** execution-probe EA;
6. use unique magic `699901` and fixed lot `0.01`;
7. `OrderCheck` then send exactly one DEMO BUY and immediately close only the probe-owned position;
8. record actual open/close retcodes, comments, prices and free margin;
9. gracefully close the probe terminal via `TerminalClose()`;
10. write a JSON result;
11. automatically relaunch the frozen V69 broker-ready dashboard.

## Interpretation

- Probe PASS + `POST_CONFIRM_ENTRY_READY == 0`:
  broker/MT5 execution works; the observed no-trade condition is upstream V69 gating/state-machine selectivity, not inability to execute a market order.

- Probe PASS + `POST_CONFIRM_ENTRY_READY > 0` + no natural V69 deal:
  escalate immediately to V69 preflight/send-event tracing; this strongly supports a strategy-order-path integration defect.

- Probe FAIL:
  use the actual open/close retcode as the execution blocker; do not wait for a natural signal.

## Safety

- DEMO account is mandatory in the probe EA.
- Symbol is exactly `XAUUSDm`.
- Lot is exactly `0.01`.
- Unique probe magic is isolated from V69 performance accounting.
- No SHORT probe.
- REAL authorization remains false.
- The probe is an execution diagnostic, not a profitability test.

## REAL progression

The project may move *toward* a REAL deployment package immediately after execution diagnosis, but REAL activation requires a separate explicit gate. A successful forced DEMO open/close proves transport, not alpha or live profitability.

## Session-volatility successor research

See `docs/research/SESSION_VOLATILITY_RESEARCH.md`.

The research direction is to learn symbol/session-dependent volatility and continuation expectancy from our own MT5 history, with DST-aware London/New York labels. External tools such as MarketMilk are references for the idea, not runtime dependencies.
