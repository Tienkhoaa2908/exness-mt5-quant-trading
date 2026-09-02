# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 04:21 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

At the beginning of every project turn resolve current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before changing code or instructing the operator.

## Current objective

Live no-trade transport, direction selection, all-bar direction coverage, downstream LONG funnel, and cycle-level economics are now localized.

The immediate gate is **MFE / MAE / realized-giveback / V61 profit-ratchet audit on the accepted 24 V69 development trades**.

Do not loosen entry gates first. The cycle evidence shows that over half of pending cycles terminate on hard structural failure, while the two softer rejection families have only archetype-level next-cycle associations and do not prove same-setup missed edge.

REAL money remains unauthorized. SHORT remains disabled/rejected. Frozen V69 strategy semantics remain unchanged.

## Frozen V69 identity

Research branch: `agent/v69-confirm-separation-retest-research`

Frozen research HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Contract:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- SHORT disabled/rejected;
- REAL authorization false;
- planned structural cash risk `$0.85-$1.10`;
- emergency cash-loss guard about `$1.20`;
- target `+$3.50`;
- risk/spread `>=4`;
- reclaim -> favorable separation `>= $1.30` -> later retest -> confirmation age `>=30s` -> entry-ready -> preflight;
- fixed structural stop, no widening/clamp;
- inherited V61 profit ratchet arms near `+$2` and attempts to move protection to about `+$1`.

The `$1.30`, `30s`, and any MFE diagnostic thresholds are development choices/diagnostics, not proven universal optima.

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

Checkpoint `614d68eca2fd30dbfe98adad02f82d61a0302aca` opened and immediately closed one probe-owned DEMO BUY `0.01 XAUUSDm`; both server retcodes were `10009 / done`.

Do not rerun the forced transport probe without contradictory evidence. Transport PASS does not prove edge or authorize REAL.

## Live no-trade diagnosis — settled

Preserved live directional evaluations:

- unique rows `83`;
- `short_edge` `83/83`;
- `direction_isolated_out` `83/83`;
- selected direction `-1` `83/83`;
- selector-defined SHORT HTF regime `83/83`;
- H1/H4 trend `-1` `83/83`;
- short score higher `83/83`.

The observed no-trade window was LONG-only abstention in a bearish regime, not broker/order-path failure.

## All-bar selector coverage — PASS

Verified exact directional-core identity between the reused V64 all-bar screen and frozen V69.

Sep 2025-Aug 2026 screen:

- unique M15 rows `23,526`;
- LONG selected `3,576` (`15.2002%` all bars);
- SHORT selected `1,744` (`7.4131%`);
- neutral `18,206` (`77.3867%`);
- LONG share of directional selections `67.218%`;
- HTF regimes: LONG `9,235`, neutral `8,157`, SHORT `6,134`.

LONG opportunity was abundant in multiple Sep-Feb months, collapsed in Mar-Jun 2026, and recovered sharply in Aug. The hypothesis that the LONG selector is globally starved is rejected.

Selector bars are context, not independent setup count.

## Downstream LONG funnel — PASS

Accepted Sep 2025-May 2026 development funnel:

- `PENDING_ARM=460` cycles;
- `MICRO_ENTRY_ARM=404`;
- zone touch `167`;
- penetration `95`;
- reversal confirm `51`;
- separation `49`;
- retest-ready `24`;
- entry-ready `24`;
- refined-entry/sent `24`;
- deals `24`.

Key interpretation:

- the dominant attrition is before/inside pending and micro-entry structure;
- V69 separation is **not** the dominant bottleneck: `51 -> 49` retains about `96.1%`;
- funnel volume alone does not prove rejected-cycle opportunity cost.

## Cycle economics + re-arm recovery — PASS

Operator ran the read-only recovery at exact checkpoint `0ca414f6ea8bfd1e7a3aa842845ec70a1f19e41f` and reproduced accepted identity `24 / 10 / 14 / +$7.14`.

### Terminal families across 460 cycles

- `HARD_STRUCTURAL=235` (`51.087%`);
- `TTL_EXPIRY=120`;
- `CONTEXT_QUALITY=80`;
- `SENT_ORDER=24`;
- `UNTERMINATED=1`.

TTL + context together are `200` cycles (`43.4783%`).

This does **not** justify loosening them automatically. Hard structural failures are the majority and should remain fail-closed absent direct counterfactual evidence.

### Archetype economics

`BREAKOUT_RETEST_BOS`:

- cycles `241`;
- sent `22`;
- conversion `9.1286%`;
- `9W / 13L`;
- gross profit `$19.08`;
- gross loss `$14.32`;
- net `+$4.76`;
- PF `1.332402`.

`PULLBACK_SWEEP_BOS`:

- cycles `219`;
- sent `2`;
- conversion `0.9132%`;
- `1W / 1L`;
- net `+$2.38`;
- PF `3.125`.

The pullback PF is not promotable evidence because it is based on only two trades. Breakout-retest is the actual production engine in this sample (`22/24` trades).

### Rearm associations

Context-quality rejected cycles:

