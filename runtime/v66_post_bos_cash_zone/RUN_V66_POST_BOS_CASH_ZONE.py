#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

EXPECTED_BRANCH = "agent/v66-post-bos-cash-zone-research"
SYMBOL = "XAUUSDm"
PERIOD = "M15"
REAL_MODEL = 4

BENCHMARK_WEEKS = [
    ("week1", "2026.08.03", "2026.08.08"),
    ("week2", "2026.08.10", "2026.08.15"),
    ("week3", "2026.08.17", "2026.08.22"),
    ("week4", "2026.08.24", "2026.08.29"),
]
BEARISH_WINDOWS = [
    ("bearish1", "2026.07.13", "2026.07.18"),
    ("bearish2", "2026.06.29", "2026.07.04"),
    ("bearish3", "2026.06.22", "2026.06.27"),
    ("bearish4", "2026.06.15", "2026.06.20"),
]
DIRECTIONS = (
    ("long", 1, "V66PostBosCashZoneLong"),
    ("short", -1, "V66PostBosCashZoneShort"),
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V66"
ZIP_OUT = OUT / "v66_post_bos_cash_zone_research.zip"
BUILDER = REPO / "scripts" / "build_v66_post_bos_cash_zone_source.py"
ANALYZER = REPO / "scripts" / "analyze_v66_post_bos_cash_zone.py"
STATIC_TEST = REPO / "tests" / "test_v66_post_bos_cash_zone_static.py"
V64_RUNNER = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"
V64_FIXED = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
ADR = REPO / "docs" / "adr" / "ADR-068-v66-post-bos-cash-zone-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V66_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(cmd, *, cwd=None, timeout=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True, timeout=timeout)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def ensure_repo() -> tuple[str, str]:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before V66 research")
    return branch, head


def configure_runtime():
    runner = load(V64_RUNNER, "v64_runtime_reused_by_v66")
    fixed = load(V64_FIXED, "v64_fixed_helpers_for_v66")
    fixed.install_mt5_locator_compat(runner.base)
    runner.OUT = OUT
    runner.COMMON_DIR = "v66_post_bos_cash_zone"
    runner.DIRECTIONS = DIRECTIONS
    runner.EXPECTED_BRANCH = EXPECTED_BRANCH
    fixed.install_compile_diagnostics(runner)
    return runner


def build_sources(runner):
    OUT.mkdir(parents=True, exist_ok=True)
    built = []
    for label, direction, expert in DIRECTIONS:
        source = OUT / f"{expert}.mq5"
        run([sys.executable, BUILDER, "--output", source, "--allowed-direction", str(direction)])
        digest = runner.sha(source)
        print(f"V66_SOURCE_PASS direction={label.upper()} expert={expert} sha256={digest}")
        built.append((label, direction, expert, source, digest))
    return built


def analyze(run_dirs: list[Path]):
    analysis = OUT / "v66_analysis.json"
    summary = OUT / "V66_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in run_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", analysis, "--summary", summary]
    run(cmd)
    return analysis, summary


def package(runner, branch: str, head: str, built, compiles: list[Path], run_dirs: list[Path]) -> None:
    protocol = OUT / "V66_PROTOCOL.json"
    protocol.write_text(json.dumps({
        "branch": branch,
        "head": head,
        "symbol": SYMBOL,
        "period": PERIOD,
        "fixed_lot": 0.01,
        "actual_target_cash": 3.50,
        "planned_risk_band_cash": [0.85, 1.25],
        "emergency_loss_cash": 1.20,
        "min_risk_spread_ratio": 4.0,
        "micro_entry_ttl_minutes": 30,
        "real_tick_model": REAL_MODEL,
        "benchmark_weeks": BENCHMARK_WEEKS,
        "bearish_windows_frozen_from_v64_without_pnl_reselection": BEARISH_WINDOWS,
        "real_tick_passes": 12,
        "selection_uses_pnl": False,
        "m1_micro_stop_remains_fixed_after_bos": True,
        "post_bos_retracement_to_cash_zone": True,
        "stage2_first_arm_ttl_preserved": True,
        "m5_role": "context_structure_only",
        "tester_only": True,
        "real_money_authorized": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = OUT / "V66_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V66_POST_BOS_CASH_ZONE_EVIDENCE=1",
        f"BRANCH={branch}",
        f"HEAD={head}",
        "FIXED_LOT=0.01",
        "PLANNED_RISK_BAND=0.85,1.25",
        "EMERGENCY_LOSS=1.20",
        "ACTUAL_TARGET=3.50",
        "MIN_RISK_SPREAD_RATIO=4.0",
        "MICRO_ENTRY_TTL_MINUTES=30",
        "POST_BOS_RETRACEMENT_TO_CASH_ZONE=1",
        "M1_MICRO_STOP_FIXED_AFTER_TRIGGER=1",
        "FROZEN_V65_WINDOWS=1",
        "MODEL4_PASSES=12",
        "TESTER_ONLY=1",
        "REAL_MONEY_AUTHORIZED=0",
    ]) + "\n", encoding="utf-8")

    include = [x[3] for x in built] + compiles + [
        protocol, evidence, OUT / "v66_analysis.json", OUT / "V66_SUMMARY.txt", ADR, HANDOFF
    ]
    for rd in run_dirs:
        if rd.exists():
            include += [p for p in sorted(rd.rglob("*")) if p.is_file()]
    include = [p for p in include if p.is_file()]

    manifest = OUT / "V66_MANIFEST_SHA256.txt"
    rows = []
    for p in include:
        try:
            rel = p.relative_to(REPO)
        except ValueError:
            rel = Path("external") / p.name
        rows.append(f"{runner.sha(p)}  {rel.as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    include.append(manifest)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            try:
                arc = p.relative_to(REPO).as_posix()
            except ValueError:
                arc = f"external/{p.name}"
            zf.write(p, arc)
    with zipfile.ZipFile(ZIP_OUT) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"V66 package CRC failure first_bad={bad}")
    print(f"V66_PACKAGE_PASS=1 files={len(include)}")
    print(f"V66_ZIP={ZIP_OUT}")
    print(f"V66_ZIP_SHA256={runner.sha(ZIP_OUT)}")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = configure_runtime()
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V66_MT5_LOCATOR_COMPAT=PASS data={data} common={common} expert_dir={expert_dir}")
    print("V66_COMPILE_DIAGNOSTICS=ENABLED")

    built = build_sources(runner)
    compiles = []
    for _, _, expert, source, digest in built:
        compiles.append(runner.compile_source(source, digest, data, expert_dir, expert))

    real_dirs: list[Path] = []
    for week, from_date, to_date in BENCHMARK_WEEKS:
        for label, _, expert in DIRECTIONS:
            run_label = f"benchmark_{week}_{label}"
            root = runner.reset_common(common, run_label)
            ini = runner.write_config(data, expert, from_date, to_date, run_label, REAL_MODEL)
            real_dirs.append(runner.run_terminal(root, ini, run_label, REAL_MODEL))

    short_expert = next(x[2] for x in DIRECTIONS if x[0] == "short")
    for label, from_date, to_date in BEARISH_WINDOWS:
        run_label = f"{label}_short"
        root = runner.reset_common(common, run_label)
        ini = runner.write_config(data, short_expert, from_date, to_date, run_label, REAL_MODEL)
        real_dirs.append(runner.run_terminal(root, ini, run_label, REAL_MODEL))

    analyze(real_dirs)
    package(runner, branch, head, built, compiles, real_dirs)
    print("V66_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
