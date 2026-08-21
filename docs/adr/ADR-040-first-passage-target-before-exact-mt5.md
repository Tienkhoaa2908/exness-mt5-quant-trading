# ADR-040 — First-passage target before any new exact-MT5 exit controller

Status: Accepted for V40 Stage A research  
Date: 2026-08-21

## Context

V38 showed universal fast exits reduce economic performance. V39 then tested a selective controller after +1R, but the primary fusion lane remained `STAGE_A_HOLD`: only 17 triggers, 3/6 positive avoided-giveback months and 32% mean monthly false-big-winner rate.

The V39 labels ask whether a trade eventually gives back and whether it eventually reaches a larger maximum. That does not directly answer an intervention question because a trade can extend strongly first and give back later.

## Decision

V40 changes the target rather than tuning V39 thresholds.

From each +1R state, model the order of two competing events:

- protective giveback boundary first;
- tail-extension boundary first.

The model uses causal M1 state features and a fixed chronological train/calibration/test protocol.

The preferred intervention is not immediate exit. It is a selective protective floor so large winners can continue while giveback-prone states can lock profit.

V32 DeepMLP keep60, V36 Transformer and source/direction diagnostics remain separate evidence lanes; they are not jointly retuned on the V39 development sample.

## Consequences

- A V40 Stage-A PASS only permits design of a frozen exact-MT5 Stage B.
- Shadow equity is diagnostic and must not be reported as verified PnL.
- No score/barrier/source/risk sweep is allowed to convert HOLD into PASS.
- Initial risk and entry count remain unchanged.
- LIVE trading remains forbidden.
