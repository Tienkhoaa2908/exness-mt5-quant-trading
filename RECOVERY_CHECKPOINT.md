# Recovery Checkpoint — V69 Frozen Forward DEMO Smoke

Updated: 2026-09-01 (+07)

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

Active branch: `agent/v69-one-shot-prospective-demo`

Always fetch the current remote HEAD; do not hardcode an old chat SHA as current state.

Canonical recovery path:

1. `docs/handover/OPERATING_PROTOCOL.md`
2. `docs/handover/CURRENT_STATE.md`
3. `docs/handover/KNOWN_FAILURES.md`
4. `docs/handover/TURN_SYNC.md`
5. `docs/handover/RECOVERY_PROMPT.md`

Frozen V69 research HEAD:

`0569701be7846605ac01f94d8b5fc4ec2a6f8dd1`

Accepted V69 evidence ZIP SHA256:

`e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb`

Frozen forward parent source SHA256:

`0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93`

Current forward contract:

- XAUUSDm M15;
- LONG only;
- fixed lot 0.01;
- DEMO only;
- SHORT disabled;
- REAL authorization false;
- two natural closed strategy trades or 48-hour smoke-review cap.

Latest Windows finding: broker volume contract validates lot 0.01 (`min=0.01`,
`step=0.01`, `max=200`), but the first dry-run OrderCheck returned generic local error
4756. The first broker-ready runner incorrectly failed after 12 seconds while its EA
broker check refreshed only every 30 seconds, so one startup sample could be treated as a
permanent blocker.

The active branch now uses a visible `SYSTEM HEALTH` layer, 5-second independent broker
checks, two consecutive READY confirmations, account/EA permissions, connection/symbol
synchronization checks, execution-mode-aware request construction and complete local plus
server retcode/comment telemetry.

Current gate:

`V69_BROKER_HEALTH_FIX=IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_WINDOWS_RERUN`

Do not authorize REAL money from this checkpoint.
