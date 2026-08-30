#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH = "agent/v62-direction-isolated-entry-refinement-research"
MODEL = 4
SYMBOL = "XAUUSDm"
PERIOD = "M15"
WEEKS = [
    ("week1", "2026.08.03", "2026.08.08"),
    ("week2", "2026.08.10", "2026.08.15"),
    ("week3", "2026.08.17", "2026.08.22"),
    ("week4", "2026.08.24", "2026.08.29"),
]
DIRECTIONS = (
    ("long", 1, "V62DirectionIsolatedEntryRefinementLong"),
    ("short", -1, "V62DirectionIsolatedEntryRefinementShort"),
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V62"
ZIP_OUT = OUT / "v62_direction_isolated_entry_refinement_month.zip"
BUILDER = REPO / "scripts" / "build_v62_direction_isolated_entry_refinement_source.py"
ANALYZER = REPO / "scripts" / "analyze_v62_direction_isolated_entry_refinement.py"
STATIC_TEST = REPO / "tests" / "test_v62_direction_isolated_entry_refinement_static.py"
ADR = REPO / "docs" / "adr" / "ADR-064-v62-direction-isolated-entry-refinement-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V62_RECOVERY_STATE.md"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V55_RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
COMMON_DIR = "v62_direction_isolated_entry_refinement"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(V55_RUNNER, "v55_base_for_v62")
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
        raise RuntimeError("working tree must be clean before V62 research")
    return branch, head


def build_sources() -> list[tuple[str, int, str, Path, str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    built = []
    for label, direction, expert in DIRECTIONS:
        source = OUT / f"{expert}.mq5"
        run([sys.executable, BUILDER, "--output", source, "--allowed-direction", str(direction)])
        digest = sha(source)
        print(f"V62_SOURCE_PASS direction={label.upper()} expert={expert} sha256={digest}")
        built.append((label, direction, expert, source, digest))
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
        raise RuntimeError("MetaEditor is open before V62 compile")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"])
    print(f"V62_METAEDITOR_LAUNCH_RC expert={expert_name} rc={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, f"V62 {expert_name} MetaEditor 0/0 + EX5")
    compile_copy = OUT / f"{expert_name}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(
        f"V62_COMPILE_PASS expert={expert_name} summary={base.compile_summary(log)} "
        f"ex5_sha256={sha(ex5)} source_sha256={source_sha}"
    )
    return compile_copy


def write_config(data: Path, expert_name: str, from_date: str, to_date: str, label: str) -> Path:
    ini = data / "config" / f"v62_{label}.ini"
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
Model={MODEL}
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
    copy = OUT / f"v62_{label}.ini"
    shutil.copy2(ini, copy)
    print(f"V62_CONFIG_PASS label={label} model={MODEL} from={from_date} to={to_date} sha256={sha(ini)}")
    return ini


def reset_common(common: Path, label: str) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / COMMON_DIR
    if root.exists():
        archived = parent / f"_v62_previous_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{label}"
        root.rename(archived)
        print(f"V62_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    print(f"V62_COMMON_ROOT={root}")
    return root


def copy_run(root: Path, label: str) -> Path:
    dst = OUT / label
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    expected = (
        "V62_ENTRY_EVAL.csv",
        "V62_EVENTS.csv",
        "V62_DEALS.csv",
        "V62_SHADOW_RR.csv",
        "V62_STATUS.txt",
    )
    for name in expected:
        src = root / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dst / name)
    eval_file = dst / "V62_ENTRY_EVAL.csv"
    if not eval_file.is_file() or eval_file.stat().st_size <= 0:
        listing = ";".join(f"{p.name}:{p.stat().st_size}" for p in sorted(root.iterdir()) if p.is_file())
        raise RuntimeError(f"V62 run {label} missing V62_ENTRY_EVAL.csv; root_listing={listing}")
    print(f"V62_EVIDENCE_PASS label={label} path={dst}")
    return dst


def run_terminal(root: Path, ini: Path, label: str, timeout: int = 3600) -> Path:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open before V62 tester pass")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V62 tester pass")
    print(f"V62_REAL_TICK_PASS_START label={label} config={ini}")
    try:
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"], timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"V62 tester timeout label={label} seconds={timeout}") from exc
    print(f"V62_MT5_LAUNCH_RC label={label} rc={cp.returncode}")
    result = copy_run(root, label)
    print(f"V62_REAL_TICK_PASS_DONE label={label}")
    return result


def analyze(real_dirs: list[Path]) -> tuple[Path, Path]:
    analysis = OUT / "v62_analysis.json"
    summary = OUT / "V62_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for rd in real_dirs:
        cmd += ["--run-dir", rd]
    cmd += ["--output", analysis, "--summary", summary]
    run(cmd)
    return analysis, summary


def package(branch: str, head: str, built, compiles: list[Path], run_dirs: list[Path]) -> None:
    protocol = OUT / "V62_PROTOCOL.json"
    protocol.write_text(json.dumps({
        "branch": branch,
        "head": head,
        "symbol": SYMBOL,
        "period": PERIOD,
        "model": MODEL,
        "fixed_lot": 0.01,
        "min_structural_risk_cash": 0.75,
        "max_structural_risk_cash": 1.25,
        "primary_target_cash": 3.0,
        "profit_arm_cash": 2.0,
        "profit_lock_cash": 1.0,
        "weeks": [{"label": w, "from": a, "to": b} for w, a, b in WEEKS],
        "passes": [f"{w}_{d}" for w, _, _ in WEEKS for d, _, _ in DIRECTIONS],
        "direction_isolated": True,
        "entry_refinement": "M15 arm -> closed M5 retest -> closed M1 turn -> structural-risk feasibility",
        "tester_only": True,
        "real_money_authorized": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = OUT / "V62_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT_RESEARCH=1",
        f"branch={branch}",
        f"head={head}",
        "fixed_lot=0.01",
        "risk_band_cash=0.75,1.25",
        "target_cash=3.00",
        "profit_ratchet=arm_2_lock_1",
        "model=4_real_ticks",
        "month=four_complete_weeks_2026_08_03_to_2026_08_29",
        "passes=8_direction_isolated",
        "combined_result_is_sum_of_isolated_passes_not_concurrent_portfolio",
        "tester_only=1",
        "real_money_authorized=0",
        "",
    ]), encoding="utf-8")

    stage = OUT / "bundle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    files = [BUILDER, ANALYZER, STATIC_TEST, ADR, HANDOFF, Path(__file__).resolve(), protocol, evidence,
             OUT / "v62_analysis.json", OUT / "V62_SUMMARY.txt"]
    files += [x[3] for x in built] + compiles + list(OUT.glob("v62_*.ini"))
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
    for rd in run_dirs:
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
            raise RuntimeError(f"V62 ZIP CRC failure: {bad}")
    print(f"V62_ZIP={ZIP_OUT}")
    print(f"V62_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V62_PACKAGE_PASS=1")


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    built = build_sources()
    compiles = [compile_source(source, digest, data, expert_dir, expert) for _, _, expert, source, digest in built]
    by_label = {label: (direction, expert) for label, direction, expert, _, _ in built}

    run_dirs: list[Path] = []
    for week, from_date, to_date in WEEKS:
        for direction_label in ("long", "short"):
            direction, expert = by_label[direction_label]
            label = f"{week}_{direction_label}"
            print(
                f"V62_PASS_PLAN label={label} allowed_direction={direction} "
                f"from={from_date} to={to_date} model={MODEL}"
            )
            root = reset_common(common, label)
            ini = write_config(data, expert, from_date, to_date, label)
            run_dirs.append(run_terminal(root, ini, label))

    analyze(run_dirs)
    package(branch, head, built, compiles, run_dirs)
    print("V62_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
