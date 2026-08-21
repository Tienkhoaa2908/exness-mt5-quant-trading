# Windows MT5 / Exness — V42 exact-router workflow

Broker research environment: Exness Technologies Ltd.; symbol `XAUUSDm`; timeframe M15. REAL-MONEY LIVE TRADING is forbidden.

Unlike V41 Stage A, V42 uses MetaTrader 5 Strategy Tester because router changes are path-dependent and shadow replay is insufficient.

Canonical branch: `agent/v42-baseline-router-exact-mt5`.
Clean one-shot bootstrap: `runtime/v42_baseline_router_exact_mt5/BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh`.
Current recovery from already compiled EA: `runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`.

## Direct-runner architecture

V42 no longer generates or patches shell scripts at runtime. The Python shell patcher was removed. The structure now matches the successful V32/V34/V38 workflows: tracked bootstrap -> tracked direct runner -> MetaEditor artifact gate -> MT5 -> analyzer -> ZIP.

Static tests run `bash -n` on bootstrap, full runner and resume runner and compare direct V42 launcher shape against successful V32/V34/V38 runner files.

## Clean full run

Before a clean full run, close manually opened MT5 and MetaEditor.

The full runner:

- verifies accepted V38 exact bundle SHA256 `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b` and CRC;
- extracts the immutable accepted `V38FastHarvestLab.base.a.mq5` parent;
- deterministically builds V42 twice and requires identical hashes;
- lints tester/no-order/risk markers;
- preserves an installed V42 source if its bytes already match the generated source;
- checks for reusable compile artifacts before deleting anything;
- accepts compile only from exact source SHA + final `Result: 0 errors, 0 warnings` + non-empty EX5;
- on a fresh compile polls the combined log/Result/EX5 postcondition rather than a fixed log-existence deadline;
- captures Windows return codes in Bash `if command; then ... else rc=$?; fi` context, never `set +e` under the global ERR trap;
- launches exact Strategy Tester on XAUUSDm M15, Model=0, USD40, 1:200, 2025-08-01 -> 2026-08-01, `AllowLiveTrading=0`, no DLL, non-visual;
- judges MT5 completion by a new `LATEST` run id/folder and complete manifested output, not process return code alone.

## Current recovery — compiled EA already exists

The 2026-08-21 20:12 attempt produced all three files in the accepted MT5 expert directory:

- `V42BaselineRouterLab.mq5`;
- `V42BaselineRouterLab.log`;
- `V42BaselineRouterLab.ex5`.

The then-current runner failed because it checked the compile-log postcondition just before filesystem outputs became observable. The directory diagnostic immediately showed `.log` and `.ex5`, so the current recovery should not launch MetaEditor again.

Run `RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`. It:

- verifies installed source SHA exactly `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`;
- decodes existing compile log and requires `Result: 0 errors, 0 warnings`;
- requires non-empty EX5 not older than installed source;
- re-verifies accepted V38 ZIP, V34 tape and frozen state;
- does **not** reference or launch MetaEditor;
- starts only Strategy Tester;
- waits for `monthly_summary.csv`, `trades.csv`, `manifest.txt` and mandatory tester/no-order markers before analysis;
- creates the same final one-ZIP evidence artifact.

If the existing compile log is not 0/0, resume prints the actual compiler evidence and stops instead of recompiling automatically.

Do not use `git clean`; runtime evidence, compiled EA files, checkpoints and environments may be untracked.

Upload only `runtime/v42_baseline_router_exact_mt5/OUTPUT_V42/v42_baseline_router_exact_mt5.zip`.
A V42 gate pass only freezes a challenger for fresh chronological confirmation. Risk remains <=1.00%/trade; no result authorizes real-money live trading.
