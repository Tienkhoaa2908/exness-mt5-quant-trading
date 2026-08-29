# ADR-058 — V56 weekly real-tick live replay diagnostic

Date: 2026-08-29
Status: Accepted for diagnostic execution

## Context

The selected production candidate `v52_b4_or_b3_trend_bos` had not produced an observed natural broker mapping during the V53 timebox, and the current DEMO/trial runtime reached V55 READY while the operator reported no automatic order from the beginning of the week of 2026-08-24.

The market is closed for the weekend. The correct diagnostic is therefore a historical replay of the same week through MetaTrader 5 Strategy Tester using broker real ticks, not a forced live order and not another alpha tournament.

## Decision

Create V56 as a tester-only derivative of the exact V55 generated source.

V56 changes no alpha threshold, selected candidate, book, risk sizing, stop/TP mapping, ownership logic or broker reconciliation logic. It only:

- reverses the inherited V48 `MQL_TESTER` refusal into a tester-only guard, so the V56 EA refuses attachment to a live chart;
- disables push notifications in tester;
- isolates all mutable FILE_COMMON output under `mt5_quant\\v56_weekly_live_replay`;
- instruments selected-book virtual OPEN/CLOSE transitions for diagnosis;
- runs MT5 Strategy Tester with `Model=4` (`Every tick based on real ticks`).

The tested symbol/timeframe remain `XAUUSDm M15`. Each tester phase starts with USD 40 and leverage 1:200, matching the project test book.

## Anti-look-ahead state protocol

V56 must not seed from the current/end-of-week adaptive state and replay backward.

The accepted V52R run ended at 2026-08-01 and produced `state_after_v52r.csv`. V56 recovers that state only from a local historical output whose companion `v52r_real_tick_repro.zip` has the accepted SHA256:

`4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c`

If the output was preserved with `git stash --include-untracked`, V56 may read it from the stash's untracked parent. If the accepted seed cannot be recovered, V56 fails closed. It must not substitute the current V55/V54/V53/V50 state.

## Two-phase replay protocol

V56 deliberately separates adaptive-state evolution from the diagnostic trading week.

### Phase A — adaptive-state warm-forward

- source state: accepted V52R `state_after_v52r.csv` as of 2026-08-01;
- interval: 2026-08-02 through 2026-08-23;
- MT5 model: 4, real ticks;
- purpose: advance only the adaptive EWMA/breadth state chronologically to the start of Monday 2026-08-24;
- output: `state_at_week_start.csv` plus warmup provenance.

The warmup phase is not used for the diagnostic week's PnL. Its account/book history must not carry into the measured week.

### Phase B — diagnostic week

- source adaptive state: the Phase A `state_at_week_start.csv`;
- account/book: a fresh tester start with USD 40 and leverage 1:200;
- interval: 2026-08-24 through 2026-08-29, with the target trading week being 24–28 August;
- MT5 model: 4, real ticks;
- purpose: measure selected virtual entries and their V55 execution mapping with no pre-week PnL/position carry-over.

This split prevents two separate distortions: future-state look-ahead and carrying 02–23 August book PnL/positions into the week being diagnosed.

## Tester controls

- symbol: `XAUUSDm`;
- timeframe: `M15`;
- optimization: disabled;
- cloud agents: disabled;
- visual mode: disabled;
- tester DLL permission: disabled;
- V56 is tester-only and cannot be used as a live-chart EA.

MetaTrader 5 real-tick testing is a historical simulation. It does not prove that historical live fills, latency or broker-side execution would have been identical.

## Diagnostic verdicts

V56 compares selected virtual book transitions with V55 simulated broker OPEN requests:

- `V56_WEEK_NO_SELECTED_CANDIDATE_ENTRY`: no selected virtual entry occurred in the diagnostic week; zero broker orders is consistent with alpha opportunity frequency for this replay.
- `V56_WEEK_EXECUTION_MAPPING_BLOCKED`: selected virtual entry occurred but no broker OPEN request was emitted; investigate V55 guard/mapping logic.
- `V56_WEEK_PARTIAL_MAPPING`: only some virtual entries mapped to broker OPEN requests.
- `V56_WEEK_BROKER_REJECTION_OBSERVED`: mapping occurred but at least one simulated broker OPEN was rejected.
- `V56_WEEK_MAPPING_OBSERVED`: selected virtual entries mapped to simulated broker OPEN requests.
- `V56_WEEK_RUNTIME_HALTED`: replay ended halted; halt reason takes precedence over alpha conclusions.

V56 does not change the historical V53 classification. `V53_NATURAL_MAPPING=NOT_OBSERVED` remains true until a natural broker-DEMO mapping is actually observed outside the tester.

## Evidence

The runner packages:

- exact generated V56 MQL source and source SHA;
- MetaEditor compile log;
- separate warmup and replay tester INIs;
- accepted V52R seed provenance and accepted ZIP SHA;
- `state_at_week_start.csv` and its SHA;
- warmup checkpoint metadata;
- replay manifest/monthly/trades files;
- isolated V56 events, transactions and status;
- post-replay adaptive state;
- analyzer JSON and text summary;
- SHA256 manifest and CRC-verified ZIP.

No V56 result authorizes REAL deployment by itself.
