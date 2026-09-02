# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 05:10 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active research branch: `agent/v70-exit-harvest-research`

Parent checkpoint: `12c97d81d6846b2b0c81cad234d698c25c9a3341` from `agent/v69-one-shot-prospective-demo`.

At the beginning of every project turn resolve the current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

REAL money remains unauthorized. SHORT remains disabled/rejected.

## Current objective

The project is no longer waiting for natural trades and is no longer running the previous diagnostic chain.

Broker transport, live no-trade direction isolation, all-bar selector coverage, downstream LONG funnel, and cycle economics are already localized.

The immediate gate is one **V70 true-position-lifetime exit-harvest replay**. It keeps frozen V69 entry and actual exit semantics unchanged, measures excursion only while the actual V69-equivalent position is open, and evaluates four exit policies in shadow during the same replay.

This V70 replay exists because the previous MFE/giveback diagnostic exposed a measurement-attribution defect: `V64_NOISE_SHADOW.max_pnl/min_pnl` continues after the real position has closed and therefore is not actual trade-lifetime MFE/MAE.

Do not tune the strategy from the old V64 noise-shadow MFE values.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Contract:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- reclaim -> favorable separation `>= $1.30` -> later retest -> confirmation age `>=30s` -> entry-ready -> preflight;
- fixed structural stop, no widening/clamp;
- inherited profit ratchet arms near `+$2` and attempts to protect about `+$1`;
- SHORT disabled/rejected;
- REAL authorization false.

Frozen V69 itself is not being edited by V70 research.

## Accepted V69 development economics

V68 LONG: `28 trades / 10W / 18L / +$2.87 / PF ~1.146 / max DD $6.04`.

V69 LONG: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / max DD $3.34`.

V69 monthly replay:

- Sep 2025 `-$1.84`;
- Oct `+$9.15`;
- Nov `+$1.24`;
- Dec `-$2.28`;
- Jan 2026 `+$0.87`;
- Feb-May flat;
- excluding October: `-$2.01`.

Sep 2025-May 2026 is development evidence, not an untouched holdout.

## Settled execution / opportunity questions

### Actual DEMO broker transport — PASS

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` opened and closed one DEMO BUY `0.01 XAUUSDm`; server retcode was `10009 / done` for both actions.

Do not rerun the forced transport probe without contradictory evidence.

### Live zero-trade window — localized

Preserved live directional evaluations were `83/83 short_edge`, selected direction `-1`, H1/H4 `-1`, and rejected as `direction_isolated_out` by the frozen LONG-only lane.

That window was regime abstention, not generic MT5/broker execution failure.

### All-bar selector coverage — PASS

Sep 2025-Aug 2026 verified all-bar screen:

- M15 rows `23,526`;
- LONG selected `3,576` (`15.2002%`);
- SHORT selected `1,744` (`7.4131%`);
- neutral `18,206` (`77.3867%`);
- LONG share of directional selections `67.218%`.

Global LONG-selector starvation is rejected. Selector rows are context, not independent trade setups.

## Downstream LONG funnel — PASS

Accepted Sep 2025-May 2026 development funnel:

- `PENDING_ARM=460`;
- `MICRO_ENTRY_ARM=404`;
- zone touch `167`;
- penetration `95`;
- reversal confirm `51`;
- separation `49`;
- retest-ready `24`;
- entry-ready `24`;
- sent/deals `24`.

V69 separation retained `49/51` reversal-confirm cycles and is not the dominant contraction layer.

## Cycle economics — PASS

Across `460` pending cycles:

- `HARD_STRUCTURAL=235` (`51.087%`);
- `TTL_EXPIRY=120`;
- `CONTEXT_QUALITY=80`;
- `SENT_ORDER=24`;
- `UNTERMINATED=1`.

Archetypes:

- `BREAKOUT_RETEST_BOS`: `241` cycles, `22` trades, `9W/13L`, `+$4.76`, PF `1.332402`;
- `PULLBACK_SWEEP_BOS`: `219` cycles, only `2` trades, `1W/1L`, `+$2.38`, PF `3.125`.

Do not promote pullback from two trades. Breakout-retest is the economic engine in this development sample (`22/24` sent trades).

Positive next-cycle PnL after TTL/context rejects is association only and does not prove same-setup missed edge. No entry gate has been loosened.

## V69 MFE/giveback recovery — PASS operationally, MFE attribution REJECTED

Operator ran the read-only recovery at exact checkpoint `12c97d81d6846b2b0c81cad234d698c25c9a3341`.

Valid outputs from that run:

