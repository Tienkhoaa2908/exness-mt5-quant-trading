# V42 Baseline Router Upgrade — exact MT5 results

Date: 2026-08-21
Status: **HOLD**

## Integrity / provenance

Successful exact run reused verified compiled V42 source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e` with compiler `Result: 0 errors, 0 warnings`.

Accepted V38 parent ZIP SHA: `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.
Accepted V38 parent source SHA: `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

User-supplied RAR of completed output SHA256: `3cd562b7b3f636b8ba88ce42765f1d38574f9d680c50b272e87d9e05f0697910`.
Internal completed bundle manifest: 18/18 hashes verified.

## Exact control

`adaptive_ewma_hl8_thr0`

- start: $40.00
- end: $107.432645
- total return: +168.5816%
- geometric/month: 8.58163%
- max DD: 9.9038%
- trades: 563
- positive months: 11/12
- AvgR: 0.214608R
- sum R: 120.82439R
- PF: 1.500756
- median hold: 157.7 minutes

## Historical exact router comparators

| Candidate | End USD | Geo/month | DD | Trades | PF |
|---|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0p05 | 111.285257 | 8.900900% | 10.4368% | 531 | 1.521009 |
| adaptive_ewma_hl10_thr0p05 | 110.025682 | 8.797648% | 9.8587% | 537 | 1.530107 |
| adaptive_ewma_hl12_thr0p05 | 107.797276 | 8.612293% | 9.9432% | 553 | 1.515554 |
| adaptive_cp_fast5_slow20_thr0p30 | 102.206843 | 8.131360% | 11.3766% | 566 | 1.463257 |

These are informative but do not satisfy the V42 material-uplift gate.

## V42 challengers

| Candidate | End USD | Geo/month | DD | Trades | AvgR | PF |
|---|---:|---:|---:|---:|---:|---:|
| v42_hl8_switch15m | 100.177653 | 7.950810% | 8.8856% | 490 | 0.240368R | 1.508428 |
| v42_hl8_switch30m | 101.152097 | 8.037927% | 8.8014% | 489 | 0.243236R | 1.519914 |
| v42_hl8_thr0p05_switch15m | 103.358584 | 8.232381% | 7.9188% | 465 | 0.266639R | 1.538075 |
| v42_hl10_thr0p05_switch15m | 102.758796 | 8.179902% | 8.7684% | 467 | 0.260573R | 1.551362 |
| v42_hl12_thr0p05_switch15m | 99.887992 | 7.924764% | 8.7330% | 485 | 0.233877R | 1.521394 |
| v42_cp_fast5_slow20_switch15m | 106.387574 | 8.493214% | 9.6614% | 507 | 0.243553R | 1.534444 |

Best V42 ending equity is `v42_cp_fast5_slow20_switch15m`, but it still ends $1.045071 below control and loses 0.08842pp/month. It beats control in only 6/12 months.

`eligible_to_freeze_for_fresh_holdout=[]`.

## Interpretation

Direction-switch hysteresis does improve trade selectivity: most V42 arms have fewer trades, higher AvgR/PF and lower DD than control. But the participation cost is too high and the right-tail/monthly compounding loss dominates.

The clearest efficiency arm is `v42_hl8_thr0p05_switch15m`: DD falls to 7.9188%, AvgR rises to 0.266639R and PF to 1.538075, but geometric return falls to 8.232381%/month. This is not a return upgrade.

The historical `adaptive_ewma_hl8_thr0p05` and `adaptive_ewma_hl10_thr0p05` remain the more interesting baseline hypotheses because they modestly improve exact ending equity without the broad participation loss caused by switch hysteresis. They still lack the preregistered material uplift required for promotion.

## Packaging incident

MT5 and analysis completed. ZIP packaging failed after analysis because MSYS `sha256sum` emitted `<hash> *filename`, while an inline Python parser assumed `<hash><two spaces>filename`. All completed evidence existed and verified.

Portable packaging is now handled by `scripts/package_research_bundle_portable.py`; completed V42 output can be packaged without rerunning MT5 via `runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh`.

## Decision

V42 = **HOLD**. Keep `adaptive_ewma_hl8_thr0` as the return control. Do not sweep switch delays on this sample. Future baseline work should investigate credit/threshold allocation around the exact HL8/HL10 thresholded variants and explicitly preserve participation/right-tail contribution.
