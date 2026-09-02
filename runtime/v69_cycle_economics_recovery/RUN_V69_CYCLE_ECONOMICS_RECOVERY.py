#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"
EXPECTED_IDENTITY = {"cycles": 460, "sent": 24, "wins": 10, "losses": 14, "net_usd": 7.14}
EXPECTED_FAMILIES = {
    "CONTEXT_QUALITY": 80,
    "HARD_STRUCTURAL": 235,
    "SENT_ORDER": 24,
    "TTL_EXPIRY": 120,
    "UNTERMINATED": 1,
}
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_CYCLE_ECONOMICS_RECOVERY"
ANALYZER = REPO / "scripts" / "analyze_v69_cycle_economics_rearm.py"
DOWNSTREAM_RUNNER = REPO / "runtime" / "v69_downstream_funnel_recovery" / "RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_repo() -> tuple[str, str]:
    expected = os.environ.get("V69_CYCLE_ECONOMICS_EXPECTED_HEAD", "").strip()
    if not expected:
        raise RuntimeError("V69_CYCLE_ECONOMICS_EXPECTED_HEAD is required")
    origin = capture(["git", "remote", "get-url", "origin"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected}")
    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError("wrong repository")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected:
        raise RuntimeError(f"wrong HEAD expected={expected} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return branch, head


def assert_accepted_identity(result: dict) -> None:
    overall = result.get("overall", {})
    mismatches = []
    for key in ("cycles", "sent", "wins", "losses"):
        actual = int(overall.get(key, -1))
        if actual != EXPECTED_IDENTITY[key]:
            mismatches.append(f"{key}:expected={EXPECTED_IDENTITY[key]} actual={actual}")
    try:
        net = float(overall.get("net_usd"))
    except (TypeError, ValueError):
        net = float("nan")
    if not (abs(net - EXPECTED_IDENTITY["net_usd"]) <= 0.02):
        mismatches.append(f"net_usd:expected=7.14 actual={overall.get('net_usd')}")
    families = result.get("terminal_family_counts", {})
    if families != EXPECTED_FAMILIES:
        mismatches.append(f"terminal_families:expected={EXPECTED_FAMILIES} actual={families}")
    if mismatches:
        raise RuntimeError("V69 cycle-economics accepted identity mismatch: " + "; ".join(mismatches))
    print("V69_CYCLE_ECONOMICS_ACCEPTED_IDENTITY=PASS")


def compact_months(result: dict) -> dict:
    return {
        month: {
            "economics": block["economics"],
            "by_archetype": block["by_archetype"],
        }
        for month, block in result["by_month"].items()
    }


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_cycle_economics_rearm")
    downstream = load(DOWNSTREAM_RUNNER, "v69_downstream_source_for_cycle_economics")
    v69_root, source_kind = downstream.discover_v69_root()
    print(f"V69_CYCLE_ECONOMICS_V69_SOURCE_KIND={source_kind}")
    print(f"V69_CYCLE_ECONOMICS_V69_ROOT={v69_root}")

    result = analyzer.analyze(v69_root)
    assert_accepted_identity(result)
    result["branch"] = branch
    result["head"] = head
    result["v69_source_kind"] = source_kind
    result["v69_root"] = str(v69_root)

    output = OUT / "V69_CYCLE_ECONOMICS_REARM.json"
    summary = OUT / "V69_CYCLE_ECONOMICS_REARM_SUMMARY.txt"
    analyzer.write_outputs(result, output, summary)

    print("V69_CYCLE_ECONOMICS_FAMILIES=" + json.dumps(result["terminal_family_counts"], sort_keys=True))
    print(f"V69_CYCLE_ECONOMICS_HARD_STRUCTURAL_SHARE_PCT={result['hard_structural_share_pct']}")
    print(f"V69_CYCLE_ECONOMICS_TTL_PLUS_CONTEXT_CYCLES={result['ttl_plus_context_cycles']}")
    print(f"V69_CYCLE_ECONOMICS_TTL_PLUS_CONTEXT_SHARE_PCT={result['ttl_plus_context_share_pct']}")
    print("V69_CYCLE_ECONOMICS_ARCHETYPES=" + json.dumps(result["by_archetype"], sort_keys=True))
    print("V69_CYCLE_ECONOMICS_REARM=" + json.dumps(result["rearm"], sort_keys=True))
    print("V69_CYCLE_ECONOMICS_TRADE_TRANSITIONS=" + json.dumps(result["trade_transitions"], sort_keys=True))
    print("V69_CYCLE_ECONOMICS_BY_MONTH=" + json.dumps(compact_months(result), sort_keys=True))
    print(f"V69_CYCLE_ECONOMICS_RESULT_JSON={output}")
    print(f"V69_CYCLE_ECONOMICS_SUMMARY={summary}")
    print("V69_CYCLE_ECONOMICS_ARCHETYPE_REARM_IS_NOT_SETUP_IDENTITY=1")
    print("V69_CYCLE_ECONOMICS_DEVELOPMENT_ONLY=1")
    print("V69_CYCLE_ECONOMICS_INDEPENDENT_EDGE_EVIDENCE=0")
    print("V69_CYCLE_ECONOMICS_COUNTERFACTUAL_REJECT_EDGE_PROVEN=0")
    print("V69_CYCLE_ECONOMICS_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_CYCLE_ECONOMICS_METAEDITOR_REQUIRED=0")
    print("V69_CYCLE_ECONOMICS_ORDERS_SENT=0")
    print("V69_CYCLE_ECONOMICS_STRATEGY_CHANGED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V69_CYCLE_ECONOMICS_RECOVERY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
