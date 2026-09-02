# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 03:21 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

## Current objective

The observed live no-trade path and the all-bar selector-coverage question are now both localized.

The immediate gate is **downstream LONG funnel localization on accepted V69 development evidence**:

`LONG selector context -> initial archetype/stop validation -> PENDING_ARM cycle -> MICRO_ENTRY_ARM -> zone touch -> penetration -> reversal confirm -> separation -> retest -> entry-ready -> REFINED_ENTRY/fill`.

Do not divide `3,576 LONG-selected M15 bars` by `24 trades` and call that a setup conversion rate. Repeated adjacent LONG bars are selector context, not one-to-one independent setups. Use `PENDING_ARM` cycles and stage reach to localize contraction.

The funnel diagnostic is development-only and read-only. It can identify where V69 discards opportunities, but it cannot by itself prove that rejected cycles would have been profitable. Counterfactual price-path/shadow analysis is required before loosening a dominant gate.

REAL money remains unauthorized. SHORT remains disabled/rejected.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Contract:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only for current live diagnosis;
- SHORT disabled/rejected;
- REAL authorization false;
- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- reclaim -> favorable separation `>= $1.30` -> later retest -> confirmation age `>=30s` -> `POST_CONFIRM_ENTRY_READY` -> `V64OrderPreflight`;
- fixed structural stop, no widening/clamp.

The `$1.30` and `30s` values are development choices, not proven universal optima.

## Accepted development evidence

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 retained all ten V68 winners while removing four losers, but `10/14` surviving V69 losers closed within 60 seconds.

Monthly V69 replay:

- Sep 2025 `-$1.84`;
- Oct `+$9.15`;
- Nov `+$1.24`;
- Dec `-$2.28`;
- Jan 2026 `+$0.87`;
- Feb-May flat;
- excluding October: `-$2.01`.

Sep 2025-May 2026 V69 replay is development evidence, not an independent holdout.

