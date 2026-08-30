#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
V60_RUNNER = REPO / "runtime" / "v60_small_loss_cash_target" / "RUN_V60_SMALL_LOSS_CASH_TARGET.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v60 = load(V60_RUNNER, "v60_runner_parent_for_v61")
base = v60.base

EXPECTED_BRANCH = "agent/v61-profit-ratchet-m5-refinement-research"
OUT = HERE / "OUTPUT_V61"
ZIP_OUT = OUT / "v61_profit_ratchet_m5_refinement_research.zip"
REAL_EXPERT = "V61ProfitRatchetM5Refinement"
SCREEN_EXPERT = "V61ProfitRatchetM5RefinementScreen"
BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v61_profit_ratchet_m5_refinement.py"
STATIC_TEST = REPO / "tests" / "test_v61_profit_ratchet_m5_refinement_static.py"
ADR = REPO / "docs" / "adr" / "ADR-063-v61-profit-ratchet-m5-refinement-research.md"

# Rebind parent runner globals. Its generic compile/config/tester helpers then operate on V61.
v60.EXPECTED_BRANCH = EXPECTED_BRANCH
v60.OUT = OUT
v60.ZIP_OUT = ZIP_OUT
v60.REAL_EXPERT = REAL_EXPERT
v60.SCREEN_EXPERT = SCREEN_EXPERT
v60.BUILDER = BUILDER
v60.SCREEN_BUILDER = SCREEN_BUILDER
v60.ANALYZER = ANALYZER
v60.STATIC_TEST = STATIC_TEST
v60.ADR = ADR


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / "v61_profit_ratchet_m5_refinement"
    if root.exists():
        archived = parent / f"_v61_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{label}"
        root.rename(archived)
        print(f"V61_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def copy_run(root: Path, label: str) -> Path:
    dst = OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    expected = ("V61_ENTRY_EVAL.csv", "V61_EVENTS.csv", "V61_DEALS.csv", "V61_SHADOW_RR.csv", "V61_STATUS.txt")
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)
    eval_file = dst / "V61_ENTRY_EVAL.csv"
    if not eval_file.is_file() or eval_file.stat().st_size <= 0:
        raise RuntimeError(f"V61 run {label} missing entry evaluation evidence")
    return dst


def parse_time(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%Y.%m.%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def monday(dt: datetime) -> datetime:
    d = dt - timedelta(days=dt.weekday())
    return datetime(d.year, d.month, d.day)


def select_directional_windows(screen_dir: Path) -> dict:
    path = screen_dir / "V61_ENTRY_EVAL.csv"
    weeks: dict[int, Counter[str]] = {1: Counter(), -1: Counter()}
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                d = int(float(row.get("selected_direction", "0") or 0))
                feasible = int(float(row.get("feasible", "0") or 0))
                h4 = int(float(row.get("h4_trend", "0") or 0))
                h1 = int(float(row.get("h1_trend", "0") or 0))
            except ValueError:
                continue
            if d not in (1, -1) or feasible != 1 or h4 != d or h1 != d:
                continue
            dt = parse_time(row.get("time", ""))
            if dt is not None:
                weeks[d][monday(dt).strftime("%Y.%m.%d")] += 1

    used: set[str] = set()
    result: dict[str, list[dict]] = {"long": [], "short": []}
    for d, key, label in ((1, "long", "LONG"), (-1, "short", "SHORT")):
        items = sorted(weeks[d].items(), key=lambda kv: (kv[0], kv[1]), reverse=True)
        for start_s, count in items:
            if start_s in used:
                continue
            start = datetime.strptime(start_s, "%Y.%m.%d")
            result[key].append({
                "direction": label,
                "from": start_s,
                "to": (start + timedelta(days=5)).strftime("%Y.%m.%d"),
                "screen_signal_count": count,
                "selection_basis": "two_most_recent_feasible_strict_h4_h1_v61_weeks_not_pnl",
            })
            used.add(start_s)
            if len(result[key]) >= 2:
                break
    if len(result["long"]) < 2 or len(result["short"]) < 2:
        raise RuntimeError(
            "V61 screen did not find two feasible strict H4/H1 weeks per side; "
            f"long_weeks={dict(weeks[1])} short_weeks={dict(weeks[-1])}"
        )
    (OUT / "V61_SELECTED_WINDOWS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V61_DIRECTIONAL_WINDOWS=" + json.dumps(result, sort_keys=True))
    return result


def analyze(real_dirs: list[Path]) -> tuple[Path, Path]:
    out = OUT / "v61_analysis.json"
    summary = OUT / "V61_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in real_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", out, "--summary", summary]
    v60.run(cmd)
    return out, summary


def package(branch: str, head: str, sources: list[Path], compiles: list[Path], screen: Path, real_dirs: list[Path]) -> None:
    evidence = OUT / "V61_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V61_PROFIT_RATCHET_M5_REFINEMENT_RESEARCH=1",
        f"branch={branch}", f"head={head}", "fixed_lot=0.01",
        "primary_target_cash=3.00", "profit_arm_cash=2.00", "profit_lock_cash=1.00",
        "shadow_target_cash=2.00,3.00,4.00", "min_structural_risk_cash=0.75",
        "max_structural_risk_cash=1.25", "m5_refinement=1", "ordercheck_preflight=1",
        "strict_h4_h1_alignment=1", "screen_model=2", "real_tick_model=4",
        "validation_windows=2_long_plus_2_short", "window_selection=pnl_independent_directional_regime",
        "tester_only=1", "real_money_authorized=0", ""
    ]), encoding="utf-8")

    stage = OUT / "bundle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    files = sources + compiles + [BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST, ADR, Path(__file__).resolve(),
        OUT / "V61_SELECTED_WINDOWS.json", OUT / "v61_analysis.json", OUT / "V61_SUMMARY.txt", evidence]
    files += list(OUT.glob("v60_*.ini")) + list(OUT.glob("v61_*.ini"))
    manifest: list[str] = []
    used: set[str] = set()
    for p in files:
        if not p.is_file():
            continue
        name = p.name if p.name not in used else "top__" + p.name
        used.add(name)
        dst = stage / name
        shutil.copy2(p, dst)
        manifest.append(f"{v60.sha(dst)}  {name}")
    for rd in [screen] + real_dirs:
        for p in rd.iterdir():
            if not p.is_file():
                continue
            name = f"{rd.name}__{p.name}"
            dst = stage / name
            shutil.copy2(p, dst)
            manifest.append(f"{v60.sha(dst)}  {name}")
    (stage / "bundle_manifest_sha256.txt").write_text("\n".join(sorted(manifest)) + "\n", encoding="utf-8")
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(stage.iterdir()):
            if p.is_file():
                z.write(p, p.name)
    with zipfile.ZipFile(ZIP_OUT) as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError(f"V61 ZIP CRC failure: {bad}")
    print(f"V61_ZIP={ZIP_OUT}")
    print(f"V61_ZIP_SHA256={v60.sha(ZIP_OUT)}")
    print("V61_PACKAGE_PASS=1")


v60.reset_common = reset_common
v60.copy_run = copy_run
v60.select_directional_windows = select_directional_windows
v60.analyze = analyze
v60.package = package


def main() -> int:
    rc = v60.main()
    print("V61_DONE=1")
    return rc


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
