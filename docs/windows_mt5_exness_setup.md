# Windows MT5 / Exness — V41 research workflow

Broker environment: Exness Technologies Ltd.; research symbol `XAUUSDm`; main timeframe M15. REAL-MONEY LIVE TRADING is forbidden.

## V41 Stage A

V41 is offline/read-only. It reuses accepted V38 exact telemetry and V36 predictions; it does **not** launch MT5 or MetaEditor.

Canonical branch: `agent/v41-baseline-stack-action-value`.

One-shot bootstrap: `runtime/v41_baseline_stack/BOOTSTRAP_V41_BASELINE_STACK_ONE_SHOT_GIT_BASH.sh`.

The runner:

1. validates branch/HEAD environment;
2. compiles V41 plus V40 schema/core dependencies;
3. runs nine static/unit gates (pytest if installed, dependency-free fallback otherwise);
4. secret-scans tracked source only;
5. verifies/reuses accepted V38 evidence;
6. reuses accepted V36 predictions or invokes the hardened offline V36 recovery runner if missing;
7. runs entry expected-R, V36 calibration, direct action-value and integrated baseline-stack diagnostics;
8. writes one manifest-verified ZIP and validates it with `scripts/analyze_mt5_research_bundle.py`.

Do not use `git clean`; accepted runtime evidence and Python environments can be untracked.

Upload only:

`runtime/v41_baseline_stack/OUTPUT_V41_STAGE_A/v41_baseline_stack_action_value_stage_a.zip`

The terminal reports exact baseline 8.58%/month separately from entry/action/stack shadow economics and the 15%/month target. Shadow results are not exact-MT5 PnL.

Only a preregistered Stage-A promotion lane may be frozen for a future exact-MT5 Stage B. Stage B must preserve <=1.00% stop-risk and re-verify tick/history coverage. Never use manual/live orders to debug a research failure.