- eligible `80`, next cycle exists `80`;
- next cycle sent `4`, `3W / 1L`, next-cycle net `+$6.90`.

TTL rejected cycles:

- eligible `120`, next cycle exists `119`;
- next cycle sent `8`, `3W / 5L`, next-cycle net `+$2.46`.

Hard-structural rejected cycles:

- eligible `235`, next cycle exists `228`;
- next cycle sent `12`, `4W / 8L`, next-cycle net `-$2.22`.

These are next-cycle associations only. `same_archetype != same setup identity`; cross-month re-arms are not linked. Do not claim that relaxing TTL/context would have captured the positive next-cycle PnL.

### Trade transition evidence

- `L->L = 7`, destination net `-$7.67`;
- `L->W = 6`, destination net `+$16.11`;
- `W->L = 6`, destination net `-$6.65`;
- `W->W = 4`, destination net `+$6.47`.

Loss clustering exists in the development sample, but these counts alone do not justify a post-win/post-loss throttle without counterfactual evidence.

## MFE / giveback recovery — prepared, read-only

Code checkpoint `c60f4a05b14f993745433f94f3c15a58221443e9` adds a current-branch recovery around the pre-existing trade-quality analyzer.

Files:

- `scripts/analyze_v69_mfe_giveback_recovery.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY.py`;
- `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh`;
- `tests/test_v69_mfe_giveback_recovery.py`;
- CI coverage in `.github/workflows/v69_upstream_diag_quality.yml`.

The diagnostic reuses existing accepted V69 development run files:

- deal entry/exit and realized PnL from `V64_DEALS.csv`;
- MFE/MAE from `V64_NOISE_SHADOW.csv` `max_pnl/min_pnl`, matched to deal entry time;
- archetype from the sent `PENDING_ARM` cycle;
- `PROFIT_LOCK` events inside each trade window.

It reports:

- MFE/MAE coverage for the 24 trades;
- median MFE winners/losers and loser MAE;
- realized giveback and winner MFE capture ratio;
- positive-MFE trades that still realized losses;
- sub-`$2` peak round-trip losses where the inherited ratchet could never arm;
- trades with `MFE >= $2` but realized `< $1`, split by whether a `PROFIT_LOCK` event occurred;
- diagnostic MFE threshold reach counts from `$0.5` through `$3.5`;
- breakdown by month and archetype;
- compact per-trade rows.

It intentionally does **not** simulate a trailing-stop counterfactual from MFE alone. A peak value does not contain enough intra-trade path ordering to replay a trailing rule honestly.

The runtime is read-only, launches neither MT5 nor MetaEditor, sends zero orders, leaves frozen V69 unchanged, and fail-closes on accepted `24 / 10 / 14 / +$7.14` deal identity.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_LIVE_NO_TRADE_PRIMARY_CAUSE=LONG_ONLY_REGIME_ABSTENTION_IN_OBSERVED_DIRECTIONAL_EVALUATIONS`

`V69_LONG_SELECTOR_GLOBAL_STARVATION_HYPOTHESIS=REJECTED`

`V69_PENDING_ARM_CYCLES=460`

`V69_HARD_STRUCTURAL_CYCLES=235`

`V69_TTL_EXPIRY_CYCLES=120`

`V69_CONTEXT_QUALITY_CYCLES=80`

`V69_SENT_ORDER_CYCLES=24`

`V69_BREAKOUT_RETEST_SENT=22`

`V69_PULLBACK_SWEEP_SENT=2`

`V69_NEXT_GATE=MFE_GIVEBACK_RATCHET_AUDIT`

`V69_SHORT_ENABLED=0`

`V69_FORWARD_REAL_MONEY_AUTHORIZED=0`

`LEGACY_2_TRADE_48H_DASHBOARD_GATE=OBSOLETE_DO_NOT_WAIT`

`REAL_DEPLOYMENT=NOT_AUTHORIZED`

## Next gate

1. Keep MT5 running; this diagnostic is read-only and does not need MetaEditor.
2. Fast-forward only to the final exact CI-green branch HEAD.
3. Run `runtime/v69_mfe_giveback_recovery/RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh` with `V69_MFE_GIVEBACK_EXPECTED_HEAD` pinned to that SHA.
4. Require accepted deal identity `24 / 10 / 14 / +$7.14`.
5. If `V64_NOISE_SHADOW` coverage is insufficient, stop and diagnose evidence availability; do not invent MFE and do not rerun strategy evidence blindly.
6. If multiple losers show positive MFE but peak `<$2`, research an earlier harvest architecture separately; the current ratchet could not have armed on those trades.
7. If trades reach `MFE >= $2` but realize `<$1`, audit `PROFIT_LOCK` event behavior before changing thresholds.
8. If winner MFE capture is poor, formulate an exit-harvest successor hypothesis, pre-register it, and validate separately. Do not tune on Sep-May and call it independent evidence.
9. Do not loosen entry filters merely to increase turnover.
10. SHORT remains disabled; REAL remains a separate explicit fail-closed deployment/risk decision.
