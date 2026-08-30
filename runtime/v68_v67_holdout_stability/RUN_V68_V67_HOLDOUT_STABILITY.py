#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

EXPECTED_BRANCH = "agent/v68-v67-holdout-stability-research"
SYMBOL = "XAUUSDm"
PERIOD = "M15"
REAL_MODEL = 4
V67_ACCEPTED_HEAD = "782b44a566c772f833cb666ead1bbb21ce150b75"
V67_ACCEPTED_ZIP_SHA256 = "545b0baecba5f9ce077b692be90803623b23106b41eca43ef2728214c4d3707b"

HOLDOUT_MONTHS = [
    ("2025_09", "2025.09.01", "2025.10.01"),
    ("2025_10", "2025.10.01", "2025.11.01"),
    ("2025_11", "2025.11.01", "2025.12.01"),
    ("2025_12", "2025.12.01", "2026.01.01"),
    ("2026_01", "2026.01.01", "2026.02.01"),
    ("2026_02", "2026.02.01", "2026.03.01"),
    ("2026_03", "2026.03.01", "2026.04.01"),
    ("2026_04", "2026.04.01", "2026.05.01"),
    ("2026_05", "2026.05.01", "2026.06.01"),
]
DIRECTIONS = (
    ("long", 1, "V68V67HoldoutStabilityLong"),
    ("short", -1, "V68V67HoldoutStabilityShort"),
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V68"
ZIP_OUT = OUT / "v68_v67_holdout_stability_research.zip"
BUILDER = REPO / "scripts" / "build_v68_v67_holdout_stability_source.py"
ANALYZER = REPO / "scripts" / "analyze_v68_v67_holdout_stability.py"
STATIC_TEST = REPO / "tests" / "test_v68_v67_holdout_stability_static.py"
V64_RUNNER = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"
V64_FIXED = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
ADR = REPO / "docs" / "adr" / "ADR-070-v68-v67-holdout-stability-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V68_RECOVERY_STATE.md"


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
        raise RuntimeError("working tree must be clean before V68 research")
    return branch, head


def configure_runtime():
    runner = load(V64_RUNNER, "v64_runtime_reused_by_v68")
    fixed = load(V64_FIXED, "v64_fixed_helpers_for_v68")
    fixed.install_mt5_locator_compat(runner.base)
    runner.OUT = OUT
    runner.COMMON_DIR = "v68_v67_holdout_stability"
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
        print(f"V68_SOURCE_PASS direction={label.upper()} expert={expert} sha256={digest}")
        built.append((label, direction, expert, source, digest))
    return built


def analyze(run_dirs: list[Path]):
    analysis = OUT / "v68_analysis.json"
    summary = OUT / "V68_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in run_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", analysis, "--summary", summary]
    run(cmd)
    return analysis, summary


def package(runner, branch: str, head: str, built, compiles: list[Path], run_dirs: list[Path]) -> None:
    protocol = OUT / "V68_PROTOCOL.json"
    protocol.write_text(json.dumps({
        "branch": branch,
        "head": head,
        "symbol": SYMBOL,
        "period": PERIOD,
        "fixed_lot": 0.01,
        "actual_target_cash": 3.50,
        "planned_risk_band_cash": [0.85, 1.10],
        "emergency_loss_cash": 1.20,
        "min_risk_spread_ratio": 4.0,
        "zone_penetration_risk_cash": 0.92,
        "confirm_validity_minutes": 5,
        "real_tick_model": REAL_MODEL,
        "holdout_months": HOLDOUT_MONTHS,
        "real_tick_passes": len(HOLDOUT_MONTHS) * len(DIRECTIONS),
        "v67_accepted_head": V67_ACCEPTED_HEAD,
        "v67_accepted_zip_sha256": V67_ACCEPTED_ZIP_SHA256,
        "v67_decision_logic_changed": False,
        "only_allowed_generated_changes": ["version", "magic", "file_common_root", "trade_comment"],
        "holdout_excludes_v67_june_july_august_calibration_windows": True,
        "selection_uses_pnl": False,
        "fixed_trades_per_week_promotion_quota": False,
        "fixed_weekly_profit_promotion_quota": False,
        "long_short_lanes_evaluated_independently": True,
        "tester_only": True,
        "real_money_authorized": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = OUT / "V68_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V68_V67_HOLDOUT_STABILITY_EVIDENCE=1",
        f"BRANCH={branch}",
        f"HEAD={head}",
        f"V67_ACCEPTED_HEAD={V67_ACCEPTED_HEAD}",
        f"V67_ACCEPTED_ZIP_SHA256={V67_ACCEPTED_ZIP_SHA256}",
        "V67_DECISION_LOGIC_CHANGED=0",
        "HOLDOUT_START=2025.09.01",
        "HOLDOUT_END=2026.06.01",
        f"MODEL4_PASSES={len(HOLDOUT_MONTHS) * len(DIRECTIONS)}",
        "FIXED_LOT=0.01",
        "PLANNED_RISK_BAND=0.85,1.10",
        "ACTUAL_TARGET=3.50",
        "NO_FIXED_TRADES_PER_WEEK_PROMOTION_QUOTA=1",
        "NO_FIXED_WEEKLY_PROFIT_PROMOTION_QUOTA=1",
        "LONG_SHORT_LANES_INDEPENDENT=1",
        "TESTER_ONLY=1",
        "REAL_MONEY_AUTHORIZED=0",
    ]) + "\n", encoding="utf-8")

    include = [x[3] for x in built] + compiles + [
        protocol, evidence, OUT / "v68_analysis.json", OUT / "V68_SUMMARY.txt", ADR, HANDOFF
    ]
    for rd in run_dirs:
        if rd.exists():
            include += [p for p in sorted(rd.rglob("*")) if p.is_file()]
    include = [p for p in include if p.is_file()]

    manifest = OUT / "V68_MANIFEST_SHA256.txt"
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
            raise RuntimeError(f"V68 package CRC failure first_bad={bad}")
    print(f"V68_PACKAGE_PASS=1 files={len(include)}")
    print(f"V68_ZIP={ZIP_OUT}")
    print(f"V68_ZIP_SHA256={runner.sha(ZIP_OUT)}")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = configure_runtime()
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V68_MT5_LOCATOR_COMPAT=PASS data={data} common={common} expert_dir={expert_dir}")
    print("V68_COMPILE_DIAGNOSTICS=ENABLED")

    built = build_sources(runner)
    compiles = []
    for _, _, expert, source, digest in built:
        compiles.append(runner.compile_source(source, digest, data, expert_dir, expert))

    real_dirs: list[Path] = []
    for month, from_date, to_date in HOLDOUT_MONTHS:
        for label, _, expert in DIRECTIONS:
            run_label = f"holdout_{month}_{label}"
            root = runner.reset_common(common, run_label)
            ini = runner.write_config(data, expert, from_date, to_date, run_label, REAL_MODEL)
            real_dirs.append(runner.run_terminal(root, ini, run_label, REAL_MODEL))

    analyze(real_dirs)
    package(runner, branch, head, built, compiles, real_dirs)
    print("V68_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
