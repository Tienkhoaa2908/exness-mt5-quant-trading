# CURRENT STATE — Exness / MetaTrader 5 Quant Trading System

Ngày cập nhật: 2026-08-17.

## Safety invariant

REAL-MONEY LIVE TRADING = FORBIDDEN.

Không Martingale, uncontrolled grid, doubling after loss. Stop-risk research ceiling 1.00%/trade. Virtual lab/ML prediction không được deploy trực tiếp.

## Latest completed runtime — V25 ML Regime Replay Lab V1

Output ZIP SHA-256: `baff90eccfaac70abaa15b30d6132c535160e2b8ab96b65fd290cba968754078`.

Evidence:
- internal SHA-256 manifest 21/21 PASS;
- MetaEditor 0 errors / 0 warnings;
- two chunks, 12 monthly resets Aug-2025 → Jul-2026;
- 12 candidates × 4 books = 576 monthly rows;
- 17,635 executed virtual trades;
- frozen OOF ML score SHA-256 `5d8a6cc45074833a60d7e82b6a56f7ae72a9f4e0153b623cc439756751b16c91`;
- fold manifest SHA-256 `ed26b87484e1c4782614c64294520bc7fb3e6728c10f08fa77c8fe2d097739a7`;
- tester-only, native/external broker orders = 0.

## V25 strategy result — USD40 @ 1%

EMA base remains the highest median-return control on the 12-month OOF replay:
- median +5.8576%/month;
- mean +4.7476%;
- positive 8/12;
- max MTM DD 8.7792%;
- mean AvgR ~0.1594;
- median turnover ~138.10x.

Strongest ML efficiency candidate: `ml_switch_ema_bos8_p75`:
- median +5.6288%;
- mean +4.9954%;
- positive 10/12;
- max MTM DD 7.3121%;
- mean AvgR ~0.1942;
- median turnover ~112.99x.

Versus EMA base: +2 positive months, max DD ~16.7% lower, AvgR ~21.8% higher, turnover ~18.2% lower, but median return ~0.23 percentage points lower. Paired monthly return uplift is statistically inconclusive.

`ml_ema_skip20_low75` validates ML abstention/quality filtering: versus `ema_h1_skip20`, max DD drops ~21.8%, AvgR rises ~22.5%, turnover drops ~29.8%, while mean return is only ~0.20 points lower. Exact-entry matching shows the ML gate removes a large near-zero-expectancy EMA subset.

## ML/DL interpretation

Direct Buy/Sell prediction remains weak. The reliable ML target is future market-range / volatility regime, used only for routing or abstention.

V25 confirms that the OOF range score has trading information, but mainly as a **quality/efficiency filter**, not yet as a robust return amplifier.

p67 multi-family routing is rejected. `ml_switch_ema_multi_p67` materially worsens tail risk, drawdown and turnover.

Post-hoc diagnostics indicate EMA deterioration concentrates in extreme predicted-range states, especially with high predicted volatility, while breakout/BOS continuation strengthens mainly in the extreme-high regime. These thresholds are discovery only and must not be promoted on the same sample.

## Forward gate

Do not claim a newly tuned V25 threshold as confirmed alpha. Any further threshold refinement is screening only and must be frozen before untouched forward evaluation.

Aug-2026 is the earliest candidate forward period not used to select V25 routing thresholds. Full analysis: `docs/research/2026-08-17_v25_ml_regime_replay_analysis.md`.

GitHub remains a milestone checkpoint; do not merge research branches into `main` until the corresponding validation gate is satisfied.
