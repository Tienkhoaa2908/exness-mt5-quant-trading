# ADR-060 — V58 fixed-0.01 pullback / fast-trend / spread-cost research

Status: Accepted for tester-only research.

## Context

V57 reproduced the selected candidate on XAUUSDm M15 for 2026-08-24..2026-08-28 with a mandatory fixed lot of 0.01. The V57 evidence ZIP SHA256 is
`c6f3eaeb2c6da585589ab71265eaee236d13eefea54aed9dc8ef84cd8c146bde`.

V57 produced 9 selected-candidate entries, 4 wins and 5 losses. The 0.01 shadow result was
`-$45.39595`, PF `0.619458`. H1 trend and the balanced SMC score did not filter any of the nine entries. ADX and structure gates were worse on the same week. Broker-simulation requests were zero even when `allow_balanced=1`; the event stream showed `spread_guard` and `stale_strategy_state`, but the point-based spread telemetry was deduplicated and insufficient to diagnose each entry.

A post-hoc observation on this one week is that refusing LONG entries with RSI2 above 80 (and symmetrically refusing SHORT entries with RSI2 below 20) leaves four shadow trades, 3 wins / 1 loss, +$34.894 at 0.01. This observation is explicitly exploratory and must not be treated as validated alpha.

## Decision

V58 is a tester-only diagnostic/research milestone. It does not promote to DEMO or REAL deployment.

V58 keeps:
- selected candidate `v52_b4_or_b3_trend_bos`;
- XAUUSDm M15;
- fixed lot `0.01`;
- accepted week-start adaptive state SHA256 `7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259`;
- one MT5 Strategy Tester pass using Model=4 real ticks for 2026-08-24..2026-08-29.

V58 adds:
1. An actual tester gate `pullback80`:
   - LONG requires RSI2 <= 80;
   - SHORT requires RSI2 >= 20.
2. Shadow gates for RSI2<=70 / >=30, no-opposite-SMC veto, H1 EMA20/EMA50 fast trend, and M15 EMA20/EMA50 fast trend.
3. Fast trend uses only closed bars through `CopyRates(..., start_pos=1, ...)`, preserving causal availability.
4. The old fixed `InpV55MaxSpreadPoints` entry refusal is replaced in V58 only by a cost-aware test:
   - spread cash is calculated at 0.01 lot with `OrderCalcProfit`;
   - allowed spread cost is `min($0.75, 5% of planned stop-risk cash)`;
   - every spread block is explicitly logged.
5. Fixed-lot margin feasibility uses a tester-only 95% free-margin ceiling. This does not change the mandatory 0.01 lot and does not imply production safety.
6. Every actual order attempt logs risk cash, risk percent, required margin, equity, spread points and spread cash.
7. Output reports both shadow gate PnL and actual MT5 broker-simulation PnL.

## Research interpretation

The same-week pullback80 result is a hypothesis generated from V57 evidence. It is not eligible for production promotion from this week alone. V58 exists to:
- verify that 0.01 orders can traverse the broker simulation path;
- quantify the actual spread blocker;
- test whether a simple anti-chase condition improves the observed week;
- collect fast-trend and SMC telemetry for later out-of-sample validation.

No claim of guaranteed profitability is made. Fixed 0.01 on a USD 40 account can expose a very large fraction of equity to one stop. V58 records that exposure rather than hiding it.

## External implementation references

Public SMC implementations such as `joshyattridge/smart-money-concepts` were used only as definition/architecture references for FVG, swing structure and BOS/CHoCH concepts. V58 does not copy their implementation. In particular, pivot/swing definitions that use future bars are not consumed before their confirmation time.

`GeneralTradingSarl/Smart-Money-Concepts` was also reviewed as an MQL5 ecosystem reference, but its compiled EX5 is not imported or executed by this project.

## Evidence boundary

Linux CI can validate Python syntax, static contracts, policy checks, secret scan, launcher shell syntax and analyzer regressions. Only the user's Windows MT5/MetaEditor can establish:
- MQL compile `0 errors, 0 warnings`;
- Strategy Tester Model=4 execution;
- 0.01 simulated order requests/deals;
- final V58 PnL and evidence ZIP.
