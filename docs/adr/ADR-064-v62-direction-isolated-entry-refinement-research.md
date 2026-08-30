# ADR-064 — V62 Direction-Isolated Entry-Refinement Research

Status: research only. No production or REAL-money authorization.

## Decision

V62 tests whether the V61 small-loss architecture can produce materially more executable LONG and SHORT trades by refining **entry timing**, not by widening the stop budget.

The Strategy Tester protocol is fixed to XAUUSDm M15, lot `0.01`, Model=4 real ticks, deposit `$40`, leverage `1:200`.

Four complete recent weeks are preregistered and are not selected by PnL:

- week1: `2026.08.03` through `2026.08.08`
- week2: `2026.08.10` through `2026.08.15`
- week3: `2026.08.17` through `2026.08.22`
- week4: `2026.08.24` through `2026.08.29`

Each week runs two independent passes: LONG-only and SHORT-only. There are exactly eight real-tick passes.

## Frozen risk / exit contract

- fixed lot `0.01`
- structural cash-risk band `$0.75-$1.25`
- primary target `+$3`
- profit ratchet arms at `+$2` and attempts to protect `+$1`
- `OrderCheck()` remains mandatory before simulated broker submission
- no Martingale, grid, averaging down or lot escalation

V62 must not widen the structural-loss budget merely to create trades.

## Entry refinement

V61 showed many SHORT directional signals but no executable SHORT setup inside the small-loss band. The observed market-entry SHORT risk was several times the target budget. V62 therefore changes the timing of the entry:

1. H4/H1/M15 directional engine identifies a setup and **arms** it.
2. The EA does not enter immediately.
3. Closed M5 bars must retrace/retest toward the M5 EMA region while remaining trend-aligned.
4. A closed M1 bar must show a turn back in the setup direction.
5. Only at the new market price is structural stop/target feasibility recalculated.
6. If the true structural stop still implies cash risk outside `$0.75-$1.25`, the setup waits or expires; the stop is not fabricated closer.
7. Pending setups expire after 240 minutes or are cancelled if their structural invalidation is breached before entry.

All M5/M1 inputs are closed-bar data (`CopyRates(..., start_pos=1, ...)`) to preserve causality.

## Direction isolation

The LONG expert is generated with `InpV62AllowedDirection=+1`; the SHORT expert with `-1`. Opposite-direction signals may be logged for diagnostics but cannot arm or submit a broker order in that pass.

This fixes the V61 methodology defect where LONG trades could occur inside a SHORT-labelled validation week.

## Analysis

V62 reports, for every week and direction independently:

- directional signals and pending arms
- pending expiry/invalidation reasons
- refinement wait/rejection reasons
- refined entries sent
- broker round trips, wins/losses, win rate
- gross profit/loss, net USD, PF
- average winner, average loser, maximum single loss
- profit-lock and OrderCheck results
- shadow `$2/$3/$4` outcomes

The monthly report provides LONG, SHORT and an `isolated-pass sum`. The sum is not a concurrent portfolio equity curve because LONG and SHORT are separate tester passes.

## Promotion rule

V62 is exploratory. A positive month, especially with a small number of trades, does not authorize production promotion. SHORT must show actual simulated execution evidence rather than merely directional signals. Subsequent evidence must cover more periods before any production change.
