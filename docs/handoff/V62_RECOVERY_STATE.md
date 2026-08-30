# V62 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v62-direction-isolated-entry-refinement-research`
- V62 is Strategy Tester research only. REAL-money authorization remains false.

## Accepted V62 code / runtime checkpoint

- Final V62 evidence head: `1826e1ffd40051621bd89733016307bcbc10475f`.
- That exact head passed GitHub Actions quality run `#815` (`33307939973`) completely.
- V62 Windows MetaEditor subsequently compiled both direction-specific experts with `Result: 0 errors, 0 warnings`.
- Operator returned the completed 8-pass V62 evidence bundle.
- ZIP SHA256: `8a506208924c547be53bfcfbc82cf46c22581f74ae9f9ac1c14c3266665b46d4`.
- ZIP CRC: PASS.
- Bundle manifest: 62 listed payload files; all 62 SHA256 values match and there are no unlisted payload files other than the manifest itself.
- Protocol: XAUUSDm M15, fixed lot 0.01, initial deposit USD 40, leverage 1:200, Strategy Tester Model=4 real ticks, tester-only, REAL authorization false.
- Fixed weeks: 2026-08-03..08, 08-10..15, 08-17..22, 08-24..29. Each week has independent LONG-only and SHORT-only pass, total 8 passes.

## Accepted V61 evidence motivating V62

Accepted V61 evidence/source head: `65cb308818a835c25e5fff17d8d71351ab901267`.
Accepted V61 evidence ZIP SHA256: `1a421abe21d2879c25dd2ea1e46cd3ce29308c25d0e364bb611d53b1d0ba571f`.

V61 dedicated screen covered 23,526 M15 rows from 2025-09-01 through 2026-08-28 and observed 3,576 LONG plus 1,744 SHORT strict directional signals. Thus the directional engine is not long-only.

V61 Model=4 execution over its selected windows produced four feasible trades, all LONG: 3 wins / 1 loss, net about `+$6.39`, PF about `8.26`, average win about `+$2.42`, average loss `-$0.88`, maximum loss `-$0.88`. Profit-lock modification succeeded three times and failed zero times. Shadow `$3` outperformed `$2` in that tiny sample; `$4` failed.

Critical limitation: V61 did not direction-isolate its real-tick passes. LONG trades could occur in SHORT-labelled weeks. Therefore V61 contains no valid SHORT broker-PnL evidence.

Within the two V61 SHORT-labelled windows there were 38 SHORT directional signals but zero feasible SHORT entries at the `$0.75-$1.25` structural-risk band. Among candidates reaching cash-risk calculation, approximate SHORT risk ranged from `$2.39` minimum to `$4.94` median and about `$9.66` maximum. Both M15 and M5 stop sources remained too far from market entry. This motivated V62 entry refinement rather than widening the risk cap.

## V62 frozen architecture

- XAUUSDm M15.
- Fixed lot `0.01`.
- Structural planned-risk band `$0.75-$1.25`.
- Primary target `+$3`.
- Profit ratchet `+$2 -> protect +$1`.
- Strict H4/H1 trend logic and symmetric directional scoring.
- M15 directional signal arms a pending setup instead of entering immediately.
- Closed M5 must show trend-aligned retrace/retest near EMA20.
- Closed M1 must show a turn back in the trade direction.
- Structural stop/target and 0.01 cash risk are recalculated at the refined market price.
- `OrderCheck()` precedes simulated broker submission.
- Direction isolation is compiled into separate LONG-only / SHORT-only experts.
- V62 does not widen the stop budget merely to force frequency.

## V62 completed one-month results

Monthly actual broker-simulated result across the isolated passes:

- Actual round trips: `11`.
- Direction: all `11 LONG`, `0 SHORT`.
- Wins/losses: `3 / 8`; win rate `27.27%`.
- Gross profit: `+$9.24`.
- Gross loss: `-$8.10`.
- Net: `+$1.14` (about +2.85% of the USD 40 initial balance when viewed only as isolated-pass PnL sum; not a concurrent equity curve).
- PF: `1.1407`.
- Average winner: `+$3.08`.
- Average loser: `-$1.0125`.
- Maximum actual single loss: `-$1.28`.
- All 11 feasible entries used M5 stop source. This is a material change from V61, where all four feasible stops were M15.
- V62 therefore increased actual entry count from V61's 4 exploratory feasible trades to 11 across the four-week protocol, but the edge is currently thin and one-sided.

Week breakdown:

- Week1 LONG: 1 trade, 0W/1L, net `-$0.98`, PF 0.
- Week1 SHORT: 4 strict SHORT signals / 4 pending arms, 0 refined entries, 0 trades; 29 refinement waits were all `structural_risk_cash_cap`.
- Week1 combined isolated sum: `-$0.98`.
- Week2 LONG: 3 trades, 1W/2L, net `+$1.27`, PF `1.6615`, average loss `-$0.96`, max loss `-$1.01`.
- Week2 SHORT: 0 strict SHORT signals / 0 trades.
- Week3 LONG: 4 trades, 2W/2L, net `+$3.92`, PF `2.8404`, average loss `-$1.065`, max loss `-$1.11`.
- Week3 SHORT: 0 strict SHORT signals / 0 trades.
- Week4 LONG: 3 trades, 0W/3L, net `-$3.07`, PF 0, average loss `-$1.0233`, max loss `-$1.28`.
- Week4 SHORT: 0 strict SHORT signals / 0 trades.

