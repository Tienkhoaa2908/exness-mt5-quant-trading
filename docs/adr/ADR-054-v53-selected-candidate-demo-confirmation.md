# ADR-054 — V53 selected-candidate broker-DEMO confirmation

Date: 2026-08-26
Updated: 2026-08-27

## Context

V52R accepted `v52_b4_or_b3_trend_bos` on a clean real-tick historical run. It increased evaluation trade count by 16.12% versus the clean breadth4 baseline while keeping max MTM DD slightly lower (16.10% vs 16.60%) and satisfying all preregistered ADR-052 guardrails.

V50 already qualified generic native Exness DEMO open/close/reconciliation plumbing with three controlled probe round trips. Repeating execution probes would add cost without testing the selected strategy integration.

## Decision

Run one short V53 broker-DEMO confirmation driven only by the selected candidate's natural virtual intent.

V53 forward source ports the exact selected source-aware rule into the accepted V48 forward observer lineage:
- breadth >=4 remains admitted;
- at exactly breadth3, the selected expert must be TREND20_H1 or BOS_FVG_H1;
- risk/book semantics remain inherited;
- broker adapter is inherited from V49/V50 DEMO-only reconciliation semantics.

Confirmation gate:
- at least 2 distinct market days;
- at least 1 broker-confirmed natural round trip;
- zero duplicate-owned-position events;
- zero direction mismatches;
- reject ratio within the inherited bound;
- final flat state;
- hard calendar stop 7 days if the natural sample does not arrive.

Possible EA final outcomes remain:
- `DEMO_CONFIRMATION_PASS`;
- `HOLD`;
- `INSUFFICIENT_EXECUTION_SAMPLE`.

## Operator timebox waiver — 2026-08-27

The natural-signal gate is not allowed to block the project indefinitely when the selected candidate simply has not generated an entry.

If by the end of 2026-08-28 (user-local date) V53 still has **zero natural round trips**, the coordinator may close this milestone without extending the wait, provided the observed runtime remains healthy and flat:
- heartbeat/status continues updating;
- `halted=0`;
- no duplicate-owned-position event;
- no direction mismatch;
- no unresolved open/close pending state;
- no owned broker position;
- no broker reject attributable to a natural strategy request.

This closure must be recorded as:
`V53_NO_SIGNAL_TIMEBOX_WAIVER`

It must **not** be relabeled `DEMO_CONFIRMATION_PASS`, because no natural candidate-to-broker open/close mapping was observed.

Under this waiver:
- V52R remains the authoritative alpha-selection evidence;
- V50 remains the authoritative generic broker-DEMO execution-plumbing evidence;
- the selected research candidate remains `v52_b4_or_b3_trend_bos`;
- the missing evidence is explicitly limited to a natural V53 round trip;
- further DEMO research/monitoring may proceed without rerunning V50 probes or retuning alpha.

If a natural V53 round trip arrives before the timebox closes and all reconciliation checks pass, the normal `DEMO_CONFIRMATION_PASS` path remains valid.

## Safety

V53 is DEMO-only. The generated MQL must refuse non-DEMO accounts, require terminal/MQL trade permission for the DEMO confirmation, require DLL permission off, own positions only through magic `530053`, and keep `real_money_authorized=0` in evidence.

No execution-probe trades are permitted. No threshold retuning, Martingale, grid, doubling-after-loss or risk increase is introduced.

## Consequence

A clean V53 pass confirms the selected strategy's natural virtual intent can map through the already-qualified broker-DEMO adapter.

A `V53_NO_SIGNAL_TIMEBOX_WAIVER` closes the waiting gate without making that confirmation claim. It preserves the distinction between evidence already established by V50/V52R and evidence that was not observed in V53.