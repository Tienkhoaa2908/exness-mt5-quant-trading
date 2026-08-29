#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH = "agent/v57-fixed001-trend-smc-research"
V56_ACCEPTED_HEAD = "5a33b2fe18cbebd82447ec30f100e8ee4bb19664"
V56_ACCEPTED_ZIP_SHA256 = "a9ec9c8cb0f7402c6ffac603fc187d79ca7aa281f84e0c0fdf8310bac3a23c55"
WEEK_START_STATE_SHA256 = "7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"
FROM_DATE = "2026.08.24"
TO_DATE = "2026.08.29"
EXPERT_NAME = "V57Fixed001TrendSMC"
FIXED_LOT = 0.01

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V57"
RUN_CP = OUT / "run"
ZIP_OUT = OUT / "v57_fixed001_trend_smc_weekly_replay.zip"

V56_RUNNER = REPO / "runtime" / "v56_weekly_live_replay" / "RUN_V56_WEEKLY_LIVE_REPLAY.py"
BUILDER = REPO / "scripts" / "build_v57_fixed001_trend_smc_source.py"
ANALYZER = REPO / "scripts" / "analyze_v57_fixed001_trend_smc.py"
STATIC_TEST = REPO / "tests" / "test_v57_fixed001_trend_smc_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
SEED = HERE / "accepted_v56_week_start_state_20260824.csv"
ADR = REPO / "docs" / "adr" / "ADR-059-v57-fixed001-trend-smc-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v56 = load(V56_RUNNER, "v56_base_for_v57")
v55 = v56.v55
base = v56.base


def run(cmd, *, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


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
        raise RuntimeError("working tree must be clean before V57 replay")
    return branch, head


def verify_seed() -> None:
    if not SEED.is_file() or SEED.stat().st_size <= 0:
        raise RuntimeError(f"V57 accepted week-start seed missing: {SEED}")
    actual = sha(SEED)
    if actual != WEEK_START_STATE_SHA256:
        raise RuntimeError(f"V57 week-start seed mismatch expected={WEEK_START_STATE_SHA256} actual={actual}")
    print(f"V57_WEEK_START_STATE_PASS=1 sha256={actual}")
    print(f"V57_SEED_PROVENANCE=V56_HEAD_{V56_ACCEPTED_HEAD}")
    print(f"V57_ACCEPTED_V56_ZIP_SHA256={V56_ACCEPTED_ZIP_SHA256}")
    print("V57_SKIP_WARMUP=1")


def build_source(expert_dir: Path) -> tuple[Path, str]:
    # Rebuild the exact V56 tester-only parent from canonical V48/V55 chain, then apply
    # only V57 research transforms. No use of the live V55 mutable state.
    v56_source, _ = v56.build_source(expert_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{EXPERT_NAME}.mq5"
    run([sys.executable, BUILDER, "--source", v56_source, "--output", source])
    digest = sha(source)
    print(f"V57_SOURCE_SHA256={digest}")
    return source, digest


def compile_source(source: Path, source_sha: str, data: Path, expert_dir: Path) -> tuple[Path, Path, Path]:
    installed = expert_dir / f"{EXPERT_NAME}.mq5"
    ex5 = installed.with_suffix(".ex5")
    log = installed.with_suffix(".log")
    marker = installed.with_suffix(".compile_source_sha256")
    shutil.copy2(source, installed)
    for p in (ex5, log, marker):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it before V57 replay.")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"])
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        s = base.compile_summary(log)
        return bool(s and "0 errors, 0 warnings" in s.lower())

    base.wait_until(ready, 120, 0.5, "V57 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_copy = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(f"V57_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={sha(ex5)}")
    return installed, ex5, compile_copy


def prepare_common(common: Path) -> Path:
    root = common / "mt5_quant" / "v57_fixed001_trend_smc"
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived = root.parent / f"_v57_previous_{stamp}"
        root.rename(archived)
        print(f"V57_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    dst = root / "seed_state.csv"
    shutil.copy2(SEED, dst)
    if sha(dst) != WEEK_START_STATE_SHA256:
        raise RuntimeError("V57 common seed copy mismatch")
    return root


def write_config(data: Path) -> Path:
    ini = data / "config" / "v57_fixed001_trend_smc.ini"
    text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[Tester]\nExpert=mt5_quant\\{EXPERT_NAME}.ex5\nSymbol=XAUUSDm\nPeriod=M15\nOptimization=0\nModel=4\nFromDate={FROM_DATE}\nToDate={TO_DATE}\nForwardMode=0\nDeposit=40\nCurrency=USD\nLeverage=1:200\nExecutionMode=0\nOptimizationCriterion=0\nUseCloud=0\nVisual=0\nShutdownTerminal=1\n"""
    base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    required = (
        f"Expert=mt5_quant\\{EXPERT_NAME}.ex5",
        "Symbol=XAUUSDm",
        "Period=M15",
        "Model=4",
        f"FromDate={FROM_DATE}",
        f"ToDate={TO_DATE}",
        "Deposit=40",
        "Leverage=1:200",
        "AllowLiveTrading=1",
        "AllowDllImport=0",
        "ShutdownTerminal=1",
    )
    for token in required:
        if token not in decoded:
            raise RuntimeError(f"V57 config missing {token}")
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ini, OUT / ini.name)
    print(f"V57_CONFIG_PASS sha256={sha(ini)}")
    print("V57_TESTER_MODEL=4")
    print("V57_REAL_TICKS=1")
    print("V57_SINGLE_REAL_TICK_PASS=1")
    return ini


def newest_complete_run(runs_root: Path, started: float) -> Path | None:
    if not runs_root.is_dir():
        return None
    out: list[Path] = []
    for p in runs_root.iterdir():
        if not p.is_dir():
            continue
        req = [p / n for n in ("monthly_summary.csv", "trades.csv", "manifest.txt")]
        if not all(x.is_file() and x.stat().st_size > 0 for x in req):
            continue
        if max(x.stat().st_mtime for x in req) < started - 5:
            continue
        out.append(p)
    return max(out, key=lambda x: x.stat().st_mtime) if out else None


def run_mt5(data: Path, root: Path, ini: Path) -> Path:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it before V57 Strategy Tester replay.")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open before V57 Strategy Tester replay.")
    started = time.time()
    print(f"RUN_V57_REAL_TICKS from={FROM_DATE} to={TO_DATE} fixed_lot={FIXED_LOT:.2f}")
    cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"])
    print(f"V57_MT5_LAUNCH_RC={cp.returncode}")
    run_dir = newest_complete_run(root / "runs", started)
    if run_dir is None:
        run_dir = base.wait_until(lambda: newest_complete_run(root / "runs", started) or False, 180, 1.0, "V57 complete run artifacts")
    print(f"V57_RUN_DIR={run_dir}")
    return run_dir


def collect(root: Path, run_dir: Path) -> dict[str, Path]:
    if RUN_CP.exists():
        shutil.rmtree(RUN_CP)
    RUN_CP.mkdir(parents=True, exist_ok=True)
    for n in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        shutil.copy2(run_dir / n, RUN_CP / n)
    mapping = {
        "V55_PRODUCTION_READINESS_EVENTS.csv": "events.csv",
        "V55_PRODUCTION_READINESS_TRANSACTIONS.csv": "transactions.csv",
        "V55_PRODUCTION_READINESS_STATUS.txt": "status.txt",
        "V55_PRODUCTION_READINESS_FINAL.txt": "final.txt",
        "V57_ENTRY_EVAL.csv": "V57_ENTRY_EVAL.csv",
        "seed_state.csv": "state_after_replay.csv",
    }
    for src_name, dst_name in mapping.items():
        src = root / src_name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, RUN_CP / dst_name)
    required = [RUN_CP / "trades.csv", RUN_CP / "events.csv", RUN_CP / "transactions.csv", RUN_CP / "V57_ENTRY_EVAL.csv"]
    for p in required:
        if not p.is_file() or p.stat().st_size <= 0:
            raise RuntimeError(f"V57 required evidence missing: {p}")
    return {p.name: p for p in RUN_CP.iterdir() if p.is_file()}


def analyze() -> dict:
    analysis = OUT / "v57_analysis.json"
    summary = OUT / "V57_SUMMARY.txt"
    trade_report = OUT / "V57_TRADE_REPORT.csv"
    run([
        sys.executable, ANALYZER,
        "--trades", RUN_CP / "trades.csv",
        "--evals", RUN_CP / "V57_ENTRY_EVAL.csv",
        "--events", RUN_CP / "events.csv",
        "--transactions", RUN_CP / "transactions.csv",
        "--output", analysis,
        "--summary", summary,
        "--trade-report", trade_report,
    ])
    return json.loads(analysis.read_text(encoding="utf-8"))


def package(branch: str, head: str, source: Path, source_sha: str, compile_txt: Path, result: dict) -> None:
    evidence = OUT / "V57_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V57_FIXED001_TREND_SMC_REPLAY=1",
        f"branch={branch}",
        f"head={head}",
        f"source_sha256={source_sha}",
        f"candidate=v52_b4_or_b3_trend_bos",
        f"fixed_lot={FIXED_LOT:.2f}",
        f"from={FROM_DATE}",
        f"to={TO_DATE}",
        "tester_model=4",
        "real_ticks=1",
        "single_real_tick_pass=1",
        "warmup_rerun=0",
        f"week_start_state_sha256={WEEK_START_STATE_SHA256}",
        f"accepted_v56_zip_sha256={V56_ACCEPTED_ZIP_SHA256}",
        "tester_only=1",
        "same_week_gate_comparison_exploratory=1",
        f"actual_balanced_broker_net_usd={result.get('actual_broker_balanced_gate',{}).get('net_pnl_usd')}",
        "",
    ]), encoding="utf-8")

    files = [source, compile_txt, SEED, ADR, Path(__file__).resolve(), BUILDER, ANALYZER, STATIC_TEST,
             OUT / "v57_fixed001_trend_smc.ini", OUT / "v57_analysis.json", OUT / "V57_SUMMARY.txt", OUT / "V57_TRADE_REPORT.csv", evidence]
    files += [p for p in RUN_CP.iterdir() if p.is_file()]
    stage = OUT / "bundle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    manifest = []
    used = set()
    for p in files:
        if not p.is_file():
            continue
        name = p.name
        if name in used:
            name = f"run__{name}"
        used.add(name)
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
            raise RuntimeError(f"V57 ZIP CRC failure: {bad}")
    print(f"V57_ZIP={ZIP_OUT}")
    print(f"V57_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V57_PACKAGE_PASS=1")


def main() -> int:
    branch, head = ensure_repo()
    verify_seed()
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])
    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    source, source_sha = build_source(expert_dir)
    _, _, compile_txt = compile_source(source, source_sha, data, expert_dir)
    root = prepare_common(common)
    ini = write_config(data)
    run_dir = run_mt5(data, root, ini)
    collect(root, run_dir)
    result = analyze()
    package(branch, head, source, source_sha, compile_txt, result)
    print("V57_DONE=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
