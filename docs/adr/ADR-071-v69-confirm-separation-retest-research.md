# ADR-071 — V69 Confirm-Separation-Retest Research

Status: research / Strategy Tester only.

## Context

Accepted V68 holdout evidence on exact head `e1684df89078c9a8c0320df2370bbee19d00ff42` produced 28 LONG trades with 10 wins / 18 losses, net `+$2.87`, PF about `1.146`, max realized DD `$6.04`, and 11 of 18 LONG losers exiting within 60 seconds. SHORT produced two trades, both losses, net `-$2.22`.

V67's post-zone reclaim concept therefore did not generalize as cleanly as the small June-August calibration sample suggested.

Sequence analysis of the V68 actual entries found a missing execution state: after `POST_ZONE_REVERSAL_CONFIRM`, V67/V68 can enter as soon as cash risk is feasible. Four V68 LONG trades entered at the exact confirmation timestamp; all four lost. More generally, the logic does not require the reclaim to establish favorable distance from the fixed structural stop and then survive a later retest.

This ADR does not interpret those post-hoc counts as a proof of an optimal time delay. They motivate a causal execution rule: confirmation must create real separation before a later retest is tradable.

## Decision

V69 preserves the V67/V68 signal, regime, zone, structural stop, risk and target contracts, but inserts a post-confirmation state:

`zone penetration -> closed-M1 reclaim confirmation -> favorable separation -> later cash-zone retest -> revalidation -> order`.

Rules:

- fixed lot `0.01`;
- planned structural risk remains `$0.85-$1.10`;
- emergency loss guard remains about `$1.20` best effort;
- target remains `+$3.50`;
- risk/spread remains `>=4`;
- original BOS-owned M1 structural stop remains fixed and is never widened or clamped;
- reclaim confirmation itself can never place an order;
- price must subsequently establish prospective risk distance of at least `$1.30` from the fixed stop;
- the separation tick itself cannot place an order;
- entry must occur on a later retest into the existing `$0.85-$1.10` feasible zone;
- confirmation must be at least 30 seconds old before entry;
- existing five-minute confirmation expiry and adverse-extreme reset remain active;
- LONG and SHORT remain independent evaluation lanes.

The `$1.30` separation and 30-second minimum age are preregistered V69 research thresholds. They are not claimed optimal.

## Validation interpretation

V69 replays exactly the nine V68 calendar months, LONG and SHORT, Model=4: 18 passes total. Because V69 was designed after reading V68 results, this replay is explicitly **not an independent holdout**. It is a mechanistic development comparison against V68.

No month is selected or removed by PnL. If V69 improves the V68 replay, a later untouched/forward validation is still required before promotion.

## Observability

V69 adds:

- `POST_CONFIRM_SEPARATION`;
- `POST_CONFIRM_RETEST_READY`;
- `POST_CONFIRM_ENTRY_READY`.

Analyzer output retains lane PnL/PF/DD/month consistency/fast-loss counts and reports the new stage conversion.

## Safety

V69 is tester-only. REAL-money authorization is false. Static CI is not runtime evidence; Windows MetaEditor compile and 18 Model=4 passes are required.
