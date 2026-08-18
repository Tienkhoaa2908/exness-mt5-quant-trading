# V28 — Event-aware regime deep research

Ngày: 2026-08-18.

## Safety
REAL-MONEY LIVE TRADING = FORBIDDEN. Không native broker orders. Stop-risk research ceiling 1.00%/trade.

## Mục tiêu
Tìm information gain orthogonal cho XAU mà không tiếp tục nhồi indicator/low-TF noise. Direction vẫn do mechanical family quyết định; ML/DL chỉ dự báo market-range/regime để route/abstain.

## Event-aware range model
Dataset causal M30 + cross-asset + USD high-impact economic-calendar family clocks. Expanding chronological walk-forward, purge 16h.

13 tháng OOS Feb-2025 → Feb-2026, 2h+4h event-aware LightGBM range score:
- mean Spearman ~0.5493;
- 13/13 tháng dương;
- worst month ~0.3827.

Paired event vs price/cross-asset base over the same 13 months:
- base mean ~0.5376;
- event-aware mean ~0.5497;
- mean uplift +0.01210;
- event beats base 10/13 months;
- paired monthly bootstrap 95% CI ~[+0.00455,+0.01923];
- bootstrap P(mean uplift <=0) ~0.001;
- one-sided sign test ~0.046.

Horizon uplift is strongest around the strategy-relevant window:
- 1h: +~0.0098 Spearman;
- 2h: +~0.0137;
- 4h: +~0.0294;
- 8h: +~0.0227;
- 12h: +~0.0214.

## Model-family benchmark
Matched 13-month OOS 4h range benchmark on the event-aware feature set:
- LightGBM mean Spearman ~0.5534, min ~0.4020;
- XGBoost ~0.5521, min ~0.3741;
- CatBoost ~0.5470, min ~0.3631.

Rank ensemble LGB+XGB reaches ~0.5577 mean but paired uplift vs LGB is not robust enough (bootstrap CI crosses zero). Keep LightGBM as primary for simplicity/stability.

## DL screening
- Event-aware TCN improves over its price-only TCN but remains below LightGBM in forward months.
- PatchTransformer materially underperforms on the current sample scale.
- A small DL rank blend gives only a marginal same-sample uplift and is not promoted.

Decision: do not increase DL capacity blindly. Sequence DL remains a diversity/research lane, not the V28 primary score.

## Economic-event feature findings
Stable useful variables include:
- hours to next USD high-impact event;
- labor/monetary/inflation/survey family clocks;
- pre-event decays;
- next event cluster size;
- upcoming high-impact counts.

Raw actual/forecast surprise is not useful as a 4h regime input. A separate causal macro-surprise event study shows short post-release directional impulse for selected US growth/labor events, concentrated mainly in the first 15–60 minutes. Sample sizes per event code are too small to promote this micro-layer yet.

## Trade-ledger screening
Joining causal OOS score to prior MT5 trades shows the natural low-range quartile is the most defensible routing boundary.

EMA skip20 when score <25th percentile:
- early partition: 39 trades, AvgR ~-0.0365;
- later partition: 35 trades, AvgR ~-0.0056.

EMA skip20 when score >=25th percentile:
- early partition AvgR ~+0.184;
- later partition AvgR ~+0.362.

MACD H1 gap10 remains positive in the low quartile in both partitions:
- early ~+0.662R;
- later ~+0.286R.

BOS gap8 is less stable in the early low-quartile sample but positive later. Broad five-band hard family selection overfits discovery→validation and is rejected.

EMA late-session pathology remains independently robust; keep skip-from-hour-20 control.

## V28 replay catalog — pre-registered
Only one ML percentile is promoted into stateful MT5 replay: natural low quartile 0.25.

Controls:
1. ema_h1_base
2. ema_h1_skip20
3. router_ema_bos8
4. router_ema_macd10
5. macd_h1_gap10
6. bos_fvg_h1_gap8

Event routes:
7. event_ema_skip20_low25_veto
8. event_low25_macd10_else_ema
9. event_low25_bos8_else_ema
10. event_low25_macd10_else_ema_bos8

Replay uses frozen peak-lock exit, four virtual books, 13 independent monthly resets, no native orders. The score is an OOF 2h+4h event-aware LightGBM range percentile.

## Fresh calendar gate
Existing recovered calendar ends around 2026-03-10 for USD while V26 price data extends into Aug-2026. A lightweight USD-only calendar top-up from 2026-03-01 onward is therefore the highest-leverage next data action. It should be completed before treating Mar-Jul as fresh event-aware confirmation.

## Decision
V28 architecture: price/cross-asset + USD event clock -> range-regime score -> family-specific route/abstain -> mechanical direction -> frozen risk/exit.

Do not promote a direct Buy/Sell ML head, a blanket no-news rule, broad optimized percentile grids, or a surprise-driven 4h macro head.