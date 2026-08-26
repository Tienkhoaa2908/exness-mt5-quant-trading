#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BRANCH = "agent/v52r-real-tick-repro"
V52_SOURCE_SHA = "676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09"
FROM_DATE = "2021.01.03"
TO_DATE = "2026.08.01"
WARMUP_MONTHS = 6
EXPERT_NAME = "V52SourceAwareTournament"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V52R"
CP = OUT / "checkpoint"
DATA_CP = CP / "data"
BUNDLE = OUT / "bundle"
ZIP_OUT = OUT / "v52r_real_tick_repro.zip"
LOG = OUT / "v52r_runner.log"

V52_RUNNER_PATH = REPO / "runtime" / "v52_source_aware" / "RUN_V52_SOURCE_AWARE_ONE_SHOT.py"
ANALYZER = REPO / "scripts" / "analyze_v52r_real_tick.py"
TEST = REPO / "tests" / "test_v52r_real_tick_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v52 = load(V52_RUNNER_PATH, "v52_parent_for_v52r")
base = v52.base
v46 = v52.v46


def run(cmd, *, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def sha(path: Path) -> str:
    return base.sha256(path)


def configure_parent_outputs() -> None:
    v52.OUT = OUT
    v52.CP = CP
    v52.DATA_CP = DATA_CP
    v52.BUNDLE = BUNDLE
    v52.ZIP_OUT = ZIP_OUT
    v52.LOG = LOG
    v52.EXPERT_NAME = EXPERT_NAME

    v46.OUT = OUT
    v46.CP = CP
    v46.DATA_CP = DATA_CP
    v46.BUNDLE = BUNDLE
    v46.ZIP_OUT = ZIP_OUT
    v46.LOG = LOG
    v46.EXPERT_NAME = EXPERT_NAME
    v46.FROM_DATE = FROM_DATE
    v46.TO_DATE = TO_DATE
    v46.WARMUP_MONTHS = WARMUP_MONTHS


def build_and_compile(data: Path, expert_dir: Path) -> tuple[Path, str, Path]:
    configure_parent_outputs()
    source, source_sha = v52.build_source(expert_dir)
    if source_sha != V52_SOURCE_SHA:
        raise RuntimeError(f"V52 frozen source identity lost expected={V52_SOURCE_SHA} actual={source_sha}")
    print(f"V52R_EXACT_V52_SOURCE_PASS=1 sha256={source_sha}")
    compile_txt = v52.compile_source(source, source_sha, data, expert_dir)
    return source, source_sha, compile_txt


def run_mt5_real_ticks(data: Path, common: Path, inputs: Path) -> None:
    if (CP / "DONE.txt").is_file():
        print("REUSE V52R COMPLETE CHECKPOINT — MT5 NOT RERUN")
        return

    mt5_done = CP / "MT5_DONE.json"
    if mt5_done.is_file():
        info = json.loads(mt5_done.read_text(encoding="utf-8"))
        print("RECOVER V52R COLLECTION-ONLY — MT5 NOT RERUN")
        v46.collect_run(common, Path(info["run_dir"]))
        return

    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it before V52R real-tick tester run.")

    latest = common / "mt5_quant" / "ML_DL_FEATURE_LAKE_LATEST.txt"
    before = base.parse_kv(latest).get("run_id", "")
    state = inputs / "v30_ml_dl_feature_lake_state.csv"
    backup = OUT / "state_before_v52r_backup.csv"
    had_state = state.is_file()
    if had_state:
        shutil.copy2(state, backup)

    try:
        if state.exists():
            state.unlink()
        if state.exists():
            raise RuntimeError("V52R cold-start state removal failed")

        ini = data / "config" / "v52r_real_tick_single_run.ini"
        text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[Tester]\nExpert=mt5_quant\\{EXPERT_NAME}.ex5\nSymbol=XAUUSDm\nPeriod=M15\nOptimization=0\nModel=4\nFromDate={FROM_DATE}\nToDate={TO_DATE}\nForwardMode=0\nDeposit=40\nCurrency=USD\nLeverage=1:200\nExecutionMode=0\nOptimizationCriterion=0\nUseCloud=0\nVisual=0\nShutdownTerminal=1\n"""
        base.write_utf16_ini(ini, text)

        print("V52R_TESTER_MODEL=4")
        print("V52R_REAL_TICKS=1")
        print(f"RUN V52R EXACT V52 SOURCE from={FROM_DATE} to={TO_DATE} cold_start=1")
        cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"])
        print(f"MT5_LAUNCH_RC={cp.returncode}")

        def locate_new():
            kv = base.parse_kv(latest)
            rid, rf = kv.get("run_id", ""), kv.get("run_folder", "")
            if not rid or rid == before or not rf:
                return False
            run_dir = common / Path(rf.replace("\\", os.sep))
            if not run_dir.is_dir():
                return False
            req = [run_dir / x for x in ("monthly_summary.csv", "trades.csv", "manifest.txt")]
            if not all(p.is_file() and p.stat().st_size > 0 for p in req):
                return False
            return rid, run_dir

        rid, run_dir = base.wait_until(
            locate_new, 900, 1.0, "new V52R LATEST + complete real-tick run artifacts"
        )
        mt5_done.write_text(
            json.dumps({"run_id": rid, "run_dir": str(run_dir), "terminal_rc": cp.returncode, "model": 4}, indent=2),
            encoding="utf-8",
        )
        DATA_CP.mkdir(parents=True, exist_ok=True)
        if state.is_file():
            shutil.copy2(state, DATA_CP / "state_after_v52r.csv")
        v46.collect_run(common, run_dir)
        print(f"V52R_RUN_ID={rid}")
    finally:
        if had_state and backup.is_file():
            shutil.copy2(backup, state)
        elif not had_state and state.exists():
            state.unlink()


def package(head: str, source_sha: str, compile_txt: Path) -> None:
    analysis = OUT / "v52r_real_tick_analysis.json"
    summary = OUT / "v52r_candidate_summary.csv"
    monthly = OUT / "v52r_monthly.csv"
    integrity = OUT / "v52r_data_integrity.json"

    run([
        sys.executable,
        ANALYZER,
        "--run-folder", DATA_CP,
        "--output", analysis,
        "--summary-csv", summary,
        "--monthly-csv", monthly,
        "--integrity-json", integrity,
    ])
    result = json.loads(analysis.read_text(encoding="utf-8"))

    evidence = OUT / "V52R_EVIDENCE.txt"
    evidence.write_text(
        "\n".join([
            "V52R_REAL_TICK_REPRO=1",
            f"head={head}",
            f"branch={BRANCH}",
            f"v52_source_sha256={source_sha}",
            f"from={FROM_DATE}",
            f"to={TO_DATE}",
            "cold_start=1",
            f"warmup_months={WARMUP_MONTHS}",
            "tester_model=4",
            "real_ticks=1",
            "alpha_logic_changed_from_v52=0",
            "native_broker_orders=0",
            "external_broker_orders=0",
            "risk_changed=0",
            f"data_integrity_pass={1 if result.get('data_integrity', {}).get('pass') else 0}",
            f"status={result.get('status')}",
            f"selected={result.get('selected_candidate')}",
            "",
        ]),
        encoding="utf-8",
    )

    files = [
        DATA_CP / "monthly_summary.csv",
        DATA_CP / "trades.csv",
        DATA_CP / "manifest.txt",
        analysis,
        summary,
        monthly,
        integrity,
        evidence,
        compile_txt,
        OUT / f"{EXPERT_NAME}.base.a.mq5",
        ANALYZER,
        Path(__file__).resolve(),
        TEST,
        LOG,
        REPO / "scripts" / "build_v52_source_aware_source.py",
        REPO / "docs" / "adr" / "ADR-052-source-aware-breadth3-opportunity-lane.md",
        REPO / "docs" / "adr" / "ADR-053-real-tick-reproducibility-gate.md",
        REPO / "docs" / "research" / "v52_source_aware_results_2026-08-26.md",
        REPO / "docs" / "research" / "v52r_real_tick_repro_plan.md",
        REPO / "docs" / "handover" / "CURRENT_STATE.md",
        REPO / "docs" / "handover" / "RECOVERY_PROMPT.md",
    ]

    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True, exist_ok=True)
    used = set()
    manifest_lines = []
    for p in files:
        if not p.is_file():
            continue
        name = p.name
        if name in used:
            raise RuntimeError(f"duplicate bundle basename: {name}")
        used.add(name)
        dst = BUNDLE / name
        shutil.copy2(p, dst)
        manifest_lines.append(f"{sha(dst)}  {name}")

    (BUNDLE / "bundle_manifest_sha256.txt").write_text(
        "\n".join(sorted(manifest_lines)) + "\n", encoding="utf-8"
    )

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(BUNDLE.iterdir()):
            if p.is_file():
                z.write(p, p.name)
    with zipfile.ZipFile(ZIP_OUT) as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure {bad}")

    print(f"STATUS={result.get('status')}")
    print(f"SELECTED={result.get('selected_candidate')}")
    print(f"V52R_ZIP={ZIP_OUT}")
    print(f"V52R_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V52R_PACKAGE_PASS=1")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CP.mkdir(parents=True, exist_ok=True)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch != BRANCH:
        raise RuntimeError(f"wrong branch expected={BRANCH} actual={branch}")

    print("V52R: exact V52 source, Model=4 real ticks, fail-closed data-integrity gate")
    run([sys.executable, "-m", "py_compile", ANALYZER, TEST, Path(__file__).resolve()])
    run([sys.executable, TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, inputs = base.locate_mt5()
    print(f"MT5_DATA={data}")
    base.verify_tape(inputs)
    source, source_sha, compile_txt = build_and_compile(data, expert_dir)
    if sha(source) != V52_SOURCE_SHA:
        raise RuntimeError("exact V52 source changed after compile")

    run_mt5_real_ticks(data, common, inputs)
    package(head, source_sha, compile_txt)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
