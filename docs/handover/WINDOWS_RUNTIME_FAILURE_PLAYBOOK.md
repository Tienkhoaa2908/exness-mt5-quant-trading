# Windows / MT5 Runtime Failure Playbook

Updated: 2026-09-01

Mandatory context before changing any Windows runner or MT5 dashboard.

## Core recovery ladder

`provenance -> source -> compile -> MT5 startup -> runtime health -> broker health -> natural execution -> collection -> analysis -> packaging`

Resume only the failed layer. Do not rerun historical MT5 when only runtime UI,
collection, analysis or packaging failed.

## Current V69 health contract

A running MT5 process is not proof that the EA is healthy.

Current V69 dashboard must expose:

- DEMO/REAL mode;
- REAL authorization;
- symbol/timeframe;
- live tick heartbeat;
- terminal/account/EA trading permissions;
- symbol synchronization;
- lot min/max/step compatibility;
- symbol trade/filling/execution mode;
- local `OrderCheck` error;
- server `MqlTradeCheckResult.retcode/comment`;
- overall `SYSTEM HEALTH: STARTING / READY / BLOCKED`;
- actual execution state (`awaiting first natural fill` vs `EXECUTION VERIFIED`).

`SYSTEM HEALTH=READY` requires stable repeated broker/runtime checks, not merely an
attached EA.

## Incident — generic OrderCheck 4756 misclassified from one startup sample

Observed 2026-09-01:

- fixed lot 0.01;
- broker min 0.01;
- broker step 0.01;
- broker max 200;
- symbol trade mode 4;
- filling flags 3;
- first `OrderCheck()` returned false;
- local error 4756 (`ERR_TRADE_SEND_FAILED`).

This proves the incident was not a min-lot failure.

The broken harness refreshed its broker check every 30 seconds while the Python runner
failed after only 12 seconds with an unchanged detail. It could therefore make a
permanent decision from the first check without ever performing a second one.

Do-not-repeat rules:

- publish a broker-check sequence number;
- count only independent checks;
- refresh quickly enough for the runner's stabilization horizon;
- require multiple consecutive READY checks;
- require repeated confirmation before deterministic BLOCKED classification;
- treat a bare generic 4756 as transient initially;
- capture `chk.retcode` and `chk.comment` even when `OrderCheck()` returns false;
- check `ACCOUNT_TRADE_ALLOWED` and `ACCOUNT_TRADE_EXPERT` separately;
- check `TERMINAL_CONNECTED` and symbol synchronization;
- construct the dry-run request according to `SYMBOL_TRADE_EXEMODE`.

## Incident — generated dashboard stale hash pin

A valid deterministic builder output changed after a dashboard fix but the runner still
contained an older generated-source hash. The runner failed although the generated source
was correct.

Rule: freeze true parent strategy identity, but do not duplicate ephemeral generated UI
hashes across builder, runner and workflow. Use A/B deterministic generation + exact
compile/install byte verification.

## Incident — unsupported `LongToString`

MetaEditor rejected dashboard code that Python static tests did not catch.

Rule: generated MQL source must have compile-API regression tests. Use
`IntegerToString(long)` for long values and check `OrderCalcProfit` return values.

## Incident — broken `py.exe -3`

Executable discovery is not enough. Probe the candidate by actually running it and
require Python 3.10+. Print rejected candidates and select only an executable that passes
the probe.

## Incident — background Terminal/console flashes

Periodic `tasklist.exe` and notification PowerShell children can create visible windows.

Rule: use `pythonw.exe`, `CREATE_NO_WINDOW`, hidden PowerShell and redirected standard
handles for background helpers. CI/static tests must guard this.

## Incident — zero forward telemetry is stronger than zero trades

The inherited EA creates status/header telemetry during successful `OnInit()`. If the
forward Common Files root contains zero telemetry after attempted startup, the exact EA
did not initialize correctly or was not actually attached to the intended environment.

Do not wait for a trade to diagnose zero telemetry.

## Incident — manual attach creates avoidable operator error

Prefer deterministic startup configuration:

`compile exact source -> verify MQ5/EX5 -> copy exact expert -> generate startup config -> launch XAUUSDm M15 -> verify heartbeat`

Do not make manual attach the normal workflow.

## Historical recovery invariants retained after handover cleanup

The canonical handover must preserve the useful lessons from V38/V42/V44/V45 even though
obsolete per-version recovery files are removed.

- **immutable V38** means accepted evidence/source identity is never silently mutated just
  to make a later harness pass.
- The Windows **CP1252** incident requires explicit UTF-8 I/O.
- An inherited Bash **ERR trap** can still fire after `set +e`; prefer tracked Python
  orchestration rather than a fragile **runtime shell patcher**.
- A MetaEditor process return code is not a valid **compile artifact** verdict by itself.
- Git Bash / **MSYS** path conversion and Windows-native path semantics must be treated
  explicitly at process boundaries.
- The V44 **recovery ladder** is stage-local: recover the failed stage and use
  **package-only** recovery when packaging alone failed; **do not rerun MT5** for that.
- V45 **cold-start** and **look-ahead** validation preserved distinct historical windows,
  including 2025 and 2022 evidence, instead of tuning against only the latest sample.
- Historical completion markers such as `MT5_DONE.json` and `DONE.txt` are acceptance
  evidence. When those markers and required artifacts prove the MT5 phase completed,
  **MT5 must not rerun** merely because a downstream analysis/package step failed.

These are historical engineering invariants, not the current V69 runtime entrypoint.

## Historical Windows rules still preserved

### Explicit UTF-8

Windows default CP1252 previously broke UTF-8 repository text. Python text I/O must be
explicit UTF-8; launchers set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.

### Bash ERR trap

`set +e` does not disable an inherited/global Bash `ERR` trap. Do not build long MT5
campaign control flow around fragile shell trap behavior. Prefer tracked Python
orchestration.

### MetaEditor rc semantics

MetaEditor can return rc=1 while producing a valid compile log and EX5. Compile PASS is:

- exact source identity;
- final `Result: 0 errors, 0 warnings`;
- non-empty current EX5 tied to that source.

Process rc alone is not acceptance evidence.

### Runtime completion semantics

Terminal launch/exit alone is not success. Require milestone-specific status,
heartbeat/telemetry, completion markers and evidence files.

### Package-only recovery

If MT5 and analysis completed and ZIP creation alone failed, package the existing exact
output. Do not rerun MT5 merely to recreate a ZIP.

### Historical cold-start / disk incidents

Older V44/V45 cold-start, disk-exhaustion and MetaTester-junction evidence remains in the
research/ADR history. Use it only when working on those historical layers; it is not the
current V69 recovery entrypoint.

## Permanent invariants

- never `git clean`;
- do not `stash pop` during active runtime/evidence work;
- no credentials/secrets in Git;
- no Martingale;
- no uncontrolled grid;
- no doubling after loss;
- preserve strategy identity during validation;
- distinguish harness, broker transport and alpha failures;
- prevent duplicate execution;
- preserve order/retcode/deal auditability;
- background helpers must remain silent;
- REAL money remains fail-closed until a later explicit deployment decision.
