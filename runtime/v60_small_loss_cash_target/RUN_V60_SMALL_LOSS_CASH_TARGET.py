#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

EXPECTED_BRANCH = "agent/v60-small-loss-cash-target-research"
SCREEN_FROM = "2025.09.01"
SCREEN_TO = "2026.08.29"
SCREEN_MODEL = 2
REAL_MODEL = 4
SCREEN_EXPERT = "V60SmallLossCashTargetScreen"
REAL_EXPERT = "V60SmallLossCashTarget"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V60"
ZIP_OUT = OUT / "v60_small_loss_cash_target_research.zip"

V55_RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
BUILDER = REPO / "scripts" / "build_v60_small_loss_cash_target_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v60_small_loss_cash_target_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v60_small_loss_cash_target.py"
STATIC_TEST = REPO / "tests" / "test_v60_small_loss_cash_target_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
ADR = REPO / "docs" / "adr" / "ADR-062-v60-small-loss-cash-target-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(V55_RUNNER, "v55_base_for_v60")
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
        raise RuntimeError("working tree must be clean before V60 research")
    return branch, head


def build_sources() -> tuple[Path, str, Path, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    real = OUT / f"{REAL_EXPERT}.mq5"
    screen = OUT / f"{SCREEN_EXPERT}.mq5"
    run([sys.executable, BUILDER, "--output", real])
    run([sys.executable, SCREEN_BUILDER, "--output", screen])
    real_sha, screen_sha = sha(real), sha(screen)
    print(f"V60_REAL_SOURCE_SHA256={real_sha}")
    print(f"V60_SCREEN_SOURCE_SHA256={screen_sha}")
    return real, real_sha, screen, screen_sha


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
        raise RuntimeError("MetaEditor is open before V60 compile")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"])
    print(f"METAEDITOR_LAUNCH_RC expert={expert_name} rc={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, f"V60 {expert_name} MetaEditor 0/0 + EX5")
    compile_copy = OUT / f"{expert_name}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(f"V60_COMPILE_PASS expert={expert_name} summary={base.compile_summary(log)} ex5_sha256={sha(ex5)} source_sha256={source_sha}")
    return compile_copy


def write_config(data: Path, expert_name: str, model: int, from_date: str, to_date: str, label: str) -> Path:
    ini = data / "config" / f"v60_{label}.ini"
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
Symbol=XAUUSDm
Period=M15
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
    copy = OUT / f"v60_{label}.ini"
    shutil.copy2(ini, copy)
    print(f"V60_CONFIG_PASS label={label} model={model} from={from_date} to={to_date} sha256={sha(ini)}")
    return ini


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / "v60_small_loss_cash_target"
    if root.exists():
        archived = parent / f"_v60_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{label}"
        root.rename(archived)
        print(f"V60_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def copy_run(root: Path, label: str) -> Path:
    dst = OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    expected = ("V60_ENTRY_EVAL.csv", "V60_EVENTS.csv", "V60_DEALS.csv", "V60_SHADOW_RR.csv", "V60_STATUS.txt")
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)
    eval_file = dst / "V60_ENTRY_EVAL.csv"
    if not eval_file.is_file() or eval_file.stat().st_size <= 0:
        raise RuntimeError(f"V60 run {label} missing entry evaluation evidence")
    return dst


def run_terminal(root: Path, ini: Path, label: str, timeout: int) -> Path:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open before V60 tester pass")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V60 tester pass")
    print(f"RUN_V60_PASS label={label} config={ini}")
    try:
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"], timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"V60 tester timeout label={label} seconds={timeout}") from exc
    print(f"V60_MT5_LAUNCH_RC label={label} rc={cp.returncode}")
    return copy_run(root, label)


def parse_time(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%Y.%m.%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def monday(dt: datetime) -> datetime:
    d = dt - timedelta(days=dt.weekday())
    return datetime(d.year, d.month, d.day)


def select_directional_windows(screen_dir: Path) -> dict:
    path = screen_dir / "V60_ENTRY_EVAL.csv"
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
            if dt is None:
                continue
            weeks[d][monday(dt).strftime("%Y.%m.%d")] += 1

    # Pick two most recent non-overlapping weeks per side. Selection uses no PnL.
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
                "selection_basis": "two_most_recent_feasible_strict_h4_h1_aligned_weeks_not_pnl",
            })
            used.add(start_s)
            if len(result[key]) >= 2:
                break

    if len(result["long"]) < 2 or len(result["short"]) < 2:
        raise RuntimeError(
            "V60 screen did not find two feasible strict H4/H1-aligned weeks per direction; "
            f"long_weeks={dict(weeks[1])} short_weeks={dict(weeks[-1])}"
        )
    (OUT / "V60_SELECTED_WINDOWS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V60_DIRECTIONAL_WINDOWS=" + json.dumps(result, sort_keys=True))
    return result


