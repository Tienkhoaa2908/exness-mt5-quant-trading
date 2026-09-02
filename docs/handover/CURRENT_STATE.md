# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 06:50 (+07)

## Authority

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`.

Active research branch: `agent/v70-exit-harvest-research`.

V70 parent: `12c97d81d6846b2b0c81cad234d698c25c9a3341` from `agent/v69-one-shot-prospective-demo`.

Always resolve the current remote HEAD, then read `OPERATING_PROTOCOL.md`, this file, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-HEAD CI before acting.

SHORT remains disabled/rejected. REAL authorization remains false.

## Frozen V69 identity

Frozen branch: `agent/v69-confirm-separation-retest-research`.
Frozen HEAD: `0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`.
Accepted evidence ZIP SHA256: `e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`.
Frozen forward source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`.

Contract: XAUUSDm M15; LONG only; lot 0.01; structural risk about $0.85-$1.10; emergency loss guard about $1.20; target +$3.50; risk/spread >=4; reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready; fixed stop; inherited +$2 -> about +$1 ratchet; SHORT disabled; REAL false.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34` under the historical legacy headline accounting. Sep 2025-May 2026 is development-only.

## Settled questions

- DEMO execution transport PASS: actual 0.01 XAUUSDm BUY+close returned server `10009 / done` both ways.
- Live no-trade window: 83/83 preserved directional evals were short-edge/bearish and rejected by LONG-only isolation. Not a broker/order-send defect. SHORT remains rejected.
- All-bar selector coverage: 23,526 M15 bars, LONG 3,576, SHORT 1,744, neutral 18,206; LONG = 67.218% of directional selections. Global LONG starvation rejected.
- Downstream LONG funnel: `460 pending -> 404 micro-arm -> 167 touch -> 95 penetration -> 51 reversal-confirm -> 49 separation -> 24 retest/entry -> 24 deals`. Separation is not the dominant contraction.
- Cycle economics: HARD_STRUCTURAL 235, TTL 120, CONTEXT_QUALITY 80, SENT 24, UNTERMINATED 1. BREAKOUT_RETEST_BOS produced 22/24 trades; PULLBACK_SWEEP_BOS only 2, so do not promote its PF.
- Old `V64_NOISE_SHADOW` excursion is rejected as actual-trade MFE/MAE because it can continue after the real position exits. Valid old in-trade evidence: 9 PROFIT_LOCK modifies, all 9 modified, 0 logged failures.

## V70 objective

V70 preserves V69 entry and actual exit semantics, measures true excursion only while the owned actual position exists, and evaluates four observation-only exit policies on ordered real ticks:

1. `BASELINE_200_100`: +$2 arm / +$1 floor.
2. `EARLY_100_025`: +$1 / +$0.25.
3. `MID_150_050`: +$1.50 / +$0.50.
4. `TIERED_100_025_200_100`: +$1/+0.25 then upgrade to +$1 after +$2.

Shadow code does not close/modify positions and adds no orders. Result is reused development evidence only.

## First complete Windows V70 tester campaign — RAW EVIDENCE VALID, FIRST ANALYSIS INVALID

At checkpoint `6d4095f1903f15077fdf805fda1f4485f4ffd314`, the operator completed all nine real-tick months Sep 2025-May 2026.

Generated source SHA256: `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`.
EX5 SHA256: `af321cdfe2f91b672443ad57aa7f33606d8e41d5660607cc3f74f6bf3f6a3f5f`.
Compile: `0 errors, 0 warnings`.
All nine monthly evidence directories were written successfully.

The raw CSV evidence is retained and reusable. The first analyzer output is INVALID for policy selection because of two post-replay analyzer defects:

1. V70 read invented `v1/v2/v3` keys instead of real V64 event fields `value1/value2/value3`, which zeroed true excursion and corrupted policy trigger PnL.
2. Baseline identity compared full round-trip economic PnL (`+$6.44`) against the legacy accepted headline (`+$7.14`). The difference is accounting convention: legacy accepted uses exit-row costs only; economic round-trip includes entry+exit explicit costs.

Do not reuse any first-run `POLICY_*` number, including the apparent EARLY improvement.

## Patched analyzer and fast recovery path

The analyzer/runtime now:

- parses canonical `value1/value2/value3` fields;
- reports `legacy_accepted_identity` separately from `economic_roundtrip_actual`;
- gates 24/10/14/~+$7.14 using legacy accounting;
- compares policy economics consistently against full round-trip economic baseline;
- fails closed if true position-lifetime excursion/policy telemetry remains all zero.

To avoid wasting another ~9-month tester campaign, V70 now supports source-pinned existing-evidence reanalysis with `V70_REANALYZE_EXISTING=1`.

The fast path:

- regenerates expected source text in memory and SHA-checks it against local `OUTPUT_V70/V70ExitHarvestShadowLong.mq5`;
- requires all nine existing monthly directories with non-empty `V64_DEALS.csv` and `V64_EVENTS.csv`;
- requires V70 exit-shadow START/END lifecycle markers;
- then runs only the corrected analyzer and the baseline/telemetry fail-closed guards;
- does not launch MT5, MetaEditor, compile, or Strategy Tester.

Only if source identity/evidence integrity fails should the full tester campaign be rerun.

## Current classification

`V69_RESEARCH=FROZEN`
`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`
`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`
`V69_LONG_SELECTOR_GLOBAL_STARVATION_HYPOTHESIS=REJECTED`
`V69_OLD_NOISE_SHADOW_MFE_AS_TRADE_MFE=REJECTED`
`V70_FIRST_WINDOWS_POLICY_OUTPUT=INVALID_DO_NOT_USE`
`V70_RAW_NINE_MONTH_EVIDENCE=REUSABLE_IF_SOURCE_IDENTITY_PASS`
`V70_ACCOUNTING_CONVENTIONS=SEPARATED`
`V70_EVENT_SCHEMA=value1_value2_value3`
`V70_EXISTING_EVIDENCE_REANALYSIS=IMPLEMENTED`
`V70_ENTRY_SEMANTICS_CHANGED=0`
`V70_REAL_EXIT_SEMANTICS_CHANGED=0`
`V70_COUNTERFACTUAL_EXIT_SHADOW_ONLY=1`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Require all six exact-head workflows completed/success after final handover synchronization.
2. Fast-forward to that exact HEAD and export `V70_EXIT_HARVEST_EXPECTED_HEAD`.
3. Export `V70_REANALYZE_EXISTING=1` and run the normal V70 launcher. MT5/MetaEditor state is irrelevant because this fast path exits before those process checks and does not launch them.
4. Require `V70_EXISTING_EVIDENCE_SOURCE_IDENTITY=PASS`, `V70_EXISTING_EVIDENCE_MONTHS=PASS count=9`, `V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS`, and `V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS` before interpreting policies.
5. Then choose at most one policy if it materially improves economic round-trip net/PF/DD without unacceptable winner damage. Otherwise close exit-harvest research and move immediately to entry/re-entry quality.
6. If existing source/evidence identity fails, only then fall back to a full nine-month tester replay.
7. Do not enable SHORT. Do not authorize REAL money.
