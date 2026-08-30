# V63 Recovery State

Last updated: 2026-08-30.

## Repository / branch

- Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
- Local operator repo: `D:\v31_mt5_40usd` / `/d/v31_mt5_40usd`
- Active research branch: `agent/v63-profit-quality-risk-zone-research`
- V63 is Strategy Tester research only. REAL-money authorization remains false.

## V63 static / CI checkpoint

- Core pullback-frequency / risk-zone engine commit: `bc101f9032ed6c4e6d750fb867b2479ac9f3601d`.
- Exact validated pre-handoff head: `32f9f83df112426fead31248244381f29ff408c4`.
- GitHub Actions quality run `#830` (`33311456882`) on head `32f9f83df112426fead31248244381f29ff408c4` completed SUCCESS.
- Passed gates: Python compile, all active Bash launcher syntax including V63, active policy wording, full pytest, secret scan and historical V29 quarantine assertion.
- This is static/Linux/Python evidence only. It is not Windows MetaEditor or MT5 Strategy Tester evidence.
- The final docs-only handoff commit after this checkpoint must itself receive a SUCCESS quality run before being given to the operator as the pinned runtime head.

## Accepted V62 evidence

- V62 evidence head: `1826e1ffd40051621bd89733016307bcbc10475f`.
- V62 evidence ZIP SHA256: `8a506208924c547be53bfcfbc82cf46c22581f74ae9f9ac1c14c3266665b46d4`.
- ZIP CRC passed and all 62 manifest payload hashes matched.
- Both V62 direction-specific experts compiled Windows MetaEditor with 0 errors / 0 warnings.
- Fixed four-week August protocol completed all 8 Model=4 direction-isolated passes.

V62 recent-month actual isolated-pass sum:

- 11 actual trades, all LONG.
- 3 wins / 8 losses, win rate 27.27%.
- Gross profit +$9.24, gross loss -$8.10, net +$1.14, PF about 1.14.
- Average winner +$3.08, average loser -$1.0125, maximum single realized loss -$1.28.
- Week1 -$0.98; week2 +$1.27; week3 +$3.92; week4 -$3.07.
- V62 increased actual entry count versus the earlier tiny V61 sample, but the edge was weak and week4 showed poor transition/chop robustness.
- V62 had zero SHORT broker trades. Week1 contained four strict SHORT signals; all refinement attempts remained above the small structural-risk budget. Weeks2-4 had no strict SHORT signals under H4/H1 alignment.

## Critical V62 methodology defect fixed by V63

V62 intended pending expiry after 240 minutes, but repeated same-direction M15 signals reassigned `g_v62_pending_armed=TimeCurrent()`. Continuous signals could therefore extend a pending setup indefinitely. V63 anchors TTL to the first arm and repeated same-direction signals cannot reset that timestamp.

V63 rebuilds current features immediately before refined entry. Current H4/H1 must still align with the pending side. The current directional selector is also rerun: an actual opposite selector cancels the pending setup, while selector-neutral is allowed during a valid pullback so the entry logic does not mechanically eliminate the pullback it was designed to wait for.

## User-approved V63 profit objective

The operator considers roughly three quality trades in one week acceptable if the strategy can earn materially more than the V62 month. A useful reference case is two +$3.5 winners and one approximately -$1 loser, about +$6 for the week.

This is a research objective, not a promised weekly return. The system must not widen losses or select data by PnL to manufacture this goal.

## Frozen V63 architecture

- XAUUSDm M15.
- Fixed lot 0.01.
- Planned structural cash risk: `$0.60-$1.05`.
- Emergency cash-loss guard: approximately `$1.10`; market execution/slippage means this cannot guarantee an exact realized cap.
- Actual cash target: `+$3.50`.
- Existing profit ratchet control: `+$2 -> protect +$1`.
- Existing tick-level shadow `$2/$3/$4` outcomes remain diagnostics.
- H4/H1 strict directional regime remains.
- Direction scoring remains symmetric LONG/SHORT.
- Pending M15 setup uses first-arm TTL of 240 minutes; repeated same-direction signals are logged as refresh evidence but may not reset TTL.
- Before entry, current H4/H1 must remain aligned; current selector may be neutral during pullback but may not be opposite.
- Existing DI/MACD/ADX are converted into entry-quality vetoes instead of merely adding more score: DI+MACD both opposing blocks entry; weak ADX plus non-aligned M15/BOS blocks entry; a fully opposite M15 trend/structure/BOS state blocks entry.
- Entry refinement is structural-risk-zone-first: current M5 structural stop and current market price must naturally fit the 0.01 risk band before a closed M1 turn can authorize order submission.
- M5 trend structure uses EMA20 versus EMA50 plus confirmed swings; V63 deliberately does not require price to have already reclaimed EMA20 before evaluating structural cash risk, because that could move entry away from the valid stop and suppress frequency.
- V62's explicit M5 EMA20 retest/reclaim entry inputs are removed from the V63 generated execution source.
- No fabricated stop is allowed to fit the cash budget.
- `OrderCheck()` remains mandatory before broker-simulated submission.
- The emergency market-close loss layer runs before normal profit ratchet / soft-loss management on each tick.