def analyze(real_dirs: list[Path]) -> tuple[Path, Path]:
    out = OUT / "v60_analysis.json"
    summary = OUT / "V60_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in real_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", out, "--summary", summary]
    run(cmd)
    return out, summary


def package(branch: str, head: str, sources: list[Path], compiles: list[Path], screen: Path, real_dirs: list[Path]) -> None:
    evidence = OUT / "V60_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V60_SMALL_LOSS_CASH_TARGET_RESEARCH=1",
        f"branch={branch}", f"head={head}",
        "fixed_lot=0.01",
        "primary_target_cash=2.00",
        "shadow_target_cash=2.00,3.00,4.00",
        "soft_loss_cash=1.00_with_structure_or_momentum_reversal",
        "max_structural_risk_cash=1.25",
        "strict_h4_h1_alignment=1",
        "premium_discount_long_le_0.45_short_ge_0.55=1",
        f"screen_model={SCREEN_MODEL}", f"real_tick_model={REAL_MODEL}",
        f"screen_from={SCREEN_FROM}", f"screen_to={SCREEN_TO}",
        "validation_windows=2_long_plus_2_short",
        "window_selection=pnl_independent_directional_regime",
        "tester_only=1", "real_money_authorized=0", ""
    ]), encoding="utf-8")

    stage = OUT / "bundle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    files = sources + compiles + [BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST, ADR, Path(__file__).resolve(),
        OUT / "V60_SELECTED_WINDOWS.json", OUT / "v60_analysis.json", OUT / "V60_SUMMARY.txt", evidence]
    files += list(OUT.glob("v60_*.ini"))
    manifest: list[str] = []
    used: set[str] = set()
    for p in files:
        if not p.is_file():
            continue
        name = p.name if p.name not in used else "top__" + p.name
        used.add(name)
        dst = stage / name
        shutil.copy2(p, dst)
        manifest.append(f"{sha(dst)}  {name}")
    for rd in [screen] + real_dirs:
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
            raise RuntimeError(f"V60 ZIP CRC failure: {bad}")
    print(f"V60_ZIP={ZIP_OUT}")
    print(f"V60_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V60_PACKAGE_PASS=1")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, SCREEN_BUILDER, ANALYZER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    real_source, real_sha, screen_source, screen_sha = build_sources()
    real_compile = compile_source(real_source, real_sha, data, expert_dir, REAL_EXPERT)
    screen_compile = compile_source(screen_source, screen_sha, data, expert_dir, SCREEN_EXPERT)

    screen_root = reset_common(common, "screen")
    screen_ini = write_config(data, SCREEN_EXPERT, SCREEN_MODEL, SCREEN_FROM, SCREEN_TO, "screen")
    print("V60_SCREEN_PASS_START=1")
    screen_dir = run_terminal(screen_root, screen_ini, "screen", timeout=1800)
    print("V60_SCREEN_PASS_DONE=1")

    windows = select_directional_windows(screen_dir)
    real_dirs: list[Path] = []
    for key in ("long", "short"):
        for n, w in enumerate(windows[key], 1):
            label = f"real_{key}{n}_{w['from'].replace('.', '')}"
            root = reset_common(common, label)
            ini = write_config(data, REAL_EXPERT, REAL_MODEL, w["from"], w["to"], label)
            print(f"V60_REAL_TICK_PASS_START direction={w['direction']} sample={n} from={w['from']} to={w['to']}")
            rd = run_terminal(root, ini, label, timeout=5400)
            real_dirs.append(rd)
            print(f"V60_REAL_TICK_PASS_DONE direction={w['direction']} sample={n} path={rd}")

    _, summary = analyze(real_dirs)
    package(branch, head, [real_source, screen_source], [real_compile, screen_compile], screen_dir, real_dirs)
    print(summary.read_text(encoding="utf-8"), end="")
    print("V60_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
