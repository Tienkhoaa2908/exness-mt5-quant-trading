#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_upstream_signal_funnel.py"
OUT = HERE / "OUTPUT_V69_REAL_READINESS_PROBE"
EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=REPO, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_repo() -> tuple[str, str]:
    expected = os.environ.get("V69_UPSTREAM_DIAG_EXPECTED_HEAD", "").strip()
    if not expected:
        raise RuntimeError("V69_UPSTREAM_DIAG_EXPECTED_HEAD is required")
    branch = capture(["git", "branch", "--show-current"])
    head = capture(["git", "rev-parse", "HEAD"])
    dirty = capture(["git", "status", "--porcelain"])
    origin = capture(["git", "remote", "get-url", "origin"])
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


def common_mt5_quant_root() -> Path:
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise RuntimeError("APPDATA is not set; cannot locate MetaQuotes Common Files")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / "mt5_quant"


def candidate_roots(parent: Path) -> list[Path]:
    roots: list[Path] = []
    current = parent / "v69_frozen_forward_demo"
    if current.is_dir():
        roots.append(current)
    roots.extend(sorted((p for p in parent.glob("_v69_forward_previous_*") if p.is_dir()), reverse=True))
    return roots


def richness(result: dict) -> tuple[int, int, int]:
    stage_total = sum(int(v) for v in result.get("stage_counts", {}).values())
    return (int(result.get("events_rows", 0)), stage_total, int(result.get("closed_deals", 0)))


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_upstream_signal_funnel")
    parent = common_mt5_quant_root()
    print(f"V69_UPSTREAM_COMMON_PARENT={parent}")
    print("V69_UPSTREAM_READ_ONLY=1")
    print("V69_UPSTREAM_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_UPSTREAM_METAEDITOR_REQUIRED=0")
    print("V69_UPSTREAM_ORDERS_SENT=0")

    roots = candidate_roots(parent)
    if not roots:
        raise RuntimeError(f"no V69 forward telemetry roots found under {parent}")

    analyses = [analyzer.analyze(root) for root in roots]
    analyses.sort(key=richness, reverse=True)
    selected = analyses[0]
    if int(selected.get("events_rows", 0)) <= 0:
        raise RuntimeError("V69 telemetry roots found but none contain readable V64_EVENTS.csv rows")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "v69_upstream_signal_diagnostic_v1",
        "branch": branch,
        "head": head,
        "read_only": True,
        "mt5_can_remain_running": True,
        "orders_sent": False,
        "selected": selected,
        "all_roots": analyses,
    }
    out = OUT / "V69_UPSTREAM_SIGNAL_DIAGNOSTIC.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("V69_UPSTREAM_SOURCE_ROOT=" + selected["root"])
    print(f"V69_UPSTREAM_EVENTS_ROWS={selected['events_rows']}")
    for name, value in selected["stage_counts"].items():
        print(f"V69_UPSTREAM_{name}={value}")
    for name, value in selected.get("aux_event_counts", {}).items():
        print(f"V69_UPSTREAM_AUX_{name}={value}")
    print(f"V69_UPSTREAM_CLOSED_DEALS={selected['closed_deals']}")
    print("V69_UPSTREAM_CLASSIFICATION=" + selected["classification"])
    print("V69_UPSTREAM_TOP_BLOCKER=" + selected["dominant_blocker"])
    print("V69_UPSTREAM_NEXT_ACTION=" + selected["next_action"])
    print(
        "V69_UPSTREAM_CONFIRM_WAIT_REASONS="
        + json.dumps(selected.get("confirm_wait_reason_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    print("V69_UPSTREAM_TOP_EVENTS=" + json.dumps(selected.get("top_event_counts", {}), ensure_ascii=False, sort_keys=True))
    print(f"V69_UPSTREAM_ANALYZED_ROOTS={len(analyses)}")
    print(f"V69_UPSTREAM_RESULT_JSON={out}")
    print("V69_UPSTREAM_DIAGNOSTIC=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=os.sys.stderr)
        raise
