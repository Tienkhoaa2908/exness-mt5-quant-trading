# ADR-054 — V53 selected-candidate broker-DEMO confirmation

Date: 2026-08-26

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

Possible final outcomes:
- `DEMO_CONFIRMATION_PASS`;
- `HOLD`;
- `INSUFFICIENT_EXECUTION_SAMPLE`.

## Safety

V53 is DEMO-only. The generated MQL must refuse non-DEMO accounts, require terminal/MQL trade permission for the DEMO confirmation, require DLL permission off, own positions only through magic `530053`, and keep `real_money_authorized=0` in evidence.

No execution-probe trades are permitted. No threshold retuning, Martingale, grid, doubling-after-loss or risk increase is introduced.

## Consequence

A clean V53 pass confirms the selected strategy's natural virtual intent can map through the already-qualified broker-DEMO adapter. It does not itself authorize real-money execution.