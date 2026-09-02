#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_SELECTOR_COVERAGE_RECOVERY"
ANALYZER = REPO / "scripts" / "analyze_v69_selector_coverage_recovery.py"
V69_BUILDER = REPO / "scripts" / "build_v69_confirm_separation_retest_source.py"
V64_SCREEN_OUTPUT = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "OUTPUT_V64"
V64_SCREEN_SOURCE = V64_SCREEN_OUTPUT / "V64MicrostructureTriggerShadowScreen.mq5"
V64_SCREEN_CSV = V64_SCREEN_OUTPUT / "screen" / "V64_ENTRY_EVAL.csv"
V64_ZIP = V64_SCREEN_OUTPUT / "v64_microstructure_trigger_shadow_research.zip"


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
    expected_head = os.environ.get("V69_SELECTOR_COVERAGE_EXPECTED_HEAD", "").strip()
    if not expected_head:
        raise RuntimeError("V69_SELECTOR_COVERAGE_EXPECTED_HEAD is required")
    origin = capture(["git", "remote", "get-url", "origin"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected_head}")
    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError("wrong repository")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected_head:
        raise RuntimeError(f"wrong HEAD expected={expected_head} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return branch, head


def extract_from_zip() -> tuple[Path, Path] | None:
    if not V64_ZIP.is_file():
        return None
    OUT.mkdir(parents=True, exist_ok=True)
    source_out = OUT / "RECOVERED_V64_SCREEN_SOURCE.mq5"
    csv_out = OUT / "RECOVERED_V64_SCREEN_ENTRY_EVAL.csv"
    with zipfile.ZipFile(V64_ZIP) as archive:
        names = archive.namelist()
        source_name = next((name for name in names if name.endswith("/V64MicrostructureTriggerShadowScreen.mq5")), None)
        csv_name = next((name for name in names if name.endswith("/screen/V64_ENTRY_EVAL.csv")), None)
        if source_name is None or csv_name is None:
            return None
        source_out.write_bytes(archive.read(source_name))
        csv_out.write_bytes(archive.read(csv_name))
    print(f"V69_COVERAGE_RECOVERED_FROM_ZIP={V64_ZIP}")
    return source_out, csv_out


def discover_evidence() -> tuple[Path, Path, str]:
    if V64_SCREEN_SOURCE.is_file() and V64_SCREEN_CSV.is_file():
        return V64_SCREEN_SOURCE, V64_SCREEN_CSV, "V64_OUTPUT_SCREEN"
    recovered = extract_from_zip()
    if recovered is not None:
        return recovered[0], recovered[1], "V64_EVIDENCE_ZIP"
    raise RuntimeError(
        "accepted V64 directional-screen evidence is not present locally; "
        "do not stop MT5 just for this. Return this message so a non-disruptive fallback can be chosen."
    )


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_selector_coverage_analyzer")
    v69 = load(V69_BUILDER, "v69_parent_for_selector_coverage")
    source_path, csv_path, kind = discover_evidence()
    print(f"V69_SELECTOR_COVERAGE_SOURCE_KIND={kind}")
    print(f"V69_SELECTOR_COVERAGE_SCREEN_SOURCE={source_path}")
    print(f"V69_SELECTOR_COVERAGE_SCREEN_CSV={csv_path}")

    screen_source = source_path.read_text(encoding="utf-8-sig", errors="replace")
    v69_source = v69.transform(1)
    identity = analyzer.compare_directional_core(screen_source, v69_source)
    print("V69_SELECTOR_DIRECTIONAL_CORE_IDENTITY=" + json.dumps(identity, sort_keys=True))
    if not identity["exact_directional_core_match"]:
        raise RuntimeError(
            "V64 screen directional core is not byte-equivalent to frozen V69 selector/features; "
            "historical coverage cannot be reused honestly"
        )

    coverage = analyzer.analyze_csv(csv_path)
    result = {
        "protocol": "v69_selector_coverage_recovery_v1",
        "branch": branch,
        "head": head,
        "source_kind": kind,
        "selector_identity": identity,
        "coverage": coverage,
        "development_coverage_only": True,
        "independent_edge_evidence": False,
        "strategy_changed": False,
        "orders_sent": 0,
        "real_money_authorized": False,
        "short_enabled": False,
        "mt5_can_remain_running": True,
        "metaeditor_required": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "V69_SELECTOR_COVERAGE_RECOVERY.json"
    summary = OUT / "V69_SELECTOR_COVERAGE_SUMMARY.txt"
    analyzer.write_outputs(result, output, summary)

    print(f"V69_SELECTOR_COVERAGE_UNIQUE_M15_ROWS={coverage['unique_m15_rows']}")
    print(f"V69_SELECTOR_COVERAGE_FIRST_TIME={coverage['first_time']}")
    print(f"V69_SELECTOR_COVERAGE_LAST_TIME={coverage['last_time']}")
    print(f"V69_SELECTOR_COVERAGE_FEATURE_READY_PCT={coverage['feature_ready_pct']}")
    print("V69_SELECTOR_COVERAGE_SELECTED_DIRECTIONS=" + json.dumps(coverage["selected_direction_counts"], sort_keys=True))
    print("V69_SELECTOR_COVERAGE_DECISION_REASONS=" + json.dumps(coverage["decision_reason_counts"], sort_keys=True))
    print("V69_SELECTOR_COVERAGE_HTF_REGIMES=" + json.dumps(coverage["htf_regime_counts"], sort_keys=True))
    print(f"V69_SELECTOR_COVERAGE_LONG_SELECTED_PCT_ALL_BARS={coverage['long_selected_pct_all_bars']}")
    print(f"V69_SELECTOR_COVERAGE_SHORT_SELECTED_PCT_ALL_BARS={coverage['short_selected_pct_all_bars']}")
    print(f"V69_SELECTOR_COVERAGE_NEUTRAL_SELECTED_PCT_ALL_BARS={coverage['neutral_selected_pct_all_bars']}")
    print(f"V69_SELECTOR_COVERAGE_LONG_SHARE_OF_DIRECTIONAL_PCT={coverage['long_share_of_directional_pct']}")
    print(f"V69_SELECTOR_COVERAGE_SHORT_SHARE_OF_DIRECTIONAL_PCT={coverage['short_share_of_directional_pct']}")
    print(f"V69_SELECTOR_COVERAGE_CLASSIFICATION={coverage['classification']}")
    print(f"V69_SELECTOR_COVERAGE_BY_MONTH={json.dumps(coverage['by_month'], sort_keys=True)}")
    print(f"V69_SELECTOR_COVERAGE_RESULT_JSON={output}")
    print(f"V69_SELECTOR_COVERAGE_SUMMARY={summary}")
    print("V69_SELECTOR_COVERAGE_DEVELOPMENT_ONLY=1")
    print("V69_SELECTOR_COVERAGE_INDEPENDENT_EDGE_EVIDENCE=0")
    print("V69_SELECTOR_COVERAGE_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_SELECTOR_COVERAGE_METAEDITOR_REQUIRED=0")
    print("V69_SELECTOR_COVERAGE_ORDERS_SENT=0")
    print("V69_SELECTOR_COVERAGE_STRATEGY_CHANGED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V69_SELECTOR_COVERAGE_RECOVERY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
