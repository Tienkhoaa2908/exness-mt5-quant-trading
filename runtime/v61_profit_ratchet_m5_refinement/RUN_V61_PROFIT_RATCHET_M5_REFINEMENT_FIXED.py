#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PARENT_RUNNER = HERE / "RUN_V61_PROFIT_RATCHET_M5_REFINEMENT.py"
FIXED_BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_source_fixed.py"
FIXED_SCREEN_BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_screen_source_fixed.py"
FIX_TEST = REPO / "tests" / "test_v61_file_common_path_fix_static.py"

CANONICAL_DIR = "v61_profit_ratchet_m5_refinement"
LEGACY_DIR = "v61_small_loss_cash_target"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v61 = load(PARENT_RUNNER, "v61_parent_for_file_common_fix")
v60 = v61.v60

# Rebind both layers because V61 delegates orchestration to the V60 runner.
v61.BUILDER = FIXED_BUILDER
v61.SCREEN_BUILDER = FIXED_SCREEN_BUILDER
v60.BUILDER = FIXED_BUILDER
v60.SCREEN_BUILDER = FIXED_SCREEN_BUILDER


def archive_root(path: Path, label: str, kind: str) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    archived = path.parent / f"_v61_{kind}_previous_{stamp}_{label}"
    path.rename(archived)
    print(f"V61_COMMON_ARCHIVED kind={kind} path={archived}")


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    canonical = parent / CANONICAL_DIR
    legacy = parent / LEGACY_DIR
    archive_root(canonical, label, "canonical")
    archive_root(legacy, label, "legacy")
    canonical.mkdir(parents=True, exist_ok=True)
    print(f"V61_COMMON_ROOT_CANONICAL={canonical}")
    print(f"V61_COMMON_ROOT_LEGACY_GUARD={legacy}")
    return canonical


def listing(path: Path) -> str:
    if not path.exists():
        return "<absent>"
    items = []
    for p in sorted(path.iterdir()):
        if p.is_file():
            items.append(f"{p.name}:{p.stat().st_size}")
        else:
            items.append(f"{p.name}/")
    return ";".join(items) if items else "<empty>"


def copy_run(root: Path, label: str) -> Path:
    dst = v61.OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    expected = (
        "V61_ENTRY_EVAL.csv",
        "V61_EVENTS.csv",
        "V61_DEALS.csv",
        "V61_SHADOW_RR.csv",
        "V61_STATUS.txt",
    )
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)

    eval_file = dst / "V61_ENTRY_EVAL.csv"
    if eval_file.is_file() and eval_file.stat().st_size > 0:
        print(f"V61_EVIDENCE_ROOT_PASS label={label} root={root}")
        return dst

    legacy = root.parent / LEGACY_DIR
    print(f"V61_EVIDENCE_MISSING label={label}")
    print(f"V61_CANONICAL_LISTING={listing(root)}")
    print(f"V61_LEGACY_LISTING={listing(legacy)}")
    legacy_eval = legacy / "V61_ENTRY_EVAL.csv"
    if legacy_eval.is_file() and legacy_eval.stat().st_size > 0:
        raise RuntimeError(
            "V61_FILE_COMMON_ROOT_MISMATCH: fresh evidence appeared in legacy root "
            f"{legacy}; fixed source must write to {root}"
        )
    raise RuntimeError(
        f"V61 run {label} missing entry evaluation evidence in canonical root {root}"
    )