## V63 validation protocol

### Fixed recent benchmark

Use the same four complete August 2026 weeks as V62 for direct comparison:

- week1: 2026.08.03 -> 2026.08.08
- week2: 2026.08.10 -> 2026.08.15
- week3: 2026.08.17 -> 2026.08.22
- week4: 2026.08.24 -> 2026.08.29

Each week runs LONG-only and SHORT-only Model=4 real ticks: 8 passes.

### Additional bearish SHORT validation

Run a dedicated PnL-independent Model=2 directional screen from 2025.09.01 through 2026.08.29. The screen is directional-only and must not use execution feasibility or PnL.

Exclude the four benchmark weeks. A bearish week is eligible when:

- strict SHORT directional signals >= 8; and
- SHORT share among strict LONG+SHORT signals >= 60%.

Select the four most recent eligible weeks. Do not use PnL for selection. Run SHORT-only Model=4 real ticks on those four weeks.

Total V63 Model=4 passes: 12.

## Required V63 reporting

For each benchmark week and each direction:

- signals / first arms / pending refreshes;
- risk-zone waits;
- entry-veto reasons;
- refined entries sent;
- trades / wins / losses / win rate;
- net USD / PF / average win / average loss / max realized loss.

Benchmark aggregate must additionally report:

- average trades per week;
- number of weeks with >=3 trades;
- positive weeks;
- weeks net >=$5;
- weeks net >=$6.

Bearish validation must report actual SHORT trades and PnL independently. Zero SHORT trades is a valid failure result and must not be hidden by LONG trades.

## Known CI history / do not misdiagnose

- An early V63 quality run failed three wording/observability assertions; Python compile and launcher syntax passed. These were not MT5/model profitability failures.
- After those fixes, quality run `#829` on `bc101f9032ed6c4e6d750fb867b2479ac9f3601d` had only one remaining historical V62 handoff-wording assertion failure; V63 tests themselves passed.
- The historical V62 assertion was then aligned with the accepted handoff wording. Quality run `#830` on `32f9f83df112426fead31248244381f29ff408c4` completed SUCCESS.

## Safety / recovery rules

- Do not rerun V50/V56/V57/V58/V59/V60/V61/V62 merely to recover V63.
- Do not use `git clean`.
- Do not `stash pop` while runtime/tester work is active.
- Do not overwrite accepted V62 evidence.
- Do not arm or execute REAL-money trading.
- Do not claim V63 Windows PASS until LONG, SHORT and screen experts compile 0/0 and all V63 tester phases finish with an evidence ZIP.
- Do not claim +$6/week as achieved unless fresh evidence actually shows it.
- Do not interpret isolated-pass sums as concurrent account equity.
- Do not widen loss budget merely to hit the weekly trade-count objective.

## What a new chat should do next

1. Read this file and `docs/handoff/V62_RECOVERY_STATE.md`.
2. Resolve the latest exact head of `agent/v63-profit-quality-risk-zone-research`.
3. Verify GitHub Actions on that exact head.
4. Run only the V63 launcher after MT5 and MetaEditor are closed.
5. Require MetaEditor 0 errors / 0 warnings for V63 LONG, SHORT and screen sources.
6. Require annual directional screen coverage, four PnL-independent bearish windows, eight fixed benchmark real-tick passes and four bearish SHORT real-tick passes.
7. Analyze benchmark weekly profitability and frequency first, then actual bearish SHORT execution.
8. If runtime fails, do not rerun older milestones; preserve the first FATAL plus relevant V63 screen/pass diagnostics.
