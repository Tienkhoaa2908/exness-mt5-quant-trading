# RECOVERY — V31.1 exact MT5 USD40 gate

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`
Historical branch: `agent/v30-ml-dl-feature-lake`

## Policy note

This is a historical V31.1 tester-recovery note. Current project-wide policy is defined by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V31.1 itself had no native/external broker-order path and used a 1.00% research-risk ceiling. Those were V31.1 phase constraints, not a permanent prohibition on researching or preparing later production/live trading with real capital.

Read first:
- `docs/handover/V31_1_READY_TO_RUN.md`
- `docs/research/v31_1_exact_mt5_usd40_model_gate.md`
- `docs/research/v30_18m_feature_lake_acceptance_and_first_ml.md`
- `docs/research/v30_causal_ml_dl_tournament_v2.md`

Accepted V30 source SHA-256:
`4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05`

V31.1 deterministic generated source SHA-256:
`45ace4bd7465dbfb8a1b5670b67d372643b1eea057b1d7a44d80b91caf2b7c3e`

Starting adaptive state SHA-256:
`39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76`

Corrected current-bar causal model tape reference SHA-256:
`0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f`

Do not reuse the older V31 tape keyed simply by `bar_features.time + 15m`; V31.1 keys the tape to actual MT5 current-bar starts and selects the latest feature row with `feature_available_time <= current_bar_start`.

The V31.1 USD40 target book is continuous across months and is named `usd40_r1p0_cent_continuous`. It starts once at USD40 and risks 1.00% of current balance. Month-end liquidation remains enabled. Full-period peak/max-MTM-DD state is carried month-to-month.

Exact test period: 2026-02-01 -> 2026-08-01, XAUUSDm M15, MT5 tester Deposit=40 USD, leverage assumption 1:200.

Modes: baseline, CatBoost, ExtraTrees, DeepMLP 64-32-16, LinearSVM, CatBoost+ExtraTrees, majority 2-of-4. Every mode restores the same adaptive state before testing.

Historical run entrypoint:
`runtime/v31_mt5_model_gate/BOOTSTRAP_V31_ONE_SHOT_GIT_BASH.sh`

The runner has per-mode checkpoints. If a later collection/analysis step fails after a mode completed and was collected, rerun the same bootstrap; completed mode checkpoints are reused. Do not manually advance/modify adaptive state.

Decision evidence comes from exact MT5 `monthly_summary.csv`/`trades.csv`. Primary same-candidate comparison is `adaptive_ewma_hl8_thr0`. Do not promote based on AUC, Python PnL reconstruction, or best-candidate cherry-picking.

Current live-trading research/deployment intent is governed by ADR-049 and later V49 evidence, not by this historical V31.1 tester note.
