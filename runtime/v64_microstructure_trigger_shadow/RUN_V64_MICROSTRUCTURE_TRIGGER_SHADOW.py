#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

EXPECTED_BRANCH = "agent/v64-microstructure-trigger-shadow-research"
SYMBOL = "XAUUSDm"
PERIOD = "M15"
SCREEN_MODEL = 2
REAL_MODEL = 4
SCREEN_FROM = "2025.09.01"
SCREEN_TO = "2026.08.29"
MIN_SCREEN_ROWS = 5000
MIN_SCREEN_SPAN_DAYS = 250
MIN_BEARISH_SHORT_SIGNALS = 8
MIN_BEARISH_SHORT_SHARE = 0.60
BEARISH_WEEK_COUNT = 4

BENCHMARK_WEEKS = [
    ("week1", "2026.08.03", "2026.08.08"),
    ("week2", "2026.08.10", "2026.08.15"),
    ("week3", "2026.08.17", "2026.08.22"),
    ("week4", "2026.08.24", "2026.08.29"),
]
DIRECTIONS = (
    ("long", 1, "V64MicrostructureTriggerShadowLong"),
    ("short", -1, "V64MicrostructureTriggerShadowShort"),
)
SCREEN_EXPERT = "V64MicrostructureTriggerShadowScreen"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V64"
ZIP_OUT = OUT / "v64_microstructure_trigger_shadow_research.zip"
BUILDER = REPO / "scripts" / "build_v64_microstructure_trigger_shadow_source_fixed.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v64_microstructure_trigger_shadow_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v64_microstructure_trigger_shadow.py"
STATIC_TEST = REPO / "tests" / "test_v64_microstructure_trigger_shadow_static.py"
ADR = REPO / "docs" / "adr" / "ADR-066-v64-microstructure-trigger-shadow-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V64_RECOVERY_STATE.md"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V55_RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
COMMON_DIR = "v64_microstructure_trigger_shadow"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(V55_RUNNER, "v55_base_for_v64")
base = v55.base


def run(cmd, *, cwd=None, timeout=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True, timeout=timeout)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def sha(path: Path) -> str:
    return base.sha256(path)


def ensure_repo() -> tuple[str, str]:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before V64 research")
    return branch, head


def build_sources() -> list[tuple[str, int, str, Path, str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    built: list[tuple[str, int, str, Path, str]] = []
    for label, direction, expert in DIRECTIONS:
        source = OUT / f"{expert}.mq5"
        run([sys.executable, BUILDER, "--output", source, "--allowed-direction", str(direction)])
        digest = sha(source)
        print(f"V64_SOURCE_PASS direction={label.upper()} expert={expert} sha256={digest}")
        built.append((label, direction, expert, source, digest))
    screen_source = OUT / f"{SCREEN_EXPERT}.mq5"
    run([sys.executable, SCREEN_BUILDER, "--output", screen_source])
    digest = sha(screen_source)
    print(f"V64_SCREEN_SOURCE_PASS expert={SCREEN_EXPERT} sha256={digest}")
    built.append(("screen", 0, SCREEN_EXPERT, screen_source, digest))
    return built


def compile_source(source: Path, source_sha: str, data: Path, expert_dir: Path, expert_name: str) -> Path:
    expert_dir.mkdir(parents=True, exist_ok=True)
    installed = expert_dir / f"{expert_name}.mq5"
    ex5 = installed.with_suffix(".ex5")
    log = installed.with_suffix(".log")
    shutil.copy2(source, installed)
    for p in (ex5, log):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V64 compile")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"])
    print(f"V64_METAEDITOR_LAUNCH_RC expert={expert_name} rc={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, f"V64 {expert_name} MetaEditor 0/0 + EX5")
    compile_copy = OUT / f"{expert_name}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(
        f"V64_COMPILE_PASS expert={expert_name} summary={base.compile_summary(log)} "
        f"ex5_sha256={sha(ex5)} source_sha256={source_sha}"
    )
    return compile_copy


def write_config(data: Path, expert_name: str, from_date: str, to_date: str, label: str, model: int) -> Path:
    ini = data / "config" / f"v64_{label}.ini"
    text = f"""[Common]
KeepPrivate=1
NewsEnable=0
[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=1
Account=0
Profile=0
[Tester]
Expert=mt5_quant\\{expert_name}.ex5
Symbol={SYMBOL}
Period={PERIOD}
Optimization=0
Model={model}
FromDate={from_date}
ToDate={to_date}
ForwardMode=0
Deposit=40
Currency=USD
Leverage=1:200
ExecutionMode=0
OptimizationCriterion=0
UseCloud=0
Visual=0
ShutdownTerminal=1
"""
    base.write_utf16_ini(ini, text)
    copy = OUT / f"v64_{label}.ini"
    shutil.copy2(ini, copy)
    print(f"V64_CONFIG_PASS label={label} model={model} from={from_date} to={to_date} sha256={sha(ini)}")
    return ini


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / COMMON_DIR
    if root.exists():
        archived = parent / f"_v64_previous_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{label}"
        root.rename(archived)
        print(f"V64_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    print(f"V64_COMMON_ROOT={root}")
    return root


def copy_run(root: Path, label: str) -> Path:
    dst = OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    expected = (
        "V64_ENTRY_EVAL.csv",
        "V64_EVENTS.csv",
        "V64_DEALS.csv",
        "V64_SHADOW_RR.csv",
        "V64_NOISE_SHADOW.csv",
        "V64_STATUS.txt",
    )
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)
    eval_file = dst / "V64_ENTRY_EVAL.csv"
    if not eval_file.is_file() or eval_file.stat().st_size <= 0:
        listing = ";".join(f"{p.name}:{p.stat().st_size}" for p in sorted(root.iterdir()) if p.is_file())
        raise RuntimeError(f"V64 run {label} missing V64_ENTRY_EVAL.csv; root_listing={listing}")
    print(f"V64_EVIDENCE_PASS label={label} path={dst}")
    return dst


