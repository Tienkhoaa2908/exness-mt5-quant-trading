# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-01 21:56 (+07)

## User request

User said: `rồi ok đưa code sửa cái kia đi` — provide the corrected one-shot command/code for the broker-health/runtime issue so the Windows DEMO smoke can be rerun.

## Mandatory pre-work state read

Resolved active remote branch and read:

- `docs/handover/OPERATING_PROTOCOL.md`;
- `docs/handover/CURRENT_STATE.md`;
- `docs/handover/KNOWN_FAILURES.md`;
- previous `docs/handover/TURN_SYNC.md`;
- exact-HEAD GitHub Actions;
- `RUN_V69_ONE_SHOT_BROKER_READY_DEMO.py`;
- `build_v69_frozen_forward_demo_broker_ready_dashboard_source.py`;
- canonical Git Bash launcher.

## CI investigation this turn

Starting remote HEAD was `34b755657968cba1c16483de13aef7b0c1255d13`.

On that head, all actual V69 broker-ready/static Python tests passed, but `v69-forward-quality` failed at the shell `Dashboard strategy isolation contract`. The failure was a stale workflow assertion: CI still expected old broker wording after runtime semantics had changed to stable multi-check health.

First CI alignment commit: `0fcdaf931a49033488d48ead785527cc8cc78bb7`.

That run still failed the same shell-contract step. Inspection showed a second stale literal: workflow expected `BROKER: READY`, while the current builder intentionally renders `BROKER PREFLIGHT: READY` plus `SYSTEM HEALTH:`.

Second CI alignment commit: `9c2161b937bd7c16e1293c1de295181d18b419df`.

`v69-forward-quality` run `33522581398` on `9c2161b...` completed **SUCCESS**. Its frozen-forward source tests, dashboard tests, broker-ready smoke tests, parent regressions, trade-quality tests, runtime-isolation tests and prospective one-shot tests all passed.

This was CI contract maintenance only. No V69 entry/exit/risk/order-send semantics were changed.

## Runtime health implementation being handed to operator

Current broker-health layer:

- refreshes every 5 seconds;
- counts independent checks via `broker_check_seq`;
- requires two consecutive independent READY checks;
- confirms deterministic fatal states on repeated independent checks;
- allows transient failures, including bare local 4756/no server detail, to stabilize for up to 90 seconds;
- records account/terminal/symbol permissions and local + server OrderCheck diagnostics;
- shows `SYSTEM HEALTH: STARTING / READY / BLOCKED` and `BROKER PREFLIGHT` on chart;
- distinguishes awaiting first natural fill from `EXECUTION VERIFIED`;
- does not add a broker order-send path to the preflight layer.

## Safety status

Unchanged:

- XAUUSDm M15;
- LONG only;
- fixed lot 0.01;
- DEMO only;
- SHORT disabled/rejected;
- REAL authorization false.

## State-sync action

This turn updates canonical `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` together after the successful code/CI checkpoint. The resulting exact remote HEAD must receive a final relevant CI verification before the user is instructed to run it.

## Next operator action

Once `v69-forward-quality` is green on the exact post-sync HEAD:

1. close MT5 and MetaEditor;
2. ensure local repo worktree is clean (do not `git clean`, do not `stash pop`);
3. fetch and fast-forward/checkout the exact active branch HEAD;
4. export `V69_ONE_SHOT_EXPECTED_HEAD` to that exact SHA;
5. run the canonical one-shot launcher once;
6. require MetaEditor `0 errors, 0 warnings` and two stable broker READY checks;
7. if blocked, return the `V69_HEALTH_CHECK=` lines or chart screenshot so local error + server retcode/comment can be diagnosed directly.
