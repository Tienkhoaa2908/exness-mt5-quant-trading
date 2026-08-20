# GitHub architecture review for parallel-alpha expansion

Date: 2026-08-20

This review uses external repositories as architectural references, not as evidence that their strategies are profitable. The implementation in this repository is original and causal; no external trading strategy code is vendored by this milestone.

## Microsoft Qlib

Repository: `microsoft/qlib` (MIT).

Useful ideas adopted:

- explicit model/research workflow separation;
- broad model zoo rather than assuming one model class wins;
- regime/adaptation concepts such as TRA/ADARNN;
- repeatable experiment configuration.

Applied here: specialist families remain separate, ML/DL controls are compared chronologically, and the meta-router learns expert/context interactions rather than predicting market direction from scratch.

## Freqtrade / FreqAI

Useful idea adopted: treat look-ahead analysis as a first-class validation problem. Freqtrade's lookahead-analysis specifically tests whether indicators/entries change when future candles are withheld.

Applied here: every feature has an availability timestamp, V34 SMC swing confirmation is delayed until confirmation bars close, and current-bar tapes use causal as-of joins. No Freqtrade GPL strategy code is copied.

## NautilusTrader

Repository license: LGPL-3.0.

Useful ideas adopted:

- deterministic event-driven replay;
- distinguish bars, L1 quotes, trades, L2 and L3 order-book data;
- execution-sensitive claims require more granular data.

Applied here: MT5 remains the Exness execution judge. The new microstructure expert is explicitly labelled an L1/tick-path proxy. If real depth data becomes available, it belongs in a separate order-book lane rather than being fabricated from bars.

## hftbacktest

Repository: `nkaz001/hftbacktest` (MIT).

Useful ideas adopted:

- tick-by-tick replay;
- order-book reconstruction/imbalance as a distinct research domain;
- latency/queue assumptions must be explicit.

Applied here: a future true-orderflow lane will require actual L2/L3 data. Current XAUUSDm research does not claim queue/LOB information.

## FinRL

Useful idea adopted: reinforcement learning is best framed as sequential policy selection. It is not used as a shortcut for discovering alpha on the current small M15 dataset.

Applied here: RL is deferred until specialist actions and a validated simulator/state/action/reward contract exist. A future RL agent may allocate among bounded expert/policy actions, never exceed the 1% stop-risk ceiling, and must return to MT5 for final economics.

## Smart Money Concepts repositories

References include `joshyattridge/smart-money-concepts` (MIT) and MT5 SMC indicator repositories.

Useful concepts: BOS/CHoCH, FVG, order blocks, liquidity and swing structure.

Critical finding: open PRs in the popular Python SMC repository explicitly address look-ahead bias in swing-high/low calculation. Therefore V34 does not import those indicators. It implements a separate causal definition in which a pivot is unusable until its right-side confirmation bars have closed.

## Design consequence

The system is now a layered research stack:

1. causal data + availability timestamps;
2. independent specialist alpha generators;
3. exact-MT5 virtual books for each specialist;
4. AI all-expert router trained on exact outcomes;
5. intra-trade sequence telemetry;
6. GRU/TCN/Transformer diagnostics for policy state;
7. bounded MT5 policy validation;
8. fresh chronological confirmation before PAPER/DEMO.

REAL-MONEY LIVE TRADING remains forbidden.
