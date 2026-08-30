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

EXPECTED_BRANCH = "agent/v63-profit-quality-risk-zone-research"
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
    ("long", 1, "V63ProfitQualityRiskZoneLong"),
    ("short", -1, "V63ProfitQualityRiskZoneShort"),
)
SCREEN_EXPERT = "V63ProfitQualityRiskZoneScreen"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V63"
ZIP_OUT = OUT / "v63_profit_quality_risk_zone_research.zip"
BUILDER = REPO / "scripts" / "build_v63_profit_quality_risk_zone_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v63_profit_quality_risk_zone_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v63_profit_quality_risk_zone.py"
STATIC_TEST = REPO / "tests" / "test_v63_profit_quality_risk_zone_static.py"
ADR = REPO / "docs" / "adr" / "ADR-065-v63-profit-quality-risk-zone-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V63_RECOVERY_STATE.md"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V55_RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
COMMON_DIR = "v63_profit_quality_risk_zone"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(V55_RUNNER, "v55_base_for_v63")
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
        raise RuntimeError("working tree must be clean before V63 research")
    return branch, head


def build_sources() -> list[tuple[str, int, str, Path, str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    built: list[tuple[str, int, str, Path, str]] = []
    for label, direction, expert in DIRECTIONS:
        source = OUT / f"{expert}.mq5"
        run([sys.executable, BUILDER, "--output", source, "--allowed-direction", str(direction)])
        digest = sha(source)
        print(f"V63_SOURCE_PASS direction={label.upper()} expert={expert} sha256={digest}")
        built.append((label, direction, expert, source, digest))
    screen_source = OUT / f"{SCREEN_EXPERT}.mq5"
    run([sys.executable, SCREEN_BUILDER, "--output", screen_source])
    digest = sha(screen_source)
    print(f"V63_SCREEN_SOURCE_PASS expert={SCREEN_EXPERT} sha256={digest}")
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
        raise RuntimeError("MetaEditor is open before V63 compile")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"])
    print(f"V63_METAEDITOR_LAUNCH_RC expert={expert_name} rc={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, f"V63 {expert_name} MetaEditor 0/0 + EX5")
    compile_copy = OUT / f"{expert_name}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(
        f"V63_COMPILE_PASS expert={expert_name} summary={base.compile_summary(log)} "
        f"ex5_sha256={sha(ex5)} source_sha256={source_sha}"
    )
    return compile_copy


def write_config(data: Path, expert_name: str, from_date: str, to_date: str, label: str, model: int) -> Path:
    ini = data / "config" / f"v63_{label}.ini"
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
    copy = OUT / f"v63_{label}.ini"
    shutil.copy2(ini, copy)
    print(f"V63_CONFIG_PASS label={label} model={model} from={from_date} to={to_date} sha256={sha(ini)}")
    return ini


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / COMMON_DIR
    if root.exists():
        archived = parent / f"_v63_previous_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{label}"
        root.rename(archived)
        print(f"V63_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    print(f"V63_COMMON_ROOT={root}")
    return root


def copy_run(root: Path, label: str) -> Path:
    dst = OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    expected = (
        "V63_ENTRY_EVAL.csv",
        "V63_EVENTS.csv",
        "V63_DEALS.csv",
        "V63_SHADOW_RR.csv",
        "V63_STATUS.txt",
    )
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)
    eval_file = dst / "V63_ENTRY_EVAL.csv"
    if not eval_file.is_file() or eval_file.stat().st_size <= 0:
        listing = ";".join(f"{p.name}:{p.stat().st_size}" for p in sorted(root.iterdir()) if p.is_file())
        raise RuntimeError(f"V63 run {label} missing V63_ENTRY_EVAL.csv; root_listing={listing}")
    print(f"V63_EVIDENCE_PASS label={label} path={dst}")
    return dst


def run_terminal(root: Path, ini: Path, label: str, model: int, timeout: int = 3600) -> Path:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open before V63 tester pass")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V63 tester pass")
    prefix = "V63_SCREEN_PASS" if model == SCREEN_MODEL else "V63_REAL_TICK_PASS"
    print(f"{prefix}_START label={label} config={ini}")
    try:
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"], timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"V63 tester timeout label={label} seconds={timeout}") from exc
    print(f"V63_MT5_LAUNCH_RC label={label} rc={cp.returncode}")
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
    path = screen_dir / "V63_ENTRY_EVAL.csv"
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    times = [parse_time(row.get("time", "")) for row in rows]
    times = [x for x in times if x is not None]
    if len(rows) < MIN_SCREEN_ROWS or not times:
        raise RuntimeError(f"V63 screen coverage insufficient rows={len(rows)}")
    span_days = (max(times) - min(times)).days
    if span_days < MIN_SCREEN_SPAN_DAYS:
        raise RuntimeError(f"V63 screen span insufficient rows={len(rows)} span_days={span_days}")
    print(f"V63_SCREEN_COVERAGE_PASS rows={len(rows)} span_days={span_days} first={min(times)} last={max(times)}")

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
        if (
            monday not in excluded
            and c["short"] >= MIN_BEARISH_SHORT_SIGNALS
            and share >= MIN_BEARISH_SHORT_SHARE
        ):
            eligible.append(row)

    # PnL-independent and recency-oriented: choose the most recent four weeks
    # that meet the preregistered bearish density/share thresholds.
    eligible.sort(key=lambda x: x["week_start"], reverse=True)
    selected = eligible[:BEARISH_WEEK_COUNT]
    diag_path = OUT / "V63_SCREEN_DIAGNOSTICS.json"
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
    print("V63_SCREEN_DIAGNOSTICS=" + json.dumps({
        "rows": len(rows), "span_days": span_days, "eligible_count": len(eligible), "selected": selected
    }, sort_keys=True))
    if len(selected) != BEARISH_WEEK_COUNT:
        raise RuntimeError(
            f"V63 insufficient bearish weeks required={BEARISH_WEEK_COUNT} actual={len(selected)} "
            f"see={diag_path}"
        )
    selected_path = OUT / "V63_SELECTED_BEARISH_WINDOWS.json"
    selected_path.write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V63_BEARISH_WINDOWS=" + json.dumps(selected, sort_keys=True))
    return selected


def analyze(real_dirs: list[Path]) -> tuple[Path, Path]:
    analysis = OUT / "v63_analysis.json"
    summary = OUT / "V63_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in real_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", analysis, "--summary", summary]
    run(cmd)
    return analysis, summary


