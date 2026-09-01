# Exness / MetaTrader 5 Quant Trading System

Current project focus: frozen V69 LONG on `XAUUSDm M15`, short live-market DEMO smoke
validation, broker/runtime health verification, then review before any later real-money
deployment decision.

## Current branch

`agent/v69-one-shot-prospective-demo`

Always fetch the current remote HEAD. Do not recover from stale `main` or old V54/V55
handover text.

## Current safety boundary

- LONG only;
- fixed lot `0.01`;
- DEMO only;
- SHORT disabled/rejected;
- REAL authorization false;
- no automatic REAL promotion;
- no Martingale, uncontrolled grid or doubling after loss.

## Frozen research anchor

V69 research HEAD:

`0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted V69 evidence ZIP SHA256:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256:

`0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

V69 LONG development replay: 24 trades, 10W/14L, `+$7.14`, PF `1.462`, max realized
DD `$3.34`. This replay is development evidence, not an untouched independent holdout.

## Current live DEMO smoke

Canonical launcher:

`bash runtime/v69_one_shot_prospective_demo/START_V69_ONE_SHOT_PROSPECTIVE_DEMO_GIT_BASH.sh`

The MT5 chart dashboard must visibly show system health, broker preflight, runtime ticks,
PnL, positions, closed trades, recent trade details, progress and output status.

Current quick-review horizon is deliberately short: two naturally closed V69 strategy
trades or a 48-hour hard cap. This step primarily verifies real runtime/execution behavior
and adds only a small forward economic sample.

Latest broker log proved that lot `0.01` is broker-valid (`min=0.01`, `step=0.01`) but the
first dry-run `OrderCheck()` returned generic local error 4756. The first implementation
then incorrectly failed before a second independent broker check could occur. The active
branch now adds stateful repeated broker-health checks and complete local/server
retcode/comment diagnostics. See the canonical handover documents.

## Read first

1. `docs/handover/OPERATING_PROTOCOL.md`
2. `docs/handover/CURRENT_STATE.md`
3. `docs/handover/KNOWN_FAILURES.md`
4. `docs/handover/TURN_SYNC.md`
5. `docs/handover/RECOVERY_PROMPT.md`
6. `docs/handover/STATE_SYNC_PROMPT.md`

Historical ADRs/research reports remain provenance. Superseded per-version recovery-state
documents are intentionally removed to prevent recovery ambiguity.
