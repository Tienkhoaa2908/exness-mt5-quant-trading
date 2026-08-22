#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

EXPECTED_BRANCH = "agent/v45-multiyear-single-run-validation"
V30_SHA = "4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V38_ZIP_SHA = "224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
V38_PARENT_SOURCE_SHA = "4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12"
V34_TAPE_SHA = "d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
V45_SOURCE_SHA = "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"
FROM_DATE = "2022.01.01"
TO_DATE = "2026.08.01"
WARMUP_MONTHS = 6
EXPERT_NAME = "V45MultiyearValidationLab"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V45"
CP = OUT / "checkpoint"
DATA_CP = CP / "data"
LOG = OUT / "v45_multiyear_runner.log"
BUNDLE = OUT / "bundle"
ZIP_OUT = OUT / "v45_multiyear_single_run_validation.zip"

BUILDER = REPO / "scripts" / "build_v45_multiyear_validation_source.py"
ANALYZER = REPO / "scripts" / "analyze_v45_multiyear_validation.py"
TEST = REPO / "tests" / "test_v45_multiyear_validation_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
PACKAGER = REPO / "scripts" / "package_research_bundle_portable.py"
BOOTSTRAP = HERE / "BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh"
PACKAGE_ONLY = HERE / "PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh"
V38_ZIP = REPO / "runtime" / "v38_fast_harvest" / "OUTPUT_V38" / "v38_fast_harvest_exact_mt5.zip"