def package(branch: str, head: str, built, compiles: list[Path], screen_dir: Path, run_dirs: list[Path], bearish: list[dict]) -> None:
    protocol = OUT / "V63_PROTOCOL.json"
    protocol.write_text(json.dumps({
        "branch": branch,
        "head": head,
        "symbol": SYMBOL,
        "period": PERIOD,
        "screen_model": SCREEN_MODEL,
        "real_model": REAL_MODEL,
        "fixed_lot": 0.01,
        "planned_risk_band_cash": [0.60, 1.05],
        "emergency_loss_cash": 1.10,
        "primary_target_cash": 3.50,
        "profit_arm_cash": 2.0,
        "profit_lock_cash": 1.0,
        "weekly_research_goal": {"quality_trades": 3, "net_usd": 6.0, "guarantee": False},
        "benchmark_weeks": [{"label": w, "from": a, "to": b} for w, a, b in BENCHMARK_WEEKS],
        "bearish_selection": {
            "screen_from": SCREEN_FROM,
            "screen_to": SCREEN_TO,
            "min_short_signals": MIN_BEARISH_SHORT_SIGNALS,
            "min_short_share": MIN_BEARISH_SHORT_SHARE,
            "most_recent_eligible_count": BEARISH_WEEK_COUNT,
            "uses_pnl": False,
            "selected": bearish,
        },
        "benchmark_real_tick_passes": 8,
        "bearish_short_real_tick_passes": 4,
        "total_real_tick_passes": 12,
        "tester_only": True,
        "real_money_authorized": False,
        "combined_result_is_isolated_pass_sum_not_concurrent_equity": True,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = OUT / "V63_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V63_PROFIT_QUALITY_RISK_ZONE_RESEARCH=1",
        f"branch={branch}",
        f"head={head}",
        "fixed_lot=0.01",
        "planned_risk_band_cash=0.60,1.05",
        "emergency_loss_cash=1.10",
        "actual_target_cash=3.50",
        "profit_ratchet=arm_2_lock_1",
        "entry=risk_zone_then_m1_turn_with_current_regime_revalidation",
        "entry_quality_veto=di_macd_double_opposed_plus_weak_trend_chop",
        "pending_ttl=first_arm_240_minutes_not_refreshable",
        "benchmark=4_fixed_august_weeks_x_long_short",
        "bearish_short_validation=4_most_recent_pnl_independent_eligible_weeks",
        "total_model4_passes=12",
        "tester_only=1",
        "real_money_authorized=0",
        "",
    ]), encoding="utf-8")

    stage = OUT / "bundle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    files = [
        BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST, ADR, HANDOFF, Path(__file__).resolve(), protocol, evidence,
        OUT / "V63_SCREEN_DIAGNOSTICS.json", OUT / "V63_SELECTED_BEARISH_WINDOWS.json",
        OUT / "v63_analysis.json", OUT / "V63_SUMMARY.txt",
    ]
    files += [x[3] for x in built] + compiles + list(OUT.glob("v63_*.ini"))
    used: set[str] = set()
    manifest: list[str] = []
    for p in files:
        if not p.is_file():
            continue
        name = p.name if p.name not in used else "top__" + p.name
        used.add(name)
        dst = stage / name
        shutil.copy2(p, dst)
        manifest.append(f"{sha(dst)}  {name}")

    for rd in [screen_dir] + run_dirs:
        for p in rd.iterdir():
            if not p.is_file():
                continue
            name = f"{rd.name}__{p.name}"
            dst = stage / name
            shutil.copy2(p, dst)
            manifest.append(f"{sha(dst)}  {name}")
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
            raise RuntimeError(f"V63 ZIP CRC failure: {bad}")
    print(f"V63_ZIP={ZIP_OUT}")
    print(f"V63_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V63_PACKAGE_PASS=1")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    built = build_sources()
    compiles = [compile_source(source, digest, data, expert_dir, expert) for _, _, expert, source, digest in built]
    by_label = {label: (direction, expert) for label, direction, expert, _, _ in built}

    screen_root = reset_common(common, "screen")
    screen_ini = write_config(data, SCREEN_EXPERT, SCREEN_FROM, SCREEN_TO, "screen", SCREEN_MODEL)
    screen_dir = run_terminal(screen_root, screen_ini, "screen", SCREEN_MODEL, timeout=1800)
    bearish = select_bearish_weeks(screen_dir)

    run_dirs: list[Path] = []
    for week, from_date, to_date in BENCHMARK_WEEKS:
        for direction_label in ("long", "short"):
            direction, expert = by_label[direction_label]
            label = f"benchmark_{week}_{direction_label}"
            print(
                f"V63_PASS_PLAN kind=benchmark label={label} allowed_direction={direction} "
                f"from={from_date} to={to_date} model={REAL_MODEL}"
            )
            root = reset_common(common, label)
            ini = write_config(data, expert, from_date, to_date, label, REAL_MODEL)
            run_dirs.append(run_terminal(root, ini, label, REAL_MODEL))

    short_direction, short_expert = by_label["short"]
    for idx, window in enumerate(bearish, start=1):
        label = f"bearish{idx}_short"
        print(
            f"V63_PASS_PLAN kind=bearish_short label={label} allowed_direction={short_direction} "
            f"from={window['week_start']} to={window['week_end']} model={REAL_MODEL}"
        )
        root = reset_common(common, label)
        ini = write_config(data, short_expert, window["week_start"], window["week_end"], label, REAL_MODEL)
        run_dirs.append(run_terminal(root, ini, label, REAL_MODEL))

    analyze(run_dirs)
    package(branch, head, built, compiles, screen_dir, run_dirs, bearish)
    print("V63_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
