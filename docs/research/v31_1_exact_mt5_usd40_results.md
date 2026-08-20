# V31.1 — exact MT5 USD40 model-gate results

Date: 2026-08-20
Branch: `agent/v30-ml-dl-feature-lake`
Safety: Strategy Tester / virtual-book research only. REAL-MONEY LIVE TRADING IS FORBIDDEN.

## Evidence acceptance

Uploaded result ZIP SHA-256:

`7459ba6b5508f42fb555c9bf8ade50a97bab7abccffc7067e095d593b256911b`

The bundle contains seven complete V31.1 Strategy Tester passes:

- baseline
- CatBoost expected-R gate
- ExtraTrees expected-R gate
- DeepMLP 64-32-16 expected-R gate
- LinearSVM / LinearSVR control
- CatBoost AND ExtraTrees
- majority 2-of-4

For all seven passes:

- MetaEditor result: `0 errors, 0 warnings`;
- MT5 process return code: `0`;
- collection completed with fresh run id;
- manifest: `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`;
- `continuous_usd40=1`;
- exact test period: `2026-02-01 -> 2026-08-01`;
- tester deposit: USD40;
- leverage assumption: 1:200;
- continuous decision book: `usd40_r1p0_cent_continuous`;
- research risk target: 1.00% of current virtual-book balance per trade.

The causal model tape was reused only after exact SHA verification:

`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

This matches the pinned reference byte-for-byte.

## Primary same-candidate comparison

Primary candidate is frozen as:

`adaptive_ewma_hl8_thr0`

| Mode | End USD | Total return | Geo monthly | Months >=15% | Positive months | Worst month | Max MTM DD | Trades | AvgR | Ledger PF | Turnover / $40 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 55.89% | 7.6807% | 2/6 | 4/6 | -4.0078% | 10.8159% | 222 | 0.2401R | 1.5579 | 1045.67x |
| DeepMLP | 60.4393 | 51.10% | 7.1215% | 2/6 | 4/6 | -1.5499% | 7.3551% | 146 | 0.3329R | 1.8037 | 728.65x |
| CatBoost | 51.2744 | 28.19% | 4.2254% | 1/6 | 4/6 | -5.3146% | 11.8421% | 172 | 0.1559R | 1.3845 | 695.19x |
| CatBoost AND ExtraTrees | 47.3229 | 18.31% | 2.8415% | 0/6 | 3/6 | -3.7482% | 12.2095% | 118 | 0.1930R | 1.3749 | 449.94x |
| majority 2-of-4 | 46.1485 | 15.37% | 2.4117% | 0/6 | 3/6 | -8.2447% | 18.1616% | 202 | 0.1286R | 1.1828 | 765.98x |
| ExtraTrees | 45.6841 | 14.21% | 2.2392% | 1/6 | 4/6 | -5.3691% | 14.7440% | 134 | 0.1359R | 1.2692 | 502.40x |
| LinearSVM | 44.0550 | 10.14% | 1.6223% | 0/6 | 4/6 | -5.6866% | 9.7890% | 179 | 0.0952R | 1.1296 | 687.56x |

`profit_factor` above is recomputed from the exact MT5 trade-ledger `total_pnl` field. The original V31.1 analyzer incorrectly looked for `net_pnl` in the trade ledger and therefore printed NaN; the analyzer has been repaired.

## Monthly primary returns

| Month | Baseline | DeepMLP | CatBoost | ExtraTrees | LinearSVM | CB+ET | Majority |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-02 | -0.6979% | +7.2977% | +1.8904% | -5.3691% | -5.6866% | -3.7482% | -4.5874% |
| 2026-03 | -4.0078% | -0.2966% | -5.3146% | -4.9805% | +0.3146% | -1.5677% | -8.2447% |
| 2026-04 | +0.5821% | -1.5499% | -1.5284% | +0.6041% | -1.8804% | -0.9666% | -3.0224% |
| 2026-05 | +12.3327% | +5.7008% | +11.4435% | +5.8588% | +3.3990% | +10.5200% | +8.6885% |
| 2026-06 | +20.8605% | +15.8341% | +20.1817% | +15.5510% | +1.2020% | +13.7154% | +14.1869% |
| 2026-07 | +19.7628% | +17.1733% | +0.7442% | +3.2150% | +13.3800% | +0.3281% | +9.4939% |

## Target gap

A 15% geometric monthly return for six consecutive months would turn USD40 into approximately:

`40 * 1.15^6 = USD92.52`

The primary baseline ends at USD62.36. Therefore the current exact-MT5 baseline is materially short of the target; it is not appropriate to describe the gap as parameter noise.

No primary model meets the 15% monthly target. Baseline reaches >=15% in only 2/6 months.

## What the model experiment actually says

The binary entry-gate framing is the limiting architecture.

DeepMLP materially improves trade quality and risk efficiency:

- AvgR: 0.2401R -> 0.3329R;
- ledger PF: 1.5579 -> 1.8037;
- max MTM DD: 10.8159% -> 7.3551%;
- trades: 222 -> 146;
- turnover: 1045.67x -> 728.65x initial capital;
- volume rejects: 62 -> 17.

But the same gate cuts too much profitable breadth, so geometric return falls from 7.68% to 7.12% per month. CatBoost, ExtraTrees and LinearSVM are materially worse on the primary exact-MT5 economics.

Decision:

- DeepMLP = useful risk/quality signal, **not** a return winner.
- CatBoost = reject as primary binary gate.
- ExtraTrees = reject as primary binary gate.
- LinearSVM = reject as primary binary gate.
- simple model voting = reject as primary binary gate.

## Exit/capture diagnostic

Primary baseline trade ledger, 222 trades:

- realized mean R: 0.2401R;
- mean MFE: 1.3310R;
- median MFE: 1.0871R;
- mean MAE: -0.7033R;
- mean giveback: 1.0909R;
- 122/222 trades reach at least +1R MFE;
- 44/222 reach at least +2R MFE;
- 30/222 reach at least +3R MFE;
- 9 of the 122 trades that reached +1R still finish at <=0R.

This is not proof that MFE was causally capturable, but it shows that the system's return gap is not only an entry-quality problem. A large amount of favorable excursion exists before realized exit.

## Exploratory best-candidate clue

Best-candidate-per-mode is not promotion evidence because it is selected after observing the same six months. Still, one clue is worth carrying into architecture research:

- baseline `adaptive_ewma_hl10_thr0p05`: 7.7433% geometric/month, DD 9.03%;
- DeepMLP `adaptive_ewma_hl10_thr0p05`: 7.5099% geometric/month, DD 6.71%;
- majority 2-of-4 `slow_mom_16h24h_timebox8h`: 7.3896% geometric/month, 6/6 positive months, DD 7.79%.

These numbers motivate complementary-family allocation research, not post-hoc promotion.

## V32 direction

Do not spend the next cycle only adding larger entry classifiers. A binary filter cannot create new opportunities and the exact MT5 evidence shows the strongest gate mainly trades return for lower DD.

V32 should move the neural layer to a broader decision role while keeping exact MT5 as the economic judge:

1. keep DeepMLP as a quality/risk signal;
2. test less-destructive keep rates as development-only robustness, not confirmation;
3. add multi-task targets for expected R, MFE, MAE and giveback;
4. research an intra-trade profit-protection / exit controller using causal state, current unrealized R, peak R and time-in-trade;
5. evaluate complementary family routing/allocation rather than duplicate candidate voting;
6. preserve <=1.00% risk per trade and an explicit aggregate-risk cap;
7. final PnL/DD/turnover evidence must again come from MT5 Strategy Tester.

The goal is not to force 15% by leverage. If a new architecture cannot move the exact MT5 economics toward the target at the fixed risk ceiling, reject it.