- accepted deal identity `24 / 10 / 14 / +$7.14` reproduced;
- all 24 entry timestamps matched a `V64_NOISE_SHADOW` record;
- `PROFIT_LOCK` occurred during the actual entry->exit window for `9` trades;
- all `9` logged profit-lock modify attempts were `modified`;
- logged `modify_failed` trades `0`;
- zero strategy changes, zero orders, REAL authorization false.

Invalid interpretation that must not be reused:

- `V64_NOISE_SHADOW.max_pnl/min_pnl` is not actual position-lifetime MFE/MAE;
- the shadow starts at actual fill but remains active independently after the actual position closes;
- it resolves when its 3x3 synthetic stop/target matrix finishes or after `InpV64NoiseShadowMaxMinutes=480`;
- therefore large values such as `$29`, `$46` or `$118` can occur after the actual deal exit;
- old derived counts such as `22/24 MFE >= $2`, median MFE, median giveback and MFE capture ratio are not evidence for actual exit tuning.

The defect is diagnostic attribution, not a broker or strategy execution defect.

## V70 true-position-lifetime exit-harvest research — implemented

Branch: `agent/v70-exit-harvest-research`.

Pre-handover implementation checkpoint: `968976e33eddc2ae205a882ff3eea4b7d3dc92ef`.

Files:

- `scripts/build_v70_exit_harvest_shadow_source.py`;
- `scripts/analyze_v70_exit_harvest_shadow.py`;
- `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH.py`;
- `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh`;
- `tests/test_v70_exit_harvest_research.py`;
- `.github/workflows/v70_exit_harvest_quality.yml`.

V70 preserves the V69 development entry cohort and actual strategy behavior while adding observation-only exit shadow telemetry.

True excursion state starts only when the actual owned position exists, updates every tick while that position remains open, and ends when the actual position disappears. The V70 analyzer explicitly does not read `V64_NOISE_SHADOW`.

Four policies are evaluated simultaneously without sending extra orders or modifying the actual position:

1. `BASELINE_200_100`: idealized current `+$2` arm / `+$1` floor validation lane;
2. `EARLY_100_025`: `+$1` arm / `+$0.25` floor;
3. `MID_150_050`: `+$1.50` arm / `+$0.50` floor;
4. `TIERED_100_025_200_100`: early `+$1 / +$0.25`, upgraded to `+$1` protection after `+$2`.

These are development counterfactual candidates, not promoted strategy parameters.

The replay runs LONG only across Sep 2025-May 2026 on real tick model 4. Entry semantics are unchanged; actual V69-equivalent exit semantics are unchanged; candidate exits are shadow-only.

If no policy improves economics without materially cutting baseline winners, abandon the exit-harvest hypothesis and return to entry/re-entry quality. If one policy clearly improves the reused development cohort, promote only that policy into a separate actual-exit semantic branch and then replay actual broker/tester behavior. Do not call either result independent evidence.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_LONG_SELECTOR_GLOBAL_STARVATION_HYPOTHESIS=REJECTED`

`V69_PENDING_ARM_CYCLES=460`

`V69_SENT_ORDER_CYCLES=24`

`V69_BREAKOUT_RETEST_SENT=22`

`V69_OLD_NOISE_SHADOW_MFE_AS_TRADE_MFE=REJECTED`

`V69_VALID_IN_TRADE_PROFIT_LOCK_MODIFIED_TRADES=9`

`V70_EXIT_HARVEST_RESEARCH=IMPLEMENTED_PENDING_WINDOWS_REPLAY`

`V70_ENTRY_SEMANTICS_CHANGED=0`

`V70_REAL_EXIT_SEMANTICS_CHANGED=0`

`V70_COUNTERFACTUAL_EXIT_SHADOW_ONLY=1`

`SHORT_ENABLED=0`

`REAL_MONEY_AUTHORIZED=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

## Next gate

1. Require the final V70 branch HEAD to have all exact-head workflows `completed/success` after handover synchronization.
2. This replay needs MetaTrader 5 and MetaEditor closed because it uses Strategy Tester/MetaEditor compile. It is not a natural-trade waiting gate.
3. Fast-forward only to the exact final `agent/v70-exit-harvest-research` HEAD and export `V70_EXIT_HARVEST_EXPECTED_HEAD` to that SHA.
4. Run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once.
5. The one run replays all nine development months and all four shadow policies together; do not run four separate tester campaigns.
6. Require the baseline actual cohort to reproduce the accepted V69 economics before interpreting candidate policy results.
7. Compare candidate net, PF, drawdown, changed-trade count, baseline-winner cuts, baseline-loss improvements, and true in-position excursion.
8. Promote at most one candidate only if the economics justify it. Otherwise close the exit-harvest hypothesis.
9. SHORT remains disabled. REAL remains unauthorized.
