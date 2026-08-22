#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_BRANCH = "agent/v46-expert-breadth-walkforward"
V46_SOURCE_SHA = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"
V45_SOURCE_SHA = "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"
V38_PARENT_SOURCE_SHA = "4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12"
FROM_DATE = "2021.01.03"
TO_DATE = "2026.08.01"
WARMUP_MONTHS = 6
EXPERT_NAME = "V46ExpertBreadthLab"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V46"
CP = OUT / "checkpoint"
DATA_CP = CP / "data"
BUNDLE = OUT / "bundle"
LOG = OUT / "v46_expert_breadth_runner.log"
ZIP_OUT = OUT / "v46_expert_breadth_walkforward.zip"

V45_BASE_PATH = REPO / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT.py"
V45_REC_PATH = REPO / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT_RECOVERABLE.py"
BUILDER = REPO / "scripts" / "build_v46_expert_breadth_source.py"
ANALYZER = REPO / "scripts" / "analyze_v46_expert_breadth.py"
TEST = REPO / "tests" / "test_v46_expert_breadth_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
PACKAGER = REPO / "scripts" / "package_research_bundle_portable.py"
BOOTSTRAP = HERE / "BOOTSTRAP_V46_EXPERT_BREADTH_ONE_SHOT_GIT_BASH.sh"
PACKAGE_ONLY = HERE / "PACKAGE_V46_EXISTING_OUTPUT_GIT_BASH.sh"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load_module(V45_BASE_PATH, "v45_base_for_v46")
rec = load_module(V45_REC_PATH, "v45_recovery_for_v46")


class Tee:
    def __init__(self, *streams): self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data); s.flush()
        return len(data)
    def flush(self):
        for s in self.streams: s.flush()


def say(msg: str) -> None:
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def run(cmd, *, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    return subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def build_v46(expert_dir: Path) -> tuple[Path, str]:
    parent = rec.get_accepted_parent(base, expert_dir)
    if base.sha256(parent) != V38_PARENT_SOURCE_SHA:
        raise RuntimeError("accepted V38 parent identity lost")
    v45_source, v45_sha = base.build_source(parent)
    if v45_sha != V45_SOURCE_SHA:
        raise RuntimeError("frozen V45 source identity lost")
    a = OUT / f"{EXPERT_NAME}.base.a.mq5"
    b = OUT / f"{EXPERT_NAME}.base.b.mq5"
    run([sys.executable, BUILDER, "--source", v45_source, "--output", a])
    run([sys.executable, BUILDER, "--source", v45_source, "--output", b])
    ha, hb = base.sha256(a), base.sha256(b)
    if ha != hb or ha != V46_SOURCE_SHA:
        raise RuntimeError(f"V46 deterministic source mismatch a={ha} b={hb}")
    print(f"V46_SOURCE_SHA={ha}")
    return a, ha


def install_and_compile(source: Path, source_sha: str, data: Path, expert_dir: Path):
    installed = expert_dir / f"{EXPERT_NAME}.mq5"
    log = installed.with_suffix(".log")
    ex5 = installed.with_suffix(".ex5")
    marker = installed.with_suffix(".compile_source_sha256")
    if not installed.is_file() or base.sha256(installed) != source_sha:
        shutil.copy2(source, installed)

    def valid_compile() -> bool:
        if not (installed.is_file() and log.is_file() and ex5.is_file() and ex5.stat().st_size > 0):
            return False
        if base.sha256(installed) != source_sha:
            return False
        summary = base.compile_summary(log)
        if not summary or not __import__("re").search(r"Result:\s*0\s+errors?,\s*0\s+warnings?", summary, flags=__import__("re").I):
            return False
        if marker.is_file() and marker.read_text(encoding="utf-8", errors="replace").strip() != source_sha:
            return False
        if not marker.is_file():
            src_mtime = installed.stat().st_mtime_ns
            if log.stat().st_mtime_ns < src_mtime or ex5.stat().st_mtime_ns < src_mtime:
                return False
        return True

    if valid_compile():
        print(f"REUSE V46 COMPILE CHECKPOINT source_sha={source_sha} summary={base.compile_summary(log)}")
    else:
        if base.task_running("metaeditor64.exe"):
            raise RuntimeError("MetaEditor is open. Close it and rerun.")
        for p in (log, ex5, marker):
            try: p.unlink()
            except FileNotFoundError: pass
        cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data / 'MQL5'}", "/log"])
        print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
        def ready():
            if not (log.is_file() and ex5.is_file() and ex5.stat().st_size > 0): return False
            s = base.compile_summary(log)
            return bool(s and __import__("re").search(r"Result:\s*0\s+errors?,\s*0\s+warnings?", s, flags=__import__("re").I))
        base.wait_until(ready, 120, 0.5, "MetaEditor V46 log 0/0 + EX5")
        marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_txt = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_txt.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(base.compile_summary(log))
    return installed, ex5, compile_txt


def collect_run(common: Path, run_dir: Path) -> None:
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        p = run_dir / name
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"V46 run artifact missing: {p}")
    manifest = (run_dir / "manifest.txt").read_text(encoding="utf-8-sig", errors="replace")
    for token in (
        "v46_expert_breadth=1",
        "v46_strategy_logic_changed=1",
        "v46_risk_changed=0",
        "v46_state_protocol=cold_start_no_future_state",
        "v46_single_tester_run=1",
        "tester_only=1",
        "native_broker_orders=0",
        "external_broker_orders=0",
        "v46_live_authorized=0",
    ):
        if token not in manifest:
            raise RuntimeError(f"V46 manifest contract missing: {token}")
    DATA_CP.mkdir(parents=True, exist_ok=True)
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        shutil.copy2(run_dir / name, DATA_CP / name)
    latest = common / "mt5_quant" / "ML_DL_FEATURE_LAKE_LATEST.txt"
    if latest.is_file(): shutil.copy2(latest, DATA_CP / latest.name)
    (CP / "DONE.txt").write_text(f"done=1\nrun_dir={run_dir}\n", encoding="utf-8")


def run_mt5_once(data: Path, common: Path, inputs: Path) -> None:
    if (CP / "DONE.txt").is_file():
        say("REUSE V46 COMPLETE CHECKPOINT — MT5 NOT RERUN")
        return
    mt5_done = CP / "MT5_DONE.json"
    if mt5_done.is_file():
        info = json.loads(mt5_done.read_text(encoding="utf-8"))
        say("RECOVER V46 COLLECTION-ONLY — MT5 NOT RERUN")
        collect_run(common, Path(info["run_dir"]))
        return
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it and rerun.")

    latest = common / "mt5_quant" / "ML_DL_FEATURE_LAKE_LATEST.txt"
    before = base.parse_kv(latest).get("run_id", "")
    state = inputs / "v30_ml_dl_feature_lake_state.csv"
    backup = OUT / "state_before_v46_backup.csv"
    had_state = state.is_file()
    if had_state: shutil.copy2(state, backup)
    try:
        if state.exists(): state.unlink()
        if state.exists(): raise RuntimeError("V46 cold-start state removal failed")
        ini = data / "config" / "v46_expert_breadth_single_run.ini"
        text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[Tester]\nExpert=mt5_quant\\{EXPERT_NAME}.ex5\nSymbol=XAUUSDm\nPeriod=M15\nOptimization=0\nModel=0\nFromDate={FROM_DATE}\nToDate={TO_DATE}\nForwardMode=0\nDeposit=40\nCurrency=USD\nLeverage=1:200\nExecutionMode=0\nOptimizationCriterion=0\nUseCloud=0\nVisual=0\nShutdownTerminal=1\n"""
        base.write_utf16_ini(ini, text)
        say(f"RUN V46 ONE EXACT MT5 TEST from={FROM_DATE} to={TO_DATE} cold_start=1 warmup_months={WARMUP_MONTHS}")
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"])
        print(f"MT5_LAUNCH_RC={cp.returncode}")

        def locate_new():
            kv = base.parse_kv(latest)
            rid, rf = kv.get("run_id", ""), kv.get("run_folder", "")
            if not rid or rid == before or not rf: return False
            run_dir = common / Path(rf.replace("\\", os.sep))
            if not run_dir.is_dir(): return False
            req = [run_dir / x for x in ("monthly_summary.csv", "trades.csv", "manifest.txt")]
            if not all(p.is_file() and p.stat().st_size > 0 for p in req): return False
            return rid, run_dir

        rid, run_dir = base.wait_until(locate_new, 300, 1.0, "new LATEST + complete V46 run artifacts")
        mt5_done.write_text(json.dumps({"run_id": rid, "run_dir": str(run_dir), "terminal_rc": cp.returncode}, indent=2), encoding="utf-8")
        DATA_CP.mkdir(parents=True, exist_ok=True)
        if state.is_file(): shutil.copy2(state, DATA_CP / "state_after_v46.csv")
        collect_run(common, run_dir)
        print(f"V46_RUN_ID={rid}")
    finally:
        if had_state and backup.is_file(): shutil.copy2(backup, state)
        elif not had_state and state.exists(): state.unlink()


def analyze_and_package(head: str, branch: str, source_sha: str, compile_txt: Path) -> None:
    analysis = OUT / "v46_expert_breadth_analysis.json"
    monthly_csv = OUT / "v46_monthly_analysis.csv"
    yearly_csv = OUT / "v46_yearly_analysis.csv"
    rolling_csv = OUT / "v46_rolling_analysis.csv"
    run([sys.executable, ANALYZER, "--run-folder", DATA_CP, "--output", analysis, "--monthly-csv", monthly_csv, "--yearly-csv", yearly_csv, "--rolling-csv", rolling_csv])
    result = json.loads(analysis.read_text(encoding="utf-8"))
    mt5info = json.loads((CP / "MT5_DONE.json").read_text(encoding="utf-8")) if (CP / "MT5_DONE.json").is_file() else {}
    evidence = OUT / "V46_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V46_EXPERT_BREADTH_SINGLE_RUN=1",
        f"head={head}", f"branch={branch}",
        f"v38_parent_source_sha256={V38_PARENT_SOURCE_SHA}",
        f"v45_parent_source_sha256={V45_SOURCE_SHA}",
        f"v46_source_sha256={source_sha}",
        f"from={FROM_DATE}", f"to={TO_DATE}", "cold_start=1", f"warmup_months={WARMUP_MONTHS}",
        f"run_id={mt5info.get('run_id','')}",
        "primary=v46_hl10_thr0p05_breadth4",
        "breadth3_and_breadth5_sensitivity_only=1",
        "tester_only=1", "native_broker_orders=0", "external_broker_orders=0", "risk_changed=0", "live_authorized=0",
        f"status={result['status']}", f"primary_pass={1 if result['primary_pass'] else 0}", ""
    ]), encoding="utf-8")

    if BUNDLE.exists(): shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)
    mapping = {
        DATA_CP / "monthly_summary.csv": "monthly_summary.csv",
        DATA_CP / "trades.csv": "trades.csv",
        DATA_CP / "manifest.txt": "manifest.txt",
        analysis: analysis.name, monthly_csv: monthly_csv.name, yearly_csv: yearly_csv.name, rolling_csv: rolling_csv.name,
        evidence: evidence.name, compile_txt: compile_txt.name,
        OUT / f"{EXPERT_NAME}.base.a.mq5": f"{EXPERT_NAME}.base.a.mq5",
        BUILDER: BUILDER.name, ANALYZER: ANALYZER.name, Path(__file__).resolve(): Path(__file__).name,
        BOOTSTRAP: BOOTSTRAP.name, PACKAGE_ONLY: PACKAGE_ONLY.name, LOG: LOG.name,
    }
    for src, name in mapping.items():
        if src.is_file(): shutil.copy2(src, BUNDLE / name)
    for optional in (DATA_CP / "ML_DL_FEATURE_LAKE_LATEST.txt", DATA_CP / "state_after_v46.csv", OUT / "state_before_v46_backup.csv"):
        if optional.is_file(): shutil.copy2(optional, BUNDLE / optional.name)
    for doc in (
        REPO / "docs" / "handover" / "CURRENT_STATE.md",
        REPO / "docs" / "handover" / "RECOVERY_PROMPT.md",
        REPO / "docs" / "handover" / "WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md",
        REPO / "docs" / "research" / "v45_multiyear_single_run_validation_results.md",
        REPO / "docs" / "research" / "v46_expert_breadth_walkforward_plan.md",
    ):
        if doc.is_file(): shutil.copy2(doc, BUNDLE / doc.name)
    run([sys.executable, PACKAGER, "--bundle", BUNDLE, "--output", ZIP_OUT])
    print("\nV46 EXPERT-BREADTH WALKFORWARD DONE")
    print(f"STATUS={result['status']}")
    print(f"PRIMARY={result['primary_candidate']}")
    print(f"PRIMARY_PASS={1 if result['primary_pass'] else 0}")
    print("LIVE_AUTHORIZED=0")
    print("UPLOAD THIS ONE ZIP:")
    print(ZIP_OUT)
    print(f"SHA256={base.sha256(ZIP_OUT)}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True); CP.mkdir(parents=True, exist_ok=True)
    logf = LOG.open("a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(sys.__stdout__, logf); sys.stderr = Tee(sys.__stderr__, logf)
    say("V46 EXPERT-BREADTH WALKFORWARD — EXACT MT5")
    print("Primary is preregistered breadth4; breadth3/5 are sensitivity only.")
    print("REAL-MONEY LIVE TRADING remains FORBIDDEN. LIVE_AUTHORIZED=0.")
    for p in (base.TERMINAL_EXE, base.METAEDITOR_EXE, V45_BASE_PATH, V45_REC_PATH, BUILDER, ANALYZER, TEST, SECRET_SCAN, PACKAGER, BOOTSTRAP, PACKAGE_ONLY):
        if not p.is_file(): raise RuntimeError(f"required file missing: {p}")
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    import numpy, pandas, sklearn
    assert numpy.__version__ == "2.3.5" and pandas.__version__ == "2.2.3" and sklearn.__version__ == "1.8.0"
    say("Static/recovery/secret gates before MetaEditor or MT5")
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, TEST, Path(__file__).resolve()])
    run([sys.executable, TEST])
    run([sys.executable, SECRET_SCAN, REPO])
    data, common, expert_dir, inputs = base.locate_mt5()
    print(f"MT5_DATA={data}")
    base.verify_tape(inputs)
    source, source_sha = build_v46(expert_dir)
    _, ex5, compile_txt = install_and_compile(source, source_sha, data, expert_dir)
    if not ex5.is_file() or ex5.stat().st_size == 0: raise RuntimeError("compiled V46 EX5 missing")
    run_mt5_once(data, common, inputs)
    analyze_and_package(head, branch, source_sha, compile_txt)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
