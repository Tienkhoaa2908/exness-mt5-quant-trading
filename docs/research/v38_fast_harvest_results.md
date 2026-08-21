# V38 Fast Harvest Lab — exact-MT5 results

Date: 2026-08-21

## Evidence

Uploaded ZIP SHA-256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Run contract:

- branch head at runtime: `54276f9d06eb5998fe25baa286442cfb181e4044`;
- V30 accepted source SHA: `4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`;
- accepted V34 base reproduced SHA: `8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10`;
- V38 deterministic source SHA: `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- V34 specialist tape SHA: `d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863`;
- state1 SHA: `5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`;
- symbol XAUUSDm, M15, 2025-08-01 through 2026-08-01;
- Strategy Tester model 0, deposit USD40, leverage 1:200;
- tester-only, no native/external broker orders, risk ceiling unchanged at <=1.00% per trade.

MetaEditor compile: **0 errors / 0 warnings**.

Integrity:

- 1,104 monthly rows = 12 months x 23 candidates x 4 books;
- 56,321 trade-ledger rows;
- 329,278 M15 telemetry rows;
- 260,471 M1 fast telemetry rows total; continuous-USD40 control has 129,311 M1 rows and covers 563/563 control trades;
- monthly summary vs ledger trade-count mismatch = 0;
- max summary-vs-ledger PnL difference ~9e-6;
- max AvgR difference ~6e-6;
- control reproducibility gate PASS.

## Primary continuous-USD40 comparison

| Candidate | End USD | Geo/month | Max DD | Trades | AvgR | PF | Median hold | Turnover x $40 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **adaptive_ewma_hl8_thr0 control** | **107.43** | **8.58%** | **9.90%** | **563** | **0.215R** | **1.501** | **157.7m** | **3945.8x** |
| fast TP 0.50R | 65.09 | 4.14% | 8.50% | 1,069 | 0.056R | 1.201 | 41.6m | 6358.3x |
| fast TP 0.75R | 90.13 | 7.00% | 9.42% | 880 | 0.109R | 1.325 | 64.9m | 6120.9x |
| **fast TP 1.00R** | **104.42** | **8.32%** | **10.23%** | **750** | **0.158R** | **1.382** | **94.4m** | **5716.7x** |
| giveback 0.25R after 0.75R | 96.65 | 7.63% | 10.11% | 831 | 0.133R | 1.349 | 70.7m | 6251.8x |
| velocity-decay after 0.50R | 83.41 | 6.32% | 9.89% | 979 | 0.087R | 1.319 | 51.4m | 6649.2x |
| timebox 30m | 54.25 | 2.57% | 12.92% | 1,388 | 0.028R | 1.145 | 30.0m | 8165.3x |

No V38 fast arm met the promotion rule. `qualified_fast_harvest_candidates=[]`.

## Interpretation

The user's speed thesis is only partly supported. Time-in-market can be cut sharply, but unconditional harvesting destroys too much right-tail expectancy and increases re-entry/turnover.

The closest arm is fixed TP1R:

- ending capital only ~USD3.01 below control;
- geo/month lower by only ~0.26 percentage point;
- median holding time lower by ~40.2%;
- but max DD is slightly worse (~3.3% relative deterioration);
- trades rise ~33.2%;
- turnover rises ~44.9%;
- PF and AvgR both fall.

This means `+1R` is near a useful decision boundary, but **not** a universal take-profit. The system needs to distinguish ordinary giveback-prone winners from rare/right-tail trend winners.

The 30-minute timebox confirms that pure speed is not the objective: it achieves the highest observed SumR per market-hour (~0.0572R/hour) but collapses total economics to 2.57% geometric/month because long trends are cut too aggressively.

The fixed TP1R arm is regime-sensitive. It beats control in some months (notably 2025-10 and 2026-03) but loses materially in strong right-tail months such as 2026-06 and 2026-07. Therefore the next gate must be conditional/selective rather than another fixed-TP sweep.

## Decision

- Preserve the accepted adaptive baseline unchanged.
- Preserve frozen V32 DeepMLP keep60 evidence.
- Preserve V36 sequence-Transformer evidence.
- Reject unconditional fast TP0.50, TP0.75, TP1.00, fixed giveback, fixed velocity-decay and 30m timebox as production candidates.
- Do not threshold-sweep more fixed TPs on the same 12-month period.
- Use V38 M1/tick telemetry to improve short-horizon state representation, but do not call the current L1/tick-path metrics true order flow.
- Next research gate: **selective harvest after approximately +1R**, where AI/regime state decides whether to harvest or preserve the right tail.

## Next-gate constraint

A selective controller must never increase entry risk or stack independent full-risk same-symbol positions. Exact MT5 remains the economic judge because an early exit changes re-entry timing, adaptive state and subsequent opportunity path.

LIVE remains forbidden.
