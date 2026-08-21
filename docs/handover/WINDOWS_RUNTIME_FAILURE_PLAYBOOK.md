# Windows / Git Bash / MetaEditor / MT5 Runtime Failure Playbook

Last updated: 2026-08-21

This file is part of the recovery source of truth. Read it with `CURRENT_STATE.md` and `RECOVERY_PROMPT.md` before changing any exact-MT5 runner.

## Prime rule

**Do not rerun MT5 when the exact Strategy Tester run already completed and the failure happened later in collection, analysis, manifest generation, or ZIP packaging.** Resume from the failed stage.

The purpose of this playbook is to prevent repeated rediscovery of V42 runtime failures.

## Recovery ladder

Always identify the last completed durable artifact and resume one stage after it.

1. **Source/provenance failure**
   - no compiled V43/V42 EA exists for the intended source;
   - repair source/provenance only;
   - do not run MT5.
2. **Compile failure**
   - source exists but compiler `Result: 0 errors, 0 warnings` + EX5 does not;
   - repair/retry compile only;
   - do not run MT5 until compile artifact gate passes.
3. **MT5 launch/execution failure**
   - compile artifact gate passed but no new LATEST/run folder exists;
   - retry Strategy Tester only after checking terminal state/config.
4. **Collection failure**
   - new LATEST/run folder exists but monthly/trades/manifest are still flushing;
   - wait/recover collection from the same run folder;
   - do not rerun MT5.
5. **Analysis failure**
   - complete run outputs exist;
   - rerun analyzer only;
   - do not rerun MT5.
6. **Packaging failure**
   - analyzer/evidence bundle exists;
   - run package-only recovery;
   - do not rerun MT5.

Never replace this ladder with a whole-workflow restart merely because it is simpler to script.

## Incident 1 — historical source-builder byte drift

Observed in V42:

- current V34 reconstruction emitted a different deterministic SHA (`228b3ec7...`);
- a stale historical contract expected `8bae2c56...`.

Do not update an accepted historical hash merely because a current builder emits new bytes.

### Mandatory rule: immutable V38 parent

Exact router research must anchor directly to accepted V38 ZIP:

`runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`

SHA256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

Verify outer SHA, ZIP CRC, unique `V38FastHarvestLab.base.a.mq5`, release/tester/router markers, then build the new source from those accepted bytes. Do not reconstruct the parent via historical V34/V38 source builders.

## Incident 2 — Windows CP1252 decoded UTF-8 tracked files

A V42 static test used bare `Path.read_text()` on a UTF-8 generated shell file. Windows Python selected CP1252 and raised `UnicodeDecodeError` on byte `0x9d`.

### Mandatory controls

- tracked/research text reads specify `encoding='utf-8'` or `utf-8-sig` as appropriate;
- bootstrap and runner export:
  - `PYTHONUTF8=1`
  - `PYTHONIOENCODING=utf-8`
- never depend on Windows active code page for repository files.

## Incident 3 — Bash ERR trap survives `set +e`

A V42 runner used `set -Eeuo pipefail` with a global ERR trap, then tried:

`set +e; metaeditor64.exe ...; rc=$?; set -e`

MetaEditor returned rc=1 and the ERR trap terminated the runner before the return code could be captured. The downstream MT5 launcher had the same latent defect.

### Mandatory controls

Never use `set +e` for Windows launcher recovery under the global ERR trap.

Use conditional context:

```bash
if command; then
  rc=0
else
  rc=$?
fi
```

This applies to both MetaEditor and `terminal64.exe`.

## Incident 4 — runtime patcher/self-modifying shell increased failure surface

V42 temporarily used a Python runtime patcher to transform a base shell runner into a generated runner. That architecture created additional escaping, encoding and control-flow failure modes.

### Mandatory rule

No runtime patcher and no self-modifying/generated execution shell for exact-MT5 research. Use a direct tracked runner shaped like the successful V32/V34/V38 workflows. Static tests must inspect the tracked runner itself.

## Incident 5 — MetaEditor launcher return code and compile artifact race

Observed V42 state:

- `METAEDITOR_LAUNCH_RC=1`;
- runner initially concluded compile log was missing;
- diagnostic listing moments later showed `V42BaselineRouterLab.mq5`, `.log` and `.ex5` all present;
- compile log was `Result: 0 errors, 0 warnings`.

The launcher return code was not the economic/research failure and the filesystem artifact was slightly delayed.

### Mandatory compile artifact gate

Compile success is defined by all of:

1. installed/generated source hashes to the intended frozen source SHA;
2. compiler log contains final `Result: 0 errors, 0 warnings`;
3. non-empty EX5 exists and corresponds to the current source.

Check existing compile artifacts **before deleting them**. A valid compile checkpoint may be reused.

For a fresh compile, poll the combined log + final Result + EX5 postcondition. Do not fail only because a fixed short log-existence deadline elapsed. MetaEditor launcher rc alone never defines compile success.

## Incident 6 — MT5 launcher rc is not the durable completion artifact

Treat exact MT5 completion as data, not merely a process return code.

### Mandatory MT5 postcondition

Require:

- a new `ML_DL_FEATURE_LAKE_LATEST.txt` run id/folder relative to the pre-run value;
- the referenced run folder exists;
- `monthly_summary.csv`, `trades.csv`, and `manifest.txt` are non-empty;
- manifest includes `tester_only=1`, `native_broker_orders=0`, `external_broker_orders=0`, and the experiment marker.

Wait for output flushing where necessary. Once a new complete run folder exists, preserve/recover it rather than starting another Strategy Tester run.

## Incident 7 — MSYS `sha256sum` output is not portable manifest syntax

After V42 exact MT5 and analysis completed, packaging failed because Git Bash/MSYS emitted manifest rows such as:

`<sha256> *filename`

while inline Python assumed Linux text-mode output:

`<sha256><two spaces>filename`

The exact research evidence was complete; only ZIP packaging failed.

### Mandatory portable packaging

Use `scripts/package_research_bundle_portable.py`.

It computes hashes in Python, writes canonical `<hash><two spaces><filename>` rows, verifies every file, creates the ZIP, and runs ZIP CRC validation. Do not parse raw `sha256sum` line formatting in Python.

## Incident 8 — package-only recovery is mandatory

Every expensive exact-MT5 runner must have a package-only recovery path from inception.

If these already exist:

- experiment evidence file;
- analyzer JSON/CSV;
- `monthly_summary.csv`;
- `trades.csv`;
- tester `manifest.txt`;

then a final packaging error must invoke package-only recovery or instruct the operator to invoke it. **Do not rerun MT5.**

V42 example:
`runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh`

V43 example:
`runtime/v43_confidence_router_exact_mt5/PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh`

## Incident 9 — do not destroy untracked recovery assets

Do not use `git clean` in these workflows. Accepted ZIPs, `.venv`, checkpoints, state files, compiled EA artifacts and collected outputs may be untracked and necessary for recovery.

Use explicit branch refspec fetch + checkout/reset of tracked source only.

## Incident 10 — syntax and structure must be checked before Windows execution

Before MetaEditor or MT5:

- `python -m py_compile` all Python helpers/tests used by the run;
- dependency-free static tests if pytest is unavailable;
- `bash -n` every executable shell entrypoint: bootstrap, direct runner, resume/package-only scripts;
- tracked-source secret scan;
- generated MQL safety lint;
- exact source hashes and immutable-parent hashes.

A Windows machine should adjudicate MetaEditor/MT5 behavior and market results, not discover ordinary shell syntax, Python encoding or manifest-parser bugs.

## Escalation / interpretation rules

- A compile/runtime failure produces **no strategy evidence**.
- An exact MT5 run with successful control reproduction does produce strategy evidence even if later packaging fails; recover/package the existing evidence.
- Shadow/offline PnL does not replace exact-MT5 adjudication for path-dependent router changes.
- Do not weaken an acceptance gate to make a run pass.
- Do not conduct a same-window rescue parameter sweep after a HOLD.
- REAL-MONEY LIVE TRADING remains forbidden.
