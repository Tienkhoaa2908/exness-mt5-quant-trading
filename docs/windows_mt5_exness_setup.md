# Windows MT5 / Exness — current research workflow

- Broker research environment: Exness Technologies Ltd.
- Symbol: `XAUUSDm`.
- Main timeframe: M15.
- REAL-MONEY LIVE TRADING = FORBIDDEN.
- Exact-MT5 uses `Every tick based on real ticks` only when an exact gate is explicitly promoted.

## Current milestone — V40 Upgrade Campaign Stage A

V40 Stage A is offline/read-only. It does not launch MT5 or MetaEditor.

Canonical branch:
`agent/v40-upgrade-campaign`

One-shot bootstrap:
`runtime/v40_upgrade_campaign/BOOTSTRAP_V40_UPGRADE_CAMPAIGN_ONE_SHOT_GIT_BASH.sh`

The bootstrap:

1. fetches the branch with an explicit refspec;
2. resets the local branch without `git clean`;
3. preserves untracked accepted V36/V38 evidence and `.venv`;
4. runs compile/static tests/secret scan;
5. verifies/reuses accepted V38 evidence;
6. reuses V36 predictions or recomputes them offline if missing;
7. runs the V40 first-passage research campaign;
8. builds and verifies one ZIP.

V40 runner environment/data-schema rules:

- canonical entry `scripts/v40_upgrade_campaign_stage_a.py` delegates the frozen research logic to `scripts/v40_upgrade_campaign_stage_a_core.py` and packages that core into the evidence output;
- accepted V38 `trades.csv` may already contain `signal_sources`; V40 preserves it and uses M15 only as fallback, avoiding pandas `_x/_y` suffix collisions;
- the dependency-free static suite includes the exact duplicate-column regression case;
- pytest is optional; dependency-free static fallback is mandatory if pytest is absent;
- secret scan targets tracked repository source/config only;
- V36 environment repair probes numpy/pandas/torch/sklearn/scipy and reuses installed packages;
- no package or runner action is allowed to launch MT5 in V40 Stage A.

## Output

Upload only:

`runtime/v40_upgrade_campaign/OUTPUT_V40_STAGE_A/v40_upgrade_campaign_stage_a.zip`

Do not upload screenshots if the ZIP is complete.

The ZIP reports:

- exact accepted baseline $40 -> $107.43, 8.58% geometric/month, DD 9.90%;
- V40 calibrated shadow economics for protective actions;
- 15%/month aspirational target;
- first-passage model metrics;
- monthly/action/segment/V36 calibration diagnostics.

Shadow economics are not exact-MT5 PnL.

## Future exact-MT5 gate

Only a preregistered V40 Stage-A PASS may advance to a frozen exact-MT5 Stage B. Stage B must preserve baseline entries/router/initial risk and verify tick/history coverage again.

Do not switch to manual/live orders to debug research failures. Research stop-risk remains <=1.00%/trade.
