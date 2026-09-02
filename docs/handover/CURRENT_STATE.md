# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Updated: 2026-09-03 06:45 (+07)

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

Frozen forward parent source SHA256: `0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`.

Contract: XAUUSDm M15, LONG only, lot 0.01, structural risk about $0.85-$1.10, emergency loss guard about $1.20, target +$3.50, risk/spread >=4, reclaim -> separation >=$1.30 -> later retest -> confirm age >=30s -> entry-ready -> preflight, fixed structural stop, inherited +$2 -> about +$1 profit ratchet, SHORT disabled, REAL false.

Accepted V69 development headline: `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34` under the historical V68/V69 headline accounting convention. Sep 2025-May 2026 remains development-only, not untouched independent evidence.

## Settled questions

- Actual DEMO transport PASS at `614d68eca2fd30dbfe98adad02f82d61a0302aca`: one XAUUSDm 0.01 BUY and close both returned server `10009 / done`.
- Live no-trade window localized: preserved evals were `83/83 short_edge`, direction -1, H1/H4 bearish, rejected by LONG-only isolation. Do not infer a broker/order-send failure and do not enable SHORT.
- All-bar selector coverage Sep 2025-Aug 2026: 23,526 M15 bars; LONG 3,576; SHORT 1,744; neutral 18,206; LONG = 67.218% of directional selections. Global LONG starvation rejected.
- Accepted downstream LONG funnel: `460 pending -> 404 micro-arm -> 167 touch -> 95 penetration -> 51 reversal-confirm -> 49 separation -> 24 retest/entry -> 24 deals`. V69 separation is not the dominant contraction.
- Cycle economics: HARD_STRUCTURAL 235/460, TTL 120, CONTEXT_QUALITY 80, SENT_ORDER 24, UNTERMINATED 1. Breakout-retest produced 22/24 trades; pullback-sweep only 2, so its high PF is not promotable evidence.
- Old `V64_NOISE_SHADOW.max_pnl/min_pnl` interpretation as real trade-lifetime MFE/MAE is rejected because that shadow can continue up to 480 minutes after the actual position exits. Valid old in-trade evidence: 9 PROFIT_LOCK modify events, 9 modified, 0 logged failures.

## V70 objective

V70 is one ordered real-tick Strategy Tester replay over Sep 2025-May 2026. It preserves V69 entry and actual exit semantics, measures excursion only while the owned actual position exists, and shadows four non-trading exit policies simultaneously:

1. `BASELINE_200_100`: +$2 arm / +$1 floor.
2. `EARLY_100_025`: +$1 arm / +$0.25 floor.
3. `MID_150_050`: +$1.50 arm / +$0.50 floor.
4. `TIERED_100_025_200_100`: +$1/+0.25, then upgrade to +$1 after +$2.

Shadow code cannot close/modify positions or add BUY/SELL orders. The comparison is reused development evidence only.

## First complete Windows V70 replay — HARNESS/ANALYZER INVALIDATED

Operator completed all nine real-tick months at exact code checkpoint `6d4095f1903f15077fdf805fda1f4485f4ffd314` after closing MT5/MetaEditor.

Compile/evidence transport succeeded: generated V70 source SHA256 `b67656b5aae22783eb949d72f60d6a42a51a4a7bf10178af0032c3e7747a5536`; EX5 SHA256 `af321cdfe2f91b672443ad57aa7f33606d8e41d5660607cc3f74f6bf3f6a3f5f`; MetaEditor result `0 errors, 0 warnings`; all Sep 2025-May 2026 tester months produced evidence.

The analyzer then correctly failed closed, and none of that run's `POLICY_*` economics may be promoted or interpreted. Two harness/analyzer defects were source-audited:

### 1. Accounting conventions were mixed

The V70 economic parser used full round-trip explicit costs: exit profit + entry costs + exit costs, producing `+$6.44` on the same 24-trade cohort.

The accepted V69 headline `+$7.14` uses the legacy V68/V69 convention: exit profit + exit-row commission/swap/fee only.

The `+$0.70` difference therefore does not by itself prove strategy drift. V70 must report both quantities:

- `legacy_accepted_identity` for the fail-closed 24/10/14/~+$7.14 cohort identity;
- `economic_roundtrip_actual` for honest policy economics including entry+exit explicit costs.

Policy deltas are compared against the economic round-trip baseline, not against the legacy headline.

### 2. V70 event numeric fields were parsed with the wrong column names

The actual V64 event CSV schema uses `value1/value2/value3`, while the V70 analyzer and its synthetic test used `v1/v2/v3`.

That caused the first replay to print all-zero `TRUE_EXCURSION` and corrupted all shadow trigger PnL values. Therefore the apparent first-run policy numbers, including the small apparent `EARLY_100_025` improvement, are INVALID and must not be reused.

## V70 patched replay gate

Code checkpoint `6d8138490b7413aed5b38e273275bd60380460d4` fixes both defects:

- canonical event parsing now reads `value1/value2/value3`, with compatibility aliases only as fallback;
- accepted identity and economic round-trip accounting are separated explicitly;
- runtime baseline guard checks the legacy accepted 24/10/14/~+$7.14 identity;
- runtime adds `V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS` and fails closed if excursion/policy telemetry remains all zero;
- tests now use the real V64 event field names and cover dual accounting plus all-zero telemetry rejection.

No V69 entry rule, actual exit rule, SHORT rule, or REAL authorization was changed by this patch.

## Current classification

`V69_RESEARCH=FROZEN`

`V69_HISTORICAL_REPLAY=DEVELOPMENT_ONLY_NOT_INDEPENDENT`

`V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS`

`V69_LONG_SELECTOR_GLOBAL_STARVATION_HYPOTHESIS=REJECTED`

`V69_OLD_NOISE_SHADOW_MFE_AS_TRADE_MFE=REJECTED`

`V70_FIRST_WINDOWS_POLICY_OUTPUT=INVALID_DO_NOT_USE`

`V70_ACCOUNTING_CONVENTIONS=SEPARATED`

`V70_EVENT_SCHEMA=value1_value2_value3`

`V70_ENTRY_SEMANTICS_CHANGED=0`

`V70_REAL_EXIT_SEMANTICS_CHANGED=0`

`V70_COUNTERFACTUAL_EXIT_SHADOW_ONLY=1`

`SHORT_ENABLED=0`

`REAL_MONEY_AUTHORIZED=0`

## Next gate

1. Require all exact-head workflows to be completed/success after final handover synchronization.
2. Keep MT5 and MetaEditor closed for the corrected Strategy Tester replay.
3. Fast-forward to the exact final `agent/v70-exit-harvest-research` HEAD and export `V70_EXIT_HARVEST_EXPECTED_HEAD` to it.
4. Run `runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh` once more. This rerun is required because the first policy output was numerically corrupted by the analyzer schema bug.
5. Require both `V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS` and `V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS` before interpreting any `POLICY_*` line.
6. Then choose at most one exit candidate if it materially improves economic round-trip net/PF/DD without unacceptable winner damage. Otherwise close exit-harvest research and move to entry/re-entry quality.
7. Do not enable SHORT. Do not authorize REAL money.
