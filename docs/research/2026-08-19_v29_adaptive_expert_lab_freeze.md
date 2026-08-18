# V29 Adaptive Expert Lab — frozen pre-runtime gate

Ngày: 2026-08-19.

## Scope
V29 replaces the rejected fixed `range percentile -> family` rule with causal shadow-expert tracking. No new user data/exporter is required.

## Frozen catalog
12 candidates × 4 virtual books × 18 independent monthly accounting resets (Feb-2025 → Jul-2026):
- controls: `ema_h1_skip20`, `macd_h1_gap10`, `bos_fvg_h1_gap8`, `trend20_h1_gap5`, `router_ema_bos8`;
- orthogonal controls: `slow_mom_16h24h_timebox8h`, `slow_mom_16h24h_peaklock_timebox8h`;
- adaptive: `adaptive_ewma_hl8_thr0`, `adaptive_ewma_hl8_thr0p05`, `adaptive_ewma_hl10_thr0p05`, `adaptive_ewma_hl12_thr0p05`, `adaptive_cp_fast5_slow20_thr0p30`.

Slow momentum: decisions only server 00:00/08:00, 16h+24h trailing-return direction agreement, enter next M15 bar, 8h maximum hold, 2ATR stop, TP4R. Both no-peak-lock and peak-lock controls are retained.

Adaptive shadow experts: EMA skip20, MACD gap10, BOS/FVG gap8, Trend gap5, slow momentum. Only normalized control-book realized R updates the causal EWMA scores. Half-lives 8/10/12 are bounded robustness probes. The CP probe uses fast5-vs-slow20 score divergence >=0.30R to choose faster adaptation; it does not own Buy/Sell direction.

## Stateful runner contract
- three sequential 6-month Strategy Tester chunks;
- monthly PnL/risk accounting resets remain independent;
- adaptive expert score state carries across chunk boundaries;
- each retry restores the exact pre-chunk adaptive state;
- checkpoint reuse is allowed only when the source/template/chunk fingerprint matches and an `adaptive_state_after.csv` snapshot exists;
- bar-feature export is disabled to reduce runtime; monthly summary + trade ledger remain enabled.

## Static QA
- pytest 11/11 PASS;
- Python analyzer py_compile PASS;
- MQL/PowerShell delimiter balance PASS;
- summary header/row field-count check PASS;
- all `FileWrite` calls remain within MQL5 63-parameter limit;
- executable safety scan PASS: no OrderSend/order_send/CTrade/AllowLiveTrading=1.

One-click release SHA-256: `674ba949fab5d649382401873f4ccbfbafc920872a30cde2e2cf0ef9b61ef82c`.
Internal kit manifest: 15/15 PASS. ZIP integrity PASS.

Windows MetaEditor/runtime is NOT yet claimed. The next and only user action is one V29 Strategy Tester batch. If it passes the research gates, the next endpoint is PAPER/DEMO forward validation; REAL-MONEY LIVE TRADING remains forbidden.
