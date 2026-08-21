# V41 Baseline Stack + Direct Action-Value — Stage A result

Date: 2026-08-21.

Uploaded V41 ZIP SHA-256: `f7e508816f96cb033f327582013fc0cf3c8583693b820c445de9c7156f469f7f`.

Integrity: ZIP CRC PASS; internal manifest PASS. Official status: **STAGE_A_HOLD**; no promotion lane.

The accepted exact-MT5 control remains `adaptive_ewma_hl8_thr0`, USD40 continuous, $40 -> $107.43 over 12 months, about 8.58% geometric/month.

| Lane | End USD | Geo/month | Shadow max DD | Delta R vs baseline | Positive OOS months |
|---|---:|---:|---:|---:|---:|
| BASELINE | 107.43 | 8.5814% | 9.1277% | 0 | control |
| ENTRY_VALUE | 72.5021 | 5.0810% | 8.0628% | -47.7240R | 2/8 |
| ACTION_VALUE | 88.5091 | 6.8425% | 8.8456% | -23.5606R | 2/7 |
| INTEGRATED_STACK | 69.3499 | 4.6925% | 8.0628% | -53.2225R | 2/8 |

The action controller selected 66 interventions (~21.64% coverage) but lost 23.56R versus baseline exits. Entry and integrated lanes were materially worse.

Decision: close V41 as HOLD; do not take a V41 layer to exact-MT5. Preserve the accepted baseline. Path-dependent baseline changes must be adjudicated directly in MT5 Strategy Tester, which motivates V42 router research.