def run_terminal(root: Path, ini: Path, label: str, model: int, timeout: int = 3600) -> Path:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open before V64 tester pass")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V64 tester pass")
    prefix = "V64_SCREEN_PASS" if model == SCREEN_MODEL else "V64_REAL_TICK_PASS"
    print(f"{prefix}_START label={label} config={ini}")
    try:
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"], timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"V64 tester timeout label={label} seconds={timeout}") from exc
    print(f"V64_MT5_LAUNCH_RC label={label} rc={cp.returncode}")
    result = copy_run(root, label)
    print(f"{prefix}_DONE label={label}")
    return result


def parse_time(value: str) -> datetime | None:
    value = (value or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def int_field(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "") or 0))
    except (TypeError, ValueError):
        return 0


def select_bearish_weeks(screen_dir: Path) -> list[dict]:
    path = screen_dir / "V64_ENTRY_EVAL.csv"
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    times = [parse_time(row.get("time", "")) for row in rows]
    times = [x for x in times if x is not None]
    if len(rows) < MIN_SCREEN_ROWS or not times:
        raise RuntimeError(f"V64 screen coverage insufficient rows={len(rows)}")
    span_days = (max(times) - min(times)).days
    if span_days < MIN_SCREEN_SPAN_DAYS:
        raise RuntimeError(f"V64 screen span insufficient rows={len(rows)} span_days={span_days}")
    print(f"V64_SCREEN_COVERAGE_PASS rows={len(rows)} span_days={span_days} first={min(times)} last={max(times)}")

    counts: defaultdict[datetime, dict[str, int]] = defaultdict(lambda: {"long": 0, "short": 0})
    for row in rows:
        dt = parse_time(row.get("time", ""))
        if dt is None:
            continue
        d = int_field(row, "selected_direction")
        h4 = int_field(row, "h4_trend")
        h1 = int_field(row, "h1_trend")
        if d not in (-1, 1) or h4 != d or h1 != d:
            continue
        monday = (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        counts[monday]["long" if d > 0 else "short"] += 1

    excluded = {datetime.strptime(x[1], "%Y.%m.%d") for x in BENCHMARK_WEEKS}
    diagnostics: list[dict] = []
    eligible: list[dict] = []
    for monday, c in sorted(counts.items()):
        total = c["long"] + c["short"]
        share = c["short"] / total if total else 0.0
        row = {
            "week_start": monday.strftime("%Y.%m.%d"),
            "week_end": (monday + timedelta(days=5)).strftime("%Y.%m.%d"),
            "long_signals": c["long"],
            "short_signals": c["short"],
            "short_share": share,
            "excluded_benchmark": monday in excluded,
        }
        diagnostics.append(row)
        if monday not in excluded and c["short"] >= MIN_BEARISH_SHORT_SIGNALS and share >= MIN_BEARISH_SHORT_SHARE:
            eligible.append(row)

    eligible.sort(key=lambda x: x["week_start"], reverse=True)
    selected = eligible[:BEARISH_WEEK_COUNT]
    diag_path = OUT / "V64_SCREEN_DIAGNOSTICS.json"
    diag_path.write_text(json.dumps({
        "rows": len(rows),
        "span_days": span_days,
        "min_bearish_short_signals": MIN_BEARISH_SHORT_SIGNALS,
        "min_bearish_short_share": MIN_BEARISH_SHORT_SHARE,
        "eligible_count": len(eligible),
        "selected": selected,
        "weeks": diagnostics,
        "selection_uses_pnl": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V64_SCREEN_DIAGNOSTICS=" + json.dumps({"rows": len(rows), "span_days": span_days, "eligible_count": len(eligible), "selected": selected}, sort_keys=True))
    if len(selected) != BEARISH_WEEK_COUNT:
        raise RuntimeError(f"V64 insufficient bearish weeks required={BEARISH_WEEK_COUNT} actual={len(selected)} see={diag_path}")
    selected_path = OUT / "V64_SELECTED_BEARISH_WINDOWS.json"
    selected_path.write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V64_BEARISH_WINDOWS=" + json.dumps(selected, sort_keys=True))
    return selected


def analyze(real_dirs: list[Path]) -> tuple[Path, Path]:
    analysis = OUT / "v64_analysis.json"
    summary = OUT / "V64_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in real_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", analysis, "--summary", summary]
    run(cmd)
    return analysis, summary


def package(branch: str, head: str, built, compiles: list[Path], screen_dir: Path, run_dirs: list[Path], bearish: list[dict]) -> None:
    protocol = OUT / "V64_PROTOCOL.json"
    protocol.write_text(json.dumps({
        "branch": branch,
        "head": head,
        "symbol": SYMBOL,
        "period": PERIOD,
        "fixed_lot": 0.01,
        "planned_risk_band_cash": [0.85, 1.20],
        "emergency_loss_cash": 1.15,
        "actual_target_cash": 3.50,
        "min_risk_spread_ratio": 4.0,
        "screen_model": SCREEN_MODEL,
        "real_tick_model": REAL_MODEL,
        "benchmark_weeks": BENCHMARK_WEEKS,
        "bearish_windows": bearish,
        "real_tick_passes": 12,
        "selection_uses_pnl": False,
        "tester_only": True,
        "real_money_authorized": False,
        "noise_shadow_stops": [1.10, 1.35, 1.60],
        "noise_shadow_targets": [3.00, 3.50, 4.00],
        "noise_shadow_horizon_minutes": 480,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = OUT / "V64_EVIDENCE.txt"
    evidence.write_text(
        "\n".join([
            "V64_MICROSTRUCTURE_TRIGGER_SHADOW_EVIDENCE=1",
            f"BRANCH={branch}",
            f"HEAD={head}",
            "FIXED_LOT=0.01",
            "PLANNED_RISK_BAND=0.85,1.20",
            "EMERGENCY_LOSS=1.15",
            "ACTUAL_TARGET=3.50",
            "MIN_RISK_SPREAD_RATIO=4.0",
            "ARCHETYPES=PULLBACK_SWEEP_BOS,BREAKOUT_RETEST_BOS",
            "NOISE_SHADOW_STOPS=1.10,1.35,1.60",
            "NOISE_SHADOW_TARGETS=3.00,3.50,4.00",
            "NOISE_SHADOW_HORIZON_MINUTES=480",
            "MODEL4_PASSES=12",
            "TESTER_ONLY=1",
            "REAL_MONEY_AUTHORIZED=0",
        ]) + "\n",
        encoding="utf-8",
    )

    manifest = OUT / "V64_MANIFEST_SHA256.txt"
    include: list[Path] = []
    include += [x[3] for x in built]
    include += compiles
    include += [protocol, evidence, OUT / "V64_SCREEN_DIAGNOSTICS.json", OUT / "V64_SELECTED_BEARISH_WINDOWS.json", OUT / "v64_analysis.json", OUT / "V64_SUMMARY.txt", ADR, HANDOFF]
    for rd in [screen_dir] + run_dirs:
        if rd.exists():
            include += [p for p in sorted(rd.rglob("*")) if p.is_file()]
    include = [p for p in include if p.is_file()]
    rows = []
    for p in include:
        try:
            rel = p.relative_to(REPO)
        except ValueError:
            rel = Path("external") / p.name
        rows.append(f"{sha(p)}  {rel.as_posix()}")
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
    print(f"V64_PACKAGE_PASS=1 files={len(include)}")
    print(f"V64_ZIP={ZIP_OUT}")
    print(f"V64_ZIP_SHA256={sha(ZIP_OUT)}")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    built = build_sources()
    data = base.find_mt5_data_dir()
    common = base.find_common_files_dir(data)
    expert_dir = data / "MQL5" / "Experts" / "mt5_quant"
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    compiles: list[Path] = []
    for _, _, expert, source, digest in built:
        compiles.append(compile_source(source, digest, data, expert_dir, expert))

    screen_root = reset_common(common, "screen")
    screen_ini = write_config(data, SCREEN_EXPERT, SCREEN_FROM, SCREEN_TO, "screen", SCREEN_MODEL)
    screen_dir = run_terminal(screen_root, screen_ini, "screen", SCREEN_MODEL, timeout=1800)
    bearish = select_bearish_weeks(screen_dir)

    real_dirs: list[Path] = []
    for week, from_date, to_date in BENCHMARK_WEEKS:
        for label, _, expert in DIRECTIONS:
            run_label = f"benchmark_{week}_{label}"
            root = reset_common(common, run_label)
            ini = write_config(data, expert, from_date, to_date, run_label, REAL_MODEL)
            real_dirs.append(run_terminal(root, ini, run_label, REAL_MODEL))

    short_expert = next(x[2] for x in DIRECTIONS if x[0] == "short")
    for idx, window in enumerate(bearish, start=1):
        run_label = f"bearish{idx}_short"
        root = reset_common(common, run_label)
        ini = write_config(data, short_expert, window["week_start"], window["week_end"], run_label, REAL_MODEL)
        real_dirs.append(run_terminal(root, ini, run_label, REAL_MODEL))

    analyze(real_dirs)
    package(branch, head, built, compiles, screen_dir, real_dirs, bearish)
    print("V64_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
