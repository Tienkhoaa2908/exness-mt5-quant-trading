# V46 Expert-Breadth Walkforward Results

Date: 2026-08-22

## Policy note

V46 is historical evidence. Current project-wide live policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V46 tester-only/native-order-disabled/live-authorization-false markers describe V46 itself. They are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Evidence identity

Accepted uploaded ZIP SHA256:
`ef8b97a856a0ba300063c0138e4a3f49e049b916886714a1a9e95378e7ac6d5a`.

Bundle integrity:
- ZIP CRC PASS;
- internal SHA manifest 24/24 PASS;
- run HEAD `655bf2f77503d91d0749d2f5c99cc0ad8678c388`;
- branch `agent/v46-expert-breadth-walkforward`;
- canonical V46 source SHA `6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3`;
- compiler `Result: 0 errors, 0 warnings`;
- exact run id `v46_expert_breadth_walkforward_v1__XAUUSDm__PERIOD_M15__2021-01-03_00-00-00__672937`.

Historical V46 markers: tester-only, native/external broker orders disabled, risk unchanged, live authorization false.

Protocol: one continuous exact MT5 run, XAUUSDm M15, 2021-01-03 -> 2026-08-01, $40 USD, leverage 1:200, cold-start state, first six months warm-up.

## Formal result

`STATUS=HOLD`

The preregistered primary `v46_hl10_thr0p05_breadth4` passed 13 of 14 readiness checks. The only failed check was the full-year sign-count gate. This formal HOLD must not be rewritten after seeing the result.

## Primary breadth4 economics

Full cold-start:
- $40 -> $106.947120;
- total return +167.3678%;
- max MTM DD 16.5983%.

Evaluation:
- compounded return +167.367657%;
- annualized +21.344869%;
- 825 trades;
- AvgR +0.144313R;
- SumR +119.05819R;
- PF 1.281739;
- 30 active months / 61 evaluation months;
- positive active-month ratio 66.67%;
- -0.05R/trade friction stress +77.80819R.

Risk stability:
- worst full year -0.810156%;
- worst rolling-12m -1.946983%;
- 2022 -0.744202%;
- 2023 -0.810156%;
- 2024 +5.179345%;
- 2025 +42.785951%;
- 2026 Jan-Jul +80.829731%.

Compared with V45 HL10p05 on the common window, breadth4 materially reduced drawdown and trade count while improving PF/AvgR and common-window compounded return.

## Crisis/regime interpretation

The result supports the intended mechanism: in weak regimes the system mostly stops opening new risk instead of forcing trades, while retaining substantial participation when expert breadth is healthy.

No event-specific war/news exception is encoded.

## Sensitivity comparators

Breadth3 remains a non-promotable sensitivity comparator because it traded more and retained materially higher drawdown.

Breadth5 remains a non-promotable sensitivity comparator because it protected capital but suppressed too much opportunity.

Breadth4 remains the frozen primary mechanism.

## Observability issue

The generated MQL source correctly defines the V46 candidate count and ledgers, but the inherited manifest writer emitted stale metadata for candidate_count/source_file. This did not invalidate trade evidence because source SHA, compiled source and candidate ledgers identified the V46 candidates.

## Decision

Formal status remains HOLD because the preregistered sign-count gate failed. Economically, the breadth mechanism was validated strongly enough that another same-sample parameter sweep was not justified.

Do not tune breadth count, HL10 half-life or the 0.05 score threshold on this evidence.

The project subsequently froze breadth4 and moved to fresh forward/operational evidence, then to V49 native broker-DEMO execution rehearsal.

Current production/live research and deployment target is governed by ADR-049. The historical V46 live-authorization marker must not be interpreted as a permanent project ban.