## Actual DEMO execution transport — PASS

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` successfully opened and immediately closed one probe-owned DEMO BUY `0.01 XAUUSDm`; both server retcodes were `10009 / done`.

This settles current MT5 <-> broker market-order transport. Do not rerun the forced transport probe without contradictory evidence. Transport PASS does not prove strategy edge or authorize REAL.

## Live no-trade diagnosis — settled

Aggregate preserved live ENTRY_EVAL evidence:

- raw rows `83`;
- unique rows `83`;
- `short_edge` `83/83`;
- `direction_isolated_out` `83/83`;
- selected direction `-1` `83/83`;
- selector-defined `SHORT_HTF_REGIME` `83/83`;
- H1 trend `-1` `83/83`;
- H4 trend `-1` `83/83`;
- short score higher `83/83`;
- long-minus-short score margin never better than `-9`.

Observed live directional candidates were therefore rejected by frozen LONG-only isolation before `PENDING_ARM`. Broker transport, reclaim, separation and retest were not the blockers for these 83 evaluations.

Do not enable historical SHORT and do not loosen LONG merely to manufacture turnover.

## All-bar selector coverage — PASS

Operator ran the selector-coverage recovery at exact checkpoint:

`4f584ec4b8207c3f3ea2d7a9e3a95b27bcc91f60`

The runtime proved the reused V64 all-bar screen and frozen V69 have an exact directional-core match across feature helpers, scoring, `V64BuildFeatures`, `V64SelectDirection`, `InpV64MinDirectionalScore`, and `InpV64MinScoreEdge`.

Coverage from `2025-09-01 00:00` through `2026-08-28 20:45`:

- unique M15 rows: `23,526`;
- feature ready: `100%`;
- LONG selected: `3,576` (`15.2002%` of all bars);
- SHORT selected: `1,744` (`7.4131%`);
- neutral: `18,206` (`77.3867%`);
- LONG share of directional selections: `67.218%`;
- SHORT share: `32.782%`;
- HTF regimes: LONG `9,235`, neutral `8,157`, SHORT `6,134`.

Decision reasons:

- `long_edge=3576`;
- `short_edge=1744`;
- `regime_neutral=12669`;
- `score_below_threshold=3497`;
- `no_trigger=2040`.

### Monthly directional coverage

| Month | LONG | SHORT | Neutral |
|---|---:|---:|---:|
| 2025-09 | 630 | 0 | 1,383 |
| 2025-10 | 512 | 121 | 1,475 |
| 2025-11 | 278 | 91 | 1,454 |
| 2025-12 | 478 | 35 | 1,492 |
| 2026-01 | 579 | 9 | 1,334 |
| 2026-02 | 232 | 85 | 1,513 |
| 2026-03 | 51 | 365 | 1,616 |
| 2026-04 | 200 | 172 | 1,559 |
| 2026-05 | 57 | 265 | 1,600 |
| 2026-06 | 14 | 425 | 1,569 |
| 2026-07 | 105 | 172 | 1,815 |
| 2026-08 | 440 | 4 | 1,396 |

This rejects the hypothesis that frozen V69's LONG selector is globally starved. LONG opportunity is strongly regime-dependent: it was abundant in several months, collapsed during Mar-Jun 2026, and recovered sharply by Aug in the historical screen.

Coverage is development observability, not independent edge evidence.

## Downstream LONG funnel recovery — prepared, read-only

Implementation checkpoints:

- `a1d05e88e83f01adf346ce088a4dfa18b822fe7c` — initial cycle-based downstream funnel recovery;
- `3685ec2cce1029cc5b535bfa7b9b69954e35f4aa` — fail-closed accepted-evidence identity guard/tests.

Files:

- `scripts/analyze_v69_downstream_long_funnel.py`;
- `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py`;
- `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_downstream_long_funnel.py`.

The diagnostic:

1. reuses the verified all-bar V64 screen for selector context;
2. reads existing V69 Sep 2025-May 2026 LONG run telemetry, or the accepted local V69 research ZIP;
3. fails closed unless development deals match accepted V69 identity `24 trades / 10W / 14L / +$7.14` within the defined cash tolerance;
4. if ZIP recovery is required, requires the exact accepted ZIP SHA256;
5. treats LONG selector bars/streaks only as context;
6. starts the economic flow denominator at actual `PENDING_ARM` cycles;
7. counts cycle reach through micro-arm, zone touch, penetration, reversal confirmation, separation, retest, entry-ready and refined entry;
8. reports pre-pending reject reasons, terminal cycle reasons, largest stage drop and month-by-month funnel;
9. never launches MT5/MetaEditor and sends zero orders.

The result localizes the dominant contraction. It does **not** prove the opportunity cost or profitability of rejected cycles.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_LIVE_NO_TRADE_PRIMARY_CAUSE=LONG_ONLY_REGIME_ABSTENTION_IN_OBSERVED_DIRECTIONAL_EVALUATIONS`

`V69_PRE_PENDING_SHORT_EDGE=83_OF_83`

`V69_ALL_BAR_ROWS=23526`

`V69_ALL_BAR_LONG_SELECTED=3576`

`V69_ALL_BAR_SHORT_SELECTED=1744`

`V69_ALL_BAR_NEUTRAL=18206`

`V69_LONG_SELECTOR_GLOBAL_STARVATION_HYPOTHESIS=REJECTED`

`V69_NEXT_GATE=DOWNSTREAM_LONG_PENDING_CYCLE_FUNNEL`

`V69_SHORT_ENABLED=0`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Keep MT5 running; do not restart it for this diagnostic.
2. Do not rerun the execution probe or previous upstream selector diagnostic.
3. Fast-forward only to the final exact CI-green branch HEAD.
4. Run `runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY_GIT_BASH.sh` once with the exact-head environment contract.
5. If accepted V69 evidence identity fails, stop and diagnose artifact identity; do not regenerate strategy evidence blindly.
6. Interpret the largest `PENDING_ARM`-cycle stage drop and terminal reasons.
7. Do not loosen the dominant gate from funnel volume alone. Build a counterfactual/shadow outcome study for rejected cycles before any successor strategy change.
8. Keep frozen V69 semantics unchanged during diagnosis.
9. SHORT remains a separate research question and stays disabled.
10. REAL remains a separate explicit fail-closed deployment/risk decision.