TERMINAL_EXE = Path(os.environ.get("MT5_TERMINAL_EXE", r"C:\Program Files\MetaTrader 5\terminal64.exe"))
METAEDITOR_EXE = Path(os.environ.get("MT5_METAEDITOR_EXE", r"C:\Program Files\MetaTrader 5\metaeditor64.exe"))

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

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def run(cmd, *, check=True, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    return subprocess.run([str(x) for x in cmd], cwd=cwd, check=check)

def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()

def task_running(image: str) -> bool:
    cp = subprocess.run(["tasklist.exe", "/FI", f"IMAGENAME eq {image}"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return image.lower() in cp.stdout.lower()

def decode_compile_log(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-16", "utf-8-sig", "cp1252"):
        try: return data.decode(enc)
        except UnicodeDecodeError: pass
    return data.decode("utf-8", errors="replace")

def compile_summary(path: Path) -> str | None:
    import re
    text = decode_compile_log(path)
    hits = re.findall(r"Result:\s*\d+\s+errors?,\s*\d+\s+warnings?", text, flags=re.I)
    return hits[-1] if hits else None

def wait_until(predicate, timeout: float, interval: float = 0.5, label: str = "condition"):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = predicate()
            if last: return last
        except Exception as exc:
            last = exc
        time.sleep(interval)
    raise RuntimeError(f"timeout waiting for {label}; last={last!r}")

def parse_kv(path: Path) -> dict[str, str]:
    out = {}
    if not path.is_file(): return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1); out[k.strip()] = v.strip()
    return out

def write_utf16_ini(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe" + text.encode("utf-16le"))

def extract_parent() -> Path:
    if not V38_ZIP.is_file(): raise RuntimeError(f"accepted V38 ZIP missing: {V38_ZIP}")
    if sha256(V38_ZIP) != V38_ZIP_SHA: raise RuntimeError("accepted V38 ZIP SHA mismatch")
    out = OUT / "V38FastHarvestLab.accepted_parent.mq5"
    with zipfile.ZipFile(V38_ZIP) as z:
        bad = z.testzip()
        if bad: raise RuntimeError(f"accepted V38 ZIP CRC failure: {bad}")
        hits = [n for n in z.namelist() if Path(n).name == "V38FastHarvestLab.base.a.mq5"]
        if len(hits) != 1: raise RuntimeError(f"expected one accepted V38 parent source, found={hits}")
        data = z.read(hits[0])
    if hashlib.sha256(data).hexdigest() != V38_PARENT_SOURCE_SHA: raise RuntimeError("accepted V38 parent source SHA mismatch")
    out.write_bytes(data)
    print(f"Accepted V38 immutable parent PASS sha256={V38_PARENT_SOURCE_SHA}")
    return out

def build_source(parent: Path) -> tuple[Path, str]:
    a = OUT / f"{EXPERT_NAME}.base.a.mq5"
    b = OUT / f"{EXPERT_NAME}.base.b.mq5"
    run([sys.executable, BUILDER, "--source", parent, "--output", a])
    run([sys.executable, BUILDER, "--source", parent, "--output", b])
    ha, hb = sha256(a), sha256(b)
    if ha != hb: raise RuntimeError(f"V45 deterministic double-build mismatch {ha} != {hb}")
    if ha != V45_SOURCE_SHA: raise RuntimeError(f"V45 frozen source SHA mismatch expected={V45_SOURCE_SHA} actual={ha}")
    text = a.read_text(encoding="utf-8-sig")
    for tok in ("MQLInfoInteger(MQL_TESTER)", "#define CANDIDATE_COUNT 23", "v45_multiyear_validation=1", "v45_strategy_logic_changed=0", "v45_risk_changed=0", "v45_state_protocol=cold_start_no_2025_state", "v45_live_authorized=0"):
        if tok not in text: raise RuntimeError(f"generated V45 MQL token missing: {tok}")
    for bad in ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell("):
        if bad in text: raise RuntimeError(f"forbidden native order path in V45 source: {bad}")
    print(f"V45_SOURCE_SHA={ha}")
    return a, ha

def locate_mt5() -> tuple[Path, Path, Path, Path]:
    appdata = Path(os.environ["APPDATA"])
    root = appdata / "MetaQuotes" / "Terminal"
    common = root / "Common" / "Files"
    matches = []
    for src in root.glob("*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5"):
        if src.is_file() and sha256(src) == V30_SHA: matches.append(src)
    if len(matches) != 1: raise RuntimeError(f"expected exactly one accepted V30 source in MT5 data folders; matches={len(matches)}")
    src = matches[0]
    data = src.parents[3]
    expert_dir = data / "MQL5" / "Experts" / "mt5_quant"
    inputs = common / "mt5_quant" / "inputs"
    expert_dir.mkdir(parents=True, exist_ok=True); inputs.mkdir(parents=True, exist_ok=True)
    return data, common, expert_dir, inputs

def verify_tape(inputs: Path) -> Path:
    tape = inputs / "v34_parallel_alpha_tape.csv"
    if not tape.is_file() or sha256(tape) != V34_TAPE_SHA:
        raise RuntimeError("verified V34 causal tape missing/hash mismatch; run V44 prerequisites first")
    if sum(1 for _ in tape.open("rb")) != 23618:
        raise RuntimeError("V34 tape row count mismatch")
    print("V34 causal tape PASS")
    return tape

def install_and_compile(source: Path, source_sha: str, data: Path, expert_dir: Path) -> tuple[Path, Path, Path]:
    installed = expert_dir / f"{EXPERT_NAME}.mq5"
    log = installed.with_suffix(".log")
    ex5 = installed.with_suffix(".ex5")
    marker = installed.with_suffix(".compile_source_sha256")
    if not installed.is_file() or sha256(installed) != source_sha:
        shutil.copy2(source, installed)

    def valid_compile() -> bool:
        if not (installed.is_file() and log.is_file() and ex5.is_file() and ex5.stat().st_size > 0): return False
        if sha256(installed) != source_sha: return False
        s = compile_summary(log)
        if not s or not __import__("re").search(r"Result:\s*0\s+errors?,\s*0\s+warnings?", s, flags=__import__("re").I): return False
        if marker.is_file():
            if marker.read_text(encoding="utf-8", errors="replace").strip() != source_sha: return False
        else:
            src_mtime = installed.stat().st_mtime_ns
            if log.stat().st_mtime_ns < src_mtime or ex5.stat().st_mtime_ns < src_mtime: return False
        return True

    if valid_compile():
        print(f"REUSE COMPILE CHECKPOINT source_sha={source_sha} summary={compile_summary(log)}")
    else:
        if task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open. Close MetaEditor completely and rerun.")
        for p in (log, ex5, marker):
            try: p.unlink()
            except FileNotFoundError: pass
        cp = subprocess.run([str(METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data / 'MQL5'}", "/log"])
        print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
        def ready():
            if not (log.is_file() and ex5.is_file() and ex5.stat().st_size > 0): return False
            s = compile_summary(log)
            return bool(s and __import__("re").search(r"Result:\s*0\s+errors?,\s*0\s+warnings?", s, flags=__import__("re").I))
        wait_until(ready, 120, 0.5, "MetaEditor log 0/0 + EX5")
        marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_txt = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_txt.write_text(decode_compile_log(log), encoding="utf-8")
    print(compile_summary(log))
    return installed, ex5, compile_txt

def collect_run(common: Path, run_dir: Path) -> None:
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        p = run_dir / name
        if not p.is_file() or p.stat().st_size == 0: raise RuntimeError(f"run artifact missing: {p}")
    manifest = (run_dir / "manifest.txt").read_text(encoding="utf-8-sig", errors="replace")
    for tok in ("v45_multiyear_validation=1", "v45_state_protocol=cold_start_no_2025_state", "v45_single_tester_run=1", "tester_only=1", "native_broker_orders=0", "external_broker_orders=0", "v45_live_authorized=0"):
        if tok not in manifest: raise RuntimeError(f"run manifest contract missing: {tok}")
    DATA_CP.mkdir(parents=True, exist_ok=True)
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        shutil.copy2(run_dir / name, DATA_CP / name)
    latest = common / "mt5_quant" / "ML_DL_FEATURE_LAKE_LATEST.txt"
    if latest.is_file(): shutil.copy2(latest, DATA_CP / latest.name)
    (CP / "DONE.txt").write_text(f"done=1\nrun_dir={run_dir}\n", encoding="utf-8")

def run_mt5_once(data: Path, common: Path, inputs: Path) -> None:
    if (CP / "DONE.txt").is_file():
        say("REUSE V45 COMPLETE CHECKPOINT — MT5 NOT RERUN")
        return

    mt5_done = CP / "MT5_DONE.json"
    if mt5_done.is_file():
        info = json.loads(mt5_done.read_text(encoding="utf-8"))
        run_dir = Path(info["run_dir"])
        say("RECOVER COLLECTION-ONLY — MT5 NOT RERUN")
        collect_run(common, run_dir)
        return

    if task_running("terminal64.exe"): raise RuntimeError("MetaTrader 5 is open. Close MT5 completely and rerun.")
    latest = common / "mt5_quant" / "ML_DL_FEATURE_LAKE_LATEST.txt"
    before = parse_kv(latest).get("run_id", "")
    state = inputs / "v30_ml_dl_feature_lake_state.csv"
    backup = OUT / "state_before_v45_backup.csv"
    had_state = state.is_file()
    if had_state: shutil.copy2(state, backup)
    try:
        if state.exists(): state.unlink()
        if state.exists(): raise RuntimeError("cold-start state removal failed")
        ini = data / "config" / "v45_multiyear_single_run.ini"
        text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[Tester]\nExpert=mt5_quant\\{EXPERT_NAME}.ex5\nSymbol=XAUUSDm\nPeriod=M15\nOptimization=0\nModel=0\nFromDate={FROM_DATE}\nToDate={TO_DATE}\nForwardMode=0\nDeposit=40\nCurrency=USD\nLeverage=1:200\nExecutionMode=0\nOptimizationCriterion=0\nUseCloud=0\nVisual=0\nShutdownTerminal=1\n"""
        write_utf16_ini(ini, text)
        say(f"RUN V45 ONE EXACT MT5 TEST from={FROM_DATE} to={TO_DATE} cold_start=1 warmup_months={WARMUP_MONTHS}")
        cp = subprocess.run([str(TERMINAL_EXE), f"/config:{ini}"])
        print(f"MT5_LAUNCH_RC={cp.returncode}")

        def locate_new():
            kv = parse_kv(latest)
            rid, rf = kv.get("run_id", ""), kv.get("run_folder", "")
            if not rid or rid == before or not rf: return False
            run_dir = common / Path(rf.replace("\\", os.sep))
            if not run_dir.is_dir(): return False
            required = [run_dir / x for x in ("monthly_summary.csv", "trades.csv", "manifest.txt")]
            if not all(p.is_file() and p.stat().st_size > 0 for p in required): return False
            return (rid, run_dir)
        rid, run_dir = wait_until(locate_new, 300, 1.0, "new LATEST + complete V45 run artifacts")
        mt5_done.write_text(json.dumps({"run_id": rid, "run_dir": str(run_dir), "terminal_rc": cp.returncode}, indent=2), encoding="utf-8")
        DATA_CP.mkdir(parents=True, exist_ok=True)
        if state.is_file(): shutil.copy2(state, DATA_CP / "state_after_v45.csv")
        collect_run(common, run_dir)
        print(f"V45_RUN_ID={rid}")
    finally:
        if had_state and backup.is_file(): shutil.copy2(backup, state)
        elif not had_state and state.exists(): state.unlink()

def analyze_and_package(head: str, branch: str, source_sha: str, compile_txt: Path) -> None:
    analysis = OUT / "v45_multiyear_analysis.json"
    monthly_csv = OUT / "v45_monthly_analysis.csv"
    yearly_csv = OUT / "v45_yearly_analysis.csv"
    rolling_csv = OUT / "v45_rolling_analysis.csv"
    run([sys.executable, ANALYZER, "--run-folder", DATA_CP, "--output", analysis, "--monthly-csv", monthly_csv, "--yearly-csv", yearly_csv, "--rolling-csv", rolling_csv, "--warmup-months", str(WARMUP_MONTHS)])
    result = json.loads(analysis.read_text(encoding="utf-8"))

    evidence = OUT / "V45_EVIDENCE.txt"
    mt5info = json.loads((CP / "MT5_DONE.json").read_text(encoding="utf-8")) if (CP / "MT5_DONE.json").is_file() else {}
    evidence.write_text("\n".join([
        "V45_MULTIYEAR_SINGLE_RUN=1", f"head={head}", f"branch={branch}", f"v38_parent_zip_sha256={V38_ZIP_SHA}", f"v38_parent_source_sha256={V38_PARENT_SOURCE_SHA}", f"v45_source_sha256={source_sha}", f"from={FROM_DATE}", f"to={TO_DATE}", "cold_start=1", f"warmup_months={WARMUP_MONTHS}", f"run_id={mt5info.get('run_id','')}", "tester_only=1", "native_broker_orders=0", "external_broker_orders=0", "risk_changed=0", "live_authorized=0", f"status={result['status']}", f"primary={result['primary_candidate']}", f"primary_pass={1 if result['primary_pass'] else 0}", f"robustness_winner={result['robustness_winner']}", f"return_winner={result['return_winner']}", ""
    ]), encoding="utf-8")

    if BUNDLE.exists(): shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True)
    mapping = {
        DATA_CP / "monthly_summary.csv": "monthly_summary.csv", DATA_CP / "trades.csv": "trades.csv", DATA_CP / "manifest.txt": "manifest.txt",
        analysis: analysis.name, monthly_csv: monthly_csv.name, yearly_csv: yearly_csv.name, rolling_csv: rolling_csv.name,
        evidence: evidence.name, compile_txt: compile_txt.name, OUT / f"{EXPERT_NAME}.base.a.mq5": f"{EXPERT_NAME}.base.a.mq5",
        BUILDER: BUILDER.name, ANALYZER: ANALYZER.name, Path(__file__).resolve(): Path(__file__).name,
        BOOTSTRAP: BOOTSTRAP.name, PACKAGE_ONLY: PACKAGE_ONLY.name, LOG: LOG.name,
    }
    for src, name in mapping.items():
        if src.is_file(): shutil.copy2(src, BUNDLE / name)
    for optional in (DATA_CP / "ML_DL_FEATURE_LAKE_LATEST.txt", DATA_CP / "state_after_v45.csv", OUT / "state_before_v45_backup.csv"):
        if optional.is_file(): shutil.copy2(optional, BUNDLE / optional.name)
    for doc in (REPO / "docs" / "handover" / "CURRENT_STATE.md", REPO / "docs" / "handover" / "RECOVERY_PROMPT.md", REPO / "docs" / "handover" / "WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md", REPO / "docs" / "research" / "v45_multiyear_single_run_validation_plan.md"):
        if doc.is_file(): shutil.copy2(doc, BUNDLE / doc.name)

    run([sys.executable, PACKAGER, "--bundle", BUNDLE, "--output", ZIP_OUT])
    print("\nV45 MULTIYEAR SINGLE-RUN DONE")
    print(f"STATUS={result['status']}")
    print(f"PRIMARY={result['primary_candidate']}")
    print(f"PRIMARY_PASS={1 if result['primary_pass'] else 0}")
    print(f"ROBUSTNESS_WINNER={result['robustness_winner']}")
    print(f"RETURN_WINNER={result['return_winner']}")
    print("LIVE_AUTHORIZED=0")
    print("UPLOAD THIS ONE ZIP:")
    print(ZIP_OUT)
    print(f"SHA256={sha256(ZIP_OUT)}")

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True); CP.mkdir(parents=True, exist_ok=True)
    logf = LOG.open("a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(sys.__stdout__, logf); sys.stderr = Tee(sys.__stderr__, logf)
    say("V45 MULTIYEAR SINGLE-RUN VALIDATION — EXACT MT5")
    print("One Strategy Tester invocation; monthly outputs are retained for later analysis.")
    print("REAL-MONEY LIVE TRADING remains FORBIDDEN. LIVE_AUTHORIZED=0.")

    for p in (TERMINAL_EXE, METAEDITOR_EXE, BUILDER, ANALYZER, TEST, SECRET_SCAN, PACKAGER, BOOTSTRAP, PACKAGE_ONLY, V38_ZIP):
        if not p.is_file(): raise RuntimeError(f"required file missing: {p}")
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch != EXPECTED_BRANCH: raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")

    import numpy, pandas, sklearn
    assert numpy.__version__ == "2.3.5" and pandas.__version__ == "2.2.3" and sklearn.__version__ == "1.8.0"
    say("Static/recovery/secret gates before MetaEditor or MT5")
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, TEST, SECRET_SCAN, PACKAGER, Path(__file__).resolve()])
    run([sys.executable, TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, inputs = locate_mt5()
    print(f"MT5_DATA={data}")
    verify_tape(inputs)
    parent = extract_parent()
    source, source_sha = build_source(parent)
    installed, ex5, compile_txt = install_and_compile(source, source_sha, data, expert_dir)
    if not ex5.is_file() or ex5.stat().st_size == 0: raise RuntimeError("compiled EX5 missing")
    run_mt5_once(data, common, inputs)
    analyze_and_package(head, branch, source_sha, compile_txt)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