def parse_time(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%Y.%m.%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def monday(dt: datetime) -> datetime:
    d = dt - timedelta(days=dt.weekday())
    return datetime(d.year, d.month, d.day)


def select_directional_windows(screen_dir: Path) -> dict:
    """Choose validation windows from directional regime/setup only, never from PnL.

    Model=2 is a fast window-selection phase. Full execution feasibility belongs to
    Model=4 real-tick validation because risk-band, spread, M5 stop refinement and
    broker geometry can differ materially from the screen approximation.
    """
    path = screen_dir / "V61_ENTRY_EVAL.csv"
    weeks: dict[int, Counter[str]] = {1: Counter(), -1: Counter()}
    feasible_weeks: dict[int, Counter[str]] = {1: Counter(), -1: Counter()}
    selected_counts: Counter[int] = Counter()
    feasible_counts: Counter[int] = Counter()
    reject_counts: Counter[str] = Counter()
    rows = 0

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            rows += 1
            try:
                d = int(float(row.get("selected_direction", "0") or 0))
                feasible = int(float(row.get("feasible", "0") or 0))
                h4 = int(float(row.get("h4_trend", "0") or 0))
                h1 = int(float(row.get("h1_trend", "0") or 0))
            except ValueError:
                continue

            reject = (row.get("reject_reason", "") or "").strip()
            if reject:
                reject_counts[reject] += 1

            if d not in (1, -1) or h4 != d or h1 != d:
                continue
            dt = parse_time(row.get("time", ""))
            if dt is None:
                continue
            week = monday(dt).strftime("%Y.%m.%d")
            selected_counts[d] += 1
            weeks[d][week] += 1
            if feasible == 1:
                feasible_counts[d] += 1
                feasible_weeks[d][week] += 1

    diag = {
        "screen_rows": rows,
        "selection_basis": "directional_signal_plus_strict_h4_h1_not_pnl_not_execution_feasibility",
        "selected_direction_counts": {"long": selected_counts[1], "short": selected_counts[-1]},
        "screen_feasible_counts": {"long": feasible_counts[1], "short": feasible_counts[-1]},
        "directional_week_counts": {"long": dict(weeks[1]), "short": dict(weeks[-1])},
        "screen_feasible_week_counts": {"long": dict(feasible_weeks[1]), "short": dict(feasible_weeks[-1])},
        "reject_reason_counts": dict(reject_counts),
    }
    diag_path = v61.OUT / "V61_SCREEN_DIAGNOSTICS.json"
    diag_path.write_text(json.dumps(diag, indent=2, sort_keys=True), encoding="utf-8")
    print("V61_SCREEN_DIAGNOSTICS=" + json.dumps(diag, sort_keys=True))

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
                "screen_directional_signal_count": count,
                "screen_feasible_signal_count": feasible_weeks[d].get(start_s, 0),
                "selection_basis": "two_most_recent_strict_h4_h1_directional_weeks_not_pnl_not_screen_feasibility",
            })
            used.add(start_s)
            if len(result[key]) >= 2:
                break

    if len(result["long"]) < 2 or len(result["short"]) < 2:
        raise RuntimeError(
            "V61 screen did not find two strict H4/H1 directional weeks per side; "
            f"selected_long={selected_counts[1]} selected_short={selected_counts[-1]} "
            f"long_weeks={dict(weeks[1])} short_weeks={dict(weeks[-1])} "
            f"screen_feasible_long={feasible_counts[1]} screen_feasible_short={feasible_counts[-1]} "
            f"rejects={dict(reject_counts)}"
        )

    (v61.OUT / "V61_SELECTED_WINDOWS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V61_DIRECTIONAL_WINDOWS=" + json.dumps(result, sort_keys=True))
    return result


# Add V61-native aliases around inherited helpers so logs are no longer ambiguous.
_parent_build_sources = v60.build_sources
_parent_compile_source = v60.compile_source
_parent_write_config = v60.write_config
_parent_run_terminal = v60.run_terminal


def build_sources():
    result = _parent_build_sources()
    real, real_sha, screen, screen_sha = result
    print(f"V61_REAL_SOURCE_SHA256={real_sha}")
    print(f"V61_SCREEN_SOURCE_SHA256={screen_sha}")
    return result


def compile_source(source, source_sha, data, expert_dir, expert_name):
    result = _parent_compile_source(source, source_sha, data, expert_dir, expert_name)
    print(f"V61_COMPILE_PASS expert={expert_name} source_sha256={source_sha}")
    return result


def write_config(data, expert_name, model, from_date, to_date, label):
    result = _parent_write_config(data, expert_name, model, from_date, to_date, label)
    print(
        f"V61_CONFIG_PASS label={label} model={model} "
        f"from={from_date} to={to_date} config={result}"
    )
    return result


def run_terminal(root, ini, label, timeout):
    print(f"V61_TESTER_PASS_START label={label} root={root}")
    result = _parent_run_terminal(root, ini, label, timeout)
    print(f"V61_TESTER_PASS_DONE label={label} evidence={result}")
    return result


v60.reset_common = reset_common
v60.copy_run = copy_run
v60.build_sources = build_sources
v60.compile_source = compile_source
v60.write_config = write_config
v60.run_terminal = run_terminal
v60.select_directional_windows = select_directional_windows

v61.reset_common = reset_common
v61.copy_run = copy_run
v61.select_directional_windows = select_directional_windows


def main() -> int:
    # Validate the thin fixes before opening MetaEditor/MT5.
    v60.run([sys.executable, "-m", "py_compile", Path(__file__), FIXED_BUILDER, FIXED_SCREEN_BUILDER, FIX_TEST])
    v60.run([sys.executable, FIX_TEST])
    print("V61_FILE_COMMON_FIX_STATIC=PASS")
    print("V61_SCREEN_SELECTION_FIX=PASS")
    rc = v61.main()
    print("V61_FILE_COMMON_FIX_DONE=1")
    return rc


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
