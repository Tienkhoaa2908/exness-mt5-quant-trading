# V28 — Event-aware regime deep research

Ngày: 2026-08-18.

## Policy note

V28 was a historical research/data/replay milestone. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V28's no-native-order and 1.00% research-risk contract was phase-specific and is not a permanent prohibition on researching or preparing production/live trading with real capital.

## Mục tiêu

Tìm information gain orthogonal cho XAU mà không tiếp tục nhồi indicator/low-TF noise. Direction vẫn do mechanical family quyết định; ML/DL chỉ dự báo market-range/regime để route/abstain.

## Event-aware range model

Dataset causal M30 + cross-asset + USD high-impact economic-calendar family clocks. Expanding chronological walk-forward, purge 16h.

13 tháng OOS Feb-2025 → Feb-2026, 2h+4h event-aware LightGBM range score đạt mean Spearman khoảng 0.5493; event-aware uplift so với price/cross-asset base nhỏ nhưng dương trên discovery sample.

## Model-family benchmark

Matched 13-month OOS 4h range benchmark showed LightGBM/XGBoost/CatBoost broadly similar, with no robust enough ensemble uplift to justify extra complexity. LightGBM remained the primary research model for simplicity/stability.

## DL screening

Event-aware TCN improved versus its price-only control but remained below LightGBM. PatchTransformer materially underperformed on current sample scale. DL remained a diversity/research lane rather than the V28 primary score.

## Economic-event feature findings

Stable useful variables included hours to next USD high-impact event, event-family clocks, pre-event decays and upcoming event counts. Raw actual/forecast surprise was not useful as a 4h regime input. Macro-surprise directional effects were too sparse for promotion.

## Trade-ledger screening

Joining causal OOS range score to prior MT5 trades suggested family-specific routing rather than a blanket news blackout. The natural low-range quartile was the most defensible screening boundary, but same-sample bands were not production thresholds.

## V28 replay catalog

Only one ML percentile was preregistered into V28 stateful replay: natural low quartile 0.25. Replay used frozen peak-lock exits, four virtual books, independent monthly resets and no native broker orders in V28.

## Fresh calendar gate

Existing calendar coverage ended before the latest price evidence, motivating a narrow USD-only calendar top-up before treating later months as event-aware confirmation.

## Decision

V28 architecture: price/cross-asset + USD event clock -> range-regime score -> family-specific route/abstain -> mechanical direction -> frozen risk/exit.

Do not promote direct Buy/Sell ML ownership, blanket no-news rules, broad optimized percentile grids or a surprise-driven 4h macro head from V28 evidence.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
