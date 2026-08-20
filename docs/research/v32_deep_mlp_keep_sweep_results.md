# V32 DeepMLP keep-rate exact-MT5 results

Date: 2026-08-20.

Uploaded evidence ZIP SHA-256: `3b077c3b7fffb4f44393edee8d0364feb2c8a37cab7993b68b0a5d467d8ce4a8`.

Six complete Strategy Tester passes are accepted: baseline and DeepMLP keep50/60/70/80/90. All compile 0 errors / 0 warnings, MT5 rc=0, and manifests record tester-only virtual research with no native/external broker orders. Source SHA is `ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a`; causal tape SHA is `8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356` and matches the pinned reference.

Primary candidate remains `adaptive_ewma_hl8_thr0`.

| Mode | End USD | Geo/month | Max DD | Trades | AvgR | PF | Turnover/$40 |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 62.3573 | 7.6807% | 10.8159% | 222 | 0.2401R | 1.5579 | 1045.67x |
| keep60 | 62.1444 | 7.6193% | 7.3639% | 153 | 0.3250R | 1.8326 | 764.42x |
| keep80 | 60.9896 | 7.2834% | 9.9301% | 191 | 0.2502R | 1.6374 | 883.29x |
| keep70 | 60.9569 | 7.2738% | 9.0562% | 179 | 0.2695R | 1.6670 | 857.14x |
| keep50 | 60.4393 | 7.1215% | 7.3551% | 146 | 0.3329R | 1.8037 | 728.65x |
| keep90 | 53.2804 | 4.8942% | 16.3281% | 210 | 0.1699R | 1.3828 | 840.60x |

keep60 is the bounded development winner for the preregistered primary lane. It ends only ~0.34% below baseline while reducing max DD ~31.9%, trade count ~31.1%, and turnover ~26.9%; AvgR rises ~35.4% and PF ~17.6%. It still does not meet the aspirational 15% monthly target.

The nested score masks do not create nested realized trade sets because gating changes the later adaptive/one-position state path. This is why exact MT5 replay remains mandatory.

Exploratory only: `adaptive_ewma_hl12_thr0p05 + keep80` ends at USD66.6393, 8.8792% geometric/month, max DD 7.0573%, AvgR 0.3128R and PF 1.8086. It is not primary evidence because candidate and threshold were selected after observing the same six months.

Decision: freeze keep60 for a future fresh chronological holdout; do not tune the primary keep rate again on February-July 2026. Further development should move the neural signal toward source/regime-conditioned policy control and complementary opportunity generation while keeping exact MT5 as the economic judge.