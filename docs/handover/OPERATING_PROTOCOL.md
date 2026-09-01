# OPERATING PROTOCOL — Exness / MT5 Quant Project

Updated: 2026-09-01

This file is the mandatory operating contract for any future ChatGPT session working on
`Tienkhoaa2908/exness-mt5-quant-trading`.

## 1. Repository authority

Primary/only repository to modify for this project:

`Tienkhoaa2908/exness-mt5-quant-trading`

`Tienkhoaa2908/vn-quant-system` is reference-only unless the user explicitly asks for a
change there.

Never recover project state from conversation memory alone. Git history, current branch,
CI, runtime evidence and the canonical handover documents are the source of truth.

## 2. Mandatory read-before-work sequence on every project-related user turn

Before proposing code, commands or conclusions, read/verify in this order:

1. current remote HEAD of the active branch;
2. `docs/handover/OPERATING_PROTOCOL.md`;
3. `docs/handover/CURRENT_STATE.md`;
4. `docs/handover/KNOWN_FAILURES.md`;
5. `docs/handover/TURN_SYNC.md`;
6. recent commits and relevant CI status on the exact current HEAD;
7. only then inspect milestone-specific code/evidence needed for the user's request.

Do not assume a SHA, launcher, metric or runtime status from an older chat when GitHub can
be checked directly.

## 3. Mandatory GitHub state-sync before every project-related final answer

Every project-related user turn must include a GitHub synchronization action before the
assistant gives its final answer.

Minimum requirement:

- update `docs/handover/TURN_SYNC.md` with the current request, what was inspected,
  changes made, verified result, unresolved blockers and next action;
- if project state materially changed, also update `docs/handover/CURRENT_STATE.md` and
  `docs/handover/KNOWN_FAILURES.md` as appropriate;
- commit those updates to the active project branch;
- verify the resulting remote branch HEAD;
- when code/runtime contracts changed, inspect CI on that exact HEAD before telling the
  user that the change is ready.

`TURN_SYNC.md` is intentionally overwritten rather than endlessly appended. Git history
preserves the timeline while the working tree always presents the latest state.

Do not create empty/noise-only commits. The turn-sync update itself must contain real
state: request, evidence, action, result or unresolved work.

## 4. User interaction / operator ergonomics

The user should normally need to run one Git Bash command block only.

Prefer:

`one command -> deterministic preflight -> compile -> launch -> verify -> supervise -> package`

Avoid:

- many manual shell fragments;
- manual EA attach when startup config can pin it;
- asking the user to find files that the runtime can discover itself;
- repeated historical backtests when the relevant evidence is already accepted;
- reopening MT5 merely for packaging/analysis;
- background console windows or helper processes that flash Terminal windows.

Long-running background helpers on Windows must use `pythonw.exe` and/or
`CREATE_NO_WINDOW` and suppress child console windows.

Never use `git clean`. Do not use `stash pop` during active MT5/evidence work.

## 5. Validation philosophy

Separate three layers explicitly:

1. **strategy/economic logic** — entries, exits, risk, state machine, edge;
2. **execution/broker transport** — volume, filling, permissions, `OrderCheck`, order
   retcodes, fills;
3. **harness/observability** — launcher, dashboard, telemetry, supervisor, packaging.

A harness failure is not strategy evidence. A broker transport failure is not an alpha
failure. Do not retune strategy thresholds to compensate for tooling errors.

For the current V69 forward smoke, historical replay already supplies the bulk of the
research evidence. The live DEMO forward step is intentionally short and primarily
checks execution/runtime integrity plus a small amount of additional economic evidence.

## 6. Runtime health must be visible on the MT5 chart

Active DEMO-forward EAs must display a pinned chart health panel containing at least:

- overall `SYSTEM HEALTH` state: `STARTING`, `READY`, or `BLOCKED`;
- broker/execution preflight status;
- DEMO/REAL mode and REAL authorization state;
- terminal/account/EA trade permissions;
- symbol + timeframe + tick heartbeat;
- fixed lot and broker min/max/step compatibility;
- latest `OrderCheck` local error + server retcode/comment;
- realized/floating PnL;
- open/flat position state;
- closed trades, wins, losses and recent trade details;
- progress, completed requirements, remaining requirements and output-export state;
- whether actual execution has been observed (`EXECUTION VERIFIED`) or is still awaiting
  the first natural strategy fill.

`READY` must never mean merely "EA is attached". It requires stable runtime and broker
health checks.

## 7. Broker preflight rules

Do not permanently block the system from one generic `GetLastError()==4756` result.
`4756` is `ERR_TRADE_SEND_FAILED`, a generic transport/send failure.

Broker preflight must:

- check `TERMINAL_CONNECTED`;
- check `ACCOUNT_TRADE_ALLOWED`;
- check `ACCOUNT_TRADE_EXPERT`;
- check `TERMINAL_TRADE_ALLOWED`;
- check `MQL_TRADE_ALLOWED`;
- check symbol synchronization;
- check symbol trade mode;
- check volume min/max/step against the actual fixed lot;
- check execution mode and choose request fields/filling accordingly;
- call `ResetLastError()` before `OrderCheck()`;
- record both `_LastError` and `MqlTradeCheckResult.retcode/comment`;
- retry transient failures on independent checks;
- require multiple consecutive READY checks before classifying the system healthy;
- classify deterministic permission/volume/symbol failures separately from transient
  transport failures.

A dry-run `OrderCheck` never proves a future fill. Actual execution is verified only by a
real DEMO strategy order/fill or a separately authorized DEMO execution probe.

## 8. Current safety boundary

Current V69 forward research is:

- `XAUUSDm M15`;
- LONG only;
- fixed lot `0.01`;
- DEMO only;
- SHORT disabled/rejected;
- REAL authorization false and fail-closed.

Do not auto-promote or auto-authorize REAL money. A later real deployment must be a
separate explicit decision after the DEMO/execution gate and risk review.

## 9. Documentation hygiene

Keep one canonical recovery path under `docs/handover/`.

Do not create a new per-version recovery document for every milestone. Historical ADRs,
research reports and Git commits can preserve lineage without polluting recovery state.

When a recovery document becomes superseded:

- merge still-useful facts into `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, or the relevant
  ADR/research document;
- delete the stale duplicate so a future session cannot mistake it for current state.

## 10. End-of-turn requirement

Before final response on each project-related user turn, confirm internally that:

- current GitHub state was read;
- the relevant issue was actually inspected rather than guessed;
- GitHub state was synchronized;
- any code claim is tied to the current branch/HEAD;
- no old launcher/SHA is being handed to the user;
- the next operator action is minimal and deterministic.
