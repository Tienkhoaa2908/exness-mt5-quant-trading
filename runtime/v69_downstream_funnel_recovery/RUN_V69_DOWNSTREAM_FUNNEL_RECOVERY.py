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
OUT = HERE / "OUTPUT_V69_DOWNSTREAM_FUNNEL_RECOVERY"
ANALYZER = REPO / "scripts" / "analyze_v69_downstream_long_funnel.py"
V64_SCREEN = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "OUTPUT_V64" / "screen" / "V64_ENTRY_EVAL.csv"
V69_OUT = REPO / "runtime" / "v69_confirm_separation_retest" / "OUTPUT_V69"
V69_ZIP = V69_OUT / "v69_confirm_separation_retest_research.zip"


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
    expected = os.environ.get("V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD", "").strip()
    if not expected:
        raise RuntimeError("V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD is required")
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


def discover_screen() -> Path:
    if V64_SCREEN.is_file():
        return V64_SCREEN
    recovered = (
        REPO
        / "runtime"
        / "v69_selector_coverage_recovery"
        / "OUTPUT_V69_SELECTOR_COVERAGE_RECOVERY"
        / "RECOVERED_V64_SCREEN_ENTRY_EVAL.csv"
    )
    if recovered.is_file():
        return recovered
    raise RuntimeError("V64 all-bar screen CSV missing; do not restart MT5. Return this FATAL for fallback.")


def direct_v69_root() -> Path | None:
    runs = sorted(V69_OUT.glob("holdout_*_long"))
    if len(runs) >= 9:
        return V69_OUT
    return None


def recover_v69_from_zip() -> Path | None:
    if not V69_ZIP.is_file():
        return None
    root = OUT / "RECOVERED_V69_DEVELOPMENT"
    if root.exists():
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
    root.mkdir(parents=True, exist_ok=True)
    copied = 0
    with zipfile.ZipFile(V69_ZIP) as archive:
        for name in archive.namelist():
            normalized = name.replace("\\", "/")
            marker = "/OUTPUT_V69/"
            if marker not in normalized or "/holdout_" not in normalized or "_long/" not in normalized:
                continue
            if not normalized.endswith(("/V64_ENTRY_EVAL.csv", "/V64_EVENTS.csv", "/V64_DEALS.csv")):
                continue
            tail = normalized.split(marker, 1)[1]
            dest = root / tail
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(name))
            copied += 1
    if len(list(root.glob("holdout_*_long"))) < 9:
        return None
    print(f"V69_DOWNSTREAM_RECOVERED_FROM_ZIP={V69_ZIP}")
    print(f"V69_DOWNSTREAM_RECOVERED_FILES={copied}")
    return root


def discover_v69_root() -> tuple[Path, str]:
    direct = direct_v69_root()
    if direct is not None:
        return direct, "V69_OUTPUT_DIRECT"
    recovered = recover_v69_from_zip()
    if recovered is not None:
        return recovered, "V69_ACCEPTED_ZIP"
    raise RuntimeError(
        "V69 Sep-May LONG development telemetry is not present locally as run directories or ZIP; "
        "do not rerun MT5 tester yet. Return this FATAL so the next fallback can be chosen."
    )


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_downstream_long_funnel")
    screen = discover_screen()
    v69_root, source_kind = discover_v69_root()
    print(f"V69_DOWNSTREAM_SCREEN_CSV={screen}")
    print(f"V69_DOWNSTREAM_V69_SOURCE_KIND={source_kind}")
    print(f"V69_DOWNSTREAM_V69_ROOT={v69_root}")

    result = analyzer.analyze(screen, v69_root)
    result["branch"] = branch
    result["head"] = head
    result["v69_source_kind"] = source_kind
    result["screen_csv"] = str(screen)
    result["v69_root"] = str(v69_root)
    output = OUT / "V69_DOWNSTREAM_LONG_FUNNEL_RECOVERY.json"
    summary = OUT / "V69_DOWNSTREAM_LONG_FUNNEL_SUMMARY.txt"
    analyzer.write_outputs(result, output, summary)

    print(f"V69_DOWNSTREAM_SELECTOR_LONG_ROWS_DEVELOPMENT={result['selector_context']['long_selected_rows']}")
    print(f"V69_DOWNSTREAM_SELECTOR_LONG_STREAKS={result['selector_context']['long_selector_streaks']}")
    print("V69_DOWNSTREAM_INITIAL_EVAL=" + json.dumps({k: result['initial_eval'][k] for k in ('rows','pending_eval_rows','pre_pending_reject_rows')}, sort_keys=True))
    print("V69_DOWNSTREAM_INITIAL_REJECTS=" + json.dumps(result["initial_eval"]["reject_reasons"], sort_keys=True))
    print(f"V69_DOWNSTREAM_PENDING_ARM_CYCLES={result['pending_arm_cycles']}")
    print("V69_DOWNSTREAM_CYCLE_STAGE_REACH=" + json.dumps(result["cycle_stage_reach"], sort_keys=True))
    print(f"V69_DOWNSTREAM_REFINED_ENTRY_SENT_CYCLES={result['refined_entry_sent_cycles']}")
    print("V69_DOWNSTREAM_EVENT_COUNTS=" + json.dumps(result["event_counts"], sort_keys=True))
    print("V69_DOWNSTREAM_TERMINAL_REASONS=" + json.dumps(result["terminal_reasons"], sort_keys=True))
    print("V69_DOWNSTREAM_DEALS=" + json.dumps(result["deals"], sort_keys=True))
    print("V69_DOWNSTREAM_DOMINANT_DROP=" + json.dumps(result["dominant_cycle_drop"], sort_keys=True))
    print("V69_DOWNSTREAM_BY_MONTH=" + json.dumps(result["by_month"], sort_keys=True))
    print(f"V69_DOWNSTREAM_RESULT_JSON={output}")
    print(f"V69_DOWNSTREAM_SUMMARY={summary}")
    print("V69_DOWNSTREAM_DEVELOPMENT_ONLY=1")
    print("V69_DOWNSTREAM_INDEPENDENT_EDGE_EVIDENCE=0")
    print("V69_DOWNSTREAM_COUNTERFACTUAL_REJECT_EDGE_PROVEN=0")
    print("V69_DOWNSTREAM_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_DOWNSTREAM_METAEDITOR_REQUIRED=0")
    print("V69_DOWNSTREAM_ORDERS_SENT=0")
    print("V69_DOWNSTREAM_STRATEGY_CHANGED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V69_DOWNSTREAM_FUNNEL_RECOVERY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