Monthly pending/refinement telemetry:

- LONG pending arms: `427`.
- SHORT pending arms: `4`.
- LONG refined entries sent: `11`.
- SHORT refined entries sent: `0`.
- Recent August test month was strongly one-sided under the strict H4/H1 definition. Do not force SHORT count merely to make the report symmetric.
- SHORT capability still needs a bearish-window execution validation because this recent month contained only four strict SHORT signals.

## V62 exit / risk observations

Shadow target result over the same 11 LONG price paths:

- `$2`: 3W/8L, net `-$1.91`, PF about `0.7585`.
- `$3`: 3W/8L, net `+$1.09`, PF about `1.1378`.
- `$4`: 3W/8L, net `+$4.09`, PF about `1.5171`.

Do not promote `$4` from only three winning price paths; this is exploratory evidence only. The user explicitly does not require large winners and prioritizes win frequency plus small losses.

Actual ratchet/broker PnL was `+$1.14`, close to the pure `$3` shadow result. Three losses had meaningful favorable excursion before ultimately losing (approximately +$0.94, +$0.80 and +$1.17 on their shadow paths), which makes earlier profit-protection policies worth preregistered testing. Tick-order-aware shadow policies are required; MFE alone is insufficient to claim those losses could safely have been avoided.

Planned structural risk was capped at `$1.25`, but one actual exit lost `$1.28`. This is execution/slippage evidence that planned stop risk is not the same as realized maximum loss. Future research must explicitly leave headroom or test an absolute cash-loss emergency layer if the practical goal is to keep realized losses near `$1`.

## Important V62 methodology bug discovered after evidence review

V62's intended pending expiry is 240 minutes, but `V62ArmPending()` overwrites `g_v62_pending_armed=TimeCurrent()` whenever another same-direction M15 signal arrives. With continuous signals, this resets the timer repeatedly and can extend a pending setup indefinitely. The completed bundle contains no `expired` pending-end reason, consistent with this lifecycle issue.

Next version must:

1. anchor TTL to the **first arm** of a pending setup;
2. not extend TTL on repeated same-direction signals;
3. optionally refresh the feature snapshot without changing first-arm time only under a preregistered rule;
4. revalidate current M15/H1/H4 direction immediately before refined entry so stale setup state cannot enter after the original regime disappears.

Do not reinterpret this as invalidating the 11 historical fills; it is a methodology defect that must be fixed before further promotion.

## Additional exploratory diagnostics, not promotion rules

- One week4 loser entered while both DI direction and MACD direction opposed the LONG side; post-hoc momentum veto research is reasonable but is not yet validated.
- Two score-8 entries were losers, but higher-score entries also lost. Do not assume a simple score threshold is an edge without new evidence.
- One week3 trade was soft-loss-closed about one second after entry at roughly `-$1.02`. This shows the system can encounter extremely fast adverse movement even after M5/M1 refinement.
- Week4's 0W/3L result shows regime/change/chop robustness is still weak despite positive monthly aggregate PnL.

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60/V61 merely to recover V62.
- Do not use `git clean`.
- Do not `stash pop` while runtime/tester work is active.
- Do not overwrite accepted historical evidence.
- Do not arm or execute REAL-money trading.
- Do not promote V62 to production from PF 1.14 and 11 all-LONG trades.
- Do not claim SHORT profitability from V62; there were zero SHORT broker trades.
- Do not interpret the isolated-pass LONG+SHORT sum as concurrent portfolio equity.
- Do not widen the loss cap simply to create SHORT trades.

## Next research direction

Use a new version rather than silently mutating accepted V62 evidence. Required research priorities:

1. Fix pending TTL / stale-regime revalidation.
2. Keep a recent four-week benchmark for comparability.
3. Add PnL-independent bearish-window selection from directional/regime evidence so actual SHORT execution can be tested when bearish conditions exist; do not force shorts inside bullish weeks.
4. Preserve fixed lot 0.01 and entry refinement.
5. Research tick-order-aware profit-protection variants (for example earlier arm / smaller lock) alongside the current `+$2 -> +$1` baseline; do not choose a variant from MFE alone.
6. Explicitly measure planned risk versus realized loss and test how to keep practical maximum loss close to `$1` without fabricating structural stops.
7. Report recent-week and bearish-window LONG/SHORT results independently.

## What a new chat should do next

1. Read this file and `docs/handoff/V61_RECOVERY_STATE.md`.
2. Treat V62 ZIP SHA `8a506208924c547be53bfcfbc82cf46c22581f74ae9f9ac1c14c3266665b46d4` as accepted exploratory month evidence.
3. Do not rerun accepted V62 merely for recovery.
4. Continue on a new research branch/version implementing the priorities above.
5. Require static/CI PASS, then Windows MetaEditor 0/0, then fresh Model=4 evidence before making profitability claims.
