#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH = "agent/v49-one-shot-demo-rehearsal"
V48_SOURCE_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V49"
V48_RUNNER = REPO / "runtime" / "v48_demo_paper" / "RUN_V48_DEMO_PAPER_START.py"
V49_BUILDER = REPO / "scripts" / "build_v49_one_shot_demo_rehearsal_source.py"
SUPERVISOR = HERE / "SUPERVISE_V49_ONE_SHOT.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v48 = load_module(V48_RUNNER, "v48_base_for_v49")
base = v48.base


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def run(cmd, *, cwd=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line:
            k, val = line.split("=", 1)
            out[k.strip()] = val.strip()
    return out


def v48_status(common: Path) -> dict[str, str]:
    return kv(common / "mt5_quant" / "paper" / "V48_DEMO_PAPER_STATUS.txt")


def graceful_close_mt5_if_flat(common: Path) -> None:
    if not base.task_running("terminal64.exe"):
        print("V48_TERMINAL_ALREADY_CLOSED=1")
        return

    s = v48_status(common)
    if not s or not s.get("run_id", "").strip():
        raise RuntimeError("MT5 is running but no valid V48 run_id status is available; refusing automatic terminal close")
    if s.get("position_open", "0") != "0":
        raise RuntimeError("V48 virtual position is OPEN. Leave V48 running and rerun this same one-shot only after it returns FLAT.")

    print(f"V48_FLAT_TRANSITION_PASS run_id={s.get('run_id','')}")
    print("V49_TRANSITION_GRACEFUL_MT5_CLOSE=1")
    ps = (
        "$p=Get-Process terminal64 -ErrorAction SilentlyContinue; "
        "if($p){$p | ForEach-Object { [void]$_.CloseMainWindow() }}"
    )
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], check=False)
    deadline = time.time() + 45
    while time.time() < deadline:
        if not base.task_running("terminal64.exe"):
            print("V48_TERMINAL_CLOSED_GRACEFULLY=1")
            return
        time.sleep(1)
    raise RuntimeError("MT5 did not close within 45s after graceful CloseMainWindow; close it manually and rerun the same one-shot")


def ensure_transition_flat(common: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    v48_status_path = paper / "V48_DEMO_PAPER_STATUS.txt"
    v48_state = paper / "v48_demo_paper_state.csv"
    s = kv(v48_status_path)
    if s and s.get("position_open", "0") != "0":
        raise RuntimeError("V48 virtual position is OPEN. Do not transition to V49 until V48 is FLAT.")
    if not v48_state.is_file():
        seed = v48.accepted_v46_state()
        print(f"V49_TRANSITION_SOURCE=accepted_v46_state path={seed}")
        return seed
    print(f"V49_TRANSITION_SOURCE=v48_current_state sha256={base.sha256(v48_state)} path={v48_state}")
    return v48_state


def archive_old_v49(common: Path) -> None:
    roots = [common / "mt5_quant" / "v49", common / "mt5_quant" / "paper"]
    paper_names = {
        "v49_demo_rehearsal_state.csv",
        "V49_DEMO_REHEARSAL_LATEST.txt",
        "V49_DEMO_REHEARSAL_INIT.txt",
        "V49_DEMO_REHEARSAL_STATUS.txt",
        "V49_DEMO_REHEARSAL_FINAL.txt",
    }
    found: list[Path] = []
    v49root = roots[0]
    if v49root.is_dir():
        found.extend(p for p in v49root.rglob("*") if p.is_file())
    paper = roots[1]
    if paper.is_dir():
        found.extend(p for p in paper.iterdir() if p.is_file() and p.name in paper_names)
    if not found:
        return
    archive = common / "mt5_quant" / f"_v49_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive.mkdir(parents=True, exist_ok=False)
    for src in found:
        rel = src.relative_to(common / "mt5_quant")
        dst = archive / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    print(f"V49_PREVIOUS_EVIDENCE_ARCHIVED={archive}")


def build_v49(data: Path, expert_dir: Path) -> tuple[Path, str]:
    v46 = v48.accepted_v46_source(expert_dir)
    parent = v48.build_source(v46)
    if base.sha256(parent) != V48_SOURCE_SHA:
        raise RuntimeError("frozen V48 parent identity mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "V49OneShotDemoRehearsal.mq5"
    run([sys.executable, V49_BUILDER, "--source", parent, "--output", out])
    digest = base.sha256(out)
    print(f"V49_SOURCE_SHA256={digest}")
    return out, digest


def compile_v49(source: Path, source_sha: str, data: Path) -> tuple[Path, Path]:
    root = data / "MQL5" / "Experts"
    root.mkdir(parents=True, exist_ok=True)
    installed = root / "V49OneShotDemoRehearsal.mq5"
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
        raise RuntimeError("MetaEditor is open. Close it before V49 one-shot start.")
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data / 'MQL5'}", "/log"])
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")

    def ready() -> bool:
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        s = base.compile_summary(log)
        return bool(s and "0 errors, 0 warnings" in s.lower())

    base.wait_until(ready, 120, 0.5, "V49 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha + "\n", encoding="utf-8")
    print(f"V49_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={base.sha256(ex5)}")
    return installed, ex5


def seed_v49_state(common: Path, source_state: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    paper.mkdir(parents=True, exist_ok=True)
    dst = paper / "v49_demo_rehearsal_state.csv"
    shutil.copy2(source_state, dst)
    if base.sha256(dst) != base.sha256(source_state):
        raise RuntimeError("V49 state transition copy mismatch")
    print(f"V49_STATE_SEEDED sha256={base.sha256(dst)} path={dst}")
    return dst


def write_config(data: Path) -> Path:
    ini = data / "config" / "v49_one_shot_demo_rehearsal.ini"
    text = """[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert=V49OneShotDemoRehearsal\nSymbol=XAUUSDm\nPeriod=M15\n"""
    base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    for token in ("AllowLiveTrading=1", "AllowDllImport=0", "Enabled=1", "Expert=V49OneShotDemoRehearsal", "Symbol=XAUUSDm", "Period=M15"):
        if token not in decoded:
            raise RuntimeError(f"V49 config self-check missing {token}")
    print(f"V49_CONFIG_PASS sha256={base.sha256(ini)} path={ini}")
    return ini


def wait_ready(common: Path) -> dict[str, str]:
    status = common / "mt5_quant" / "v49" / "V49_DEMO_REHEARSAL_STATUS.txt"
    deadline = time.time() + 120
    while time.time() < deadline:
        s = kv(status)
        if s:
            if (
                s.get("account_mode") == "DEMO"
                and s.get("terminal_trade_allowed") == "1"
                and s.get("mql_trade_allowed") == "1"
                and s.get("terminal_dlls_allowed") == "0"
                and s.get("real_money_authorized") == "0"
                and s.get("run_id", "").strip()
            ):
                print("V49_DEMO_REHEARSAL_READY=1")
                return s
            if s.get("halted") == "1":
                raise RuntimeError(f"V49 halted during startup reason={s.get('halt_reason','')}")
        if not base.task_running("terminal64.exe"):
            raise RuntimeError("MT5 exited before V49 READY")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V49 DEMO rehearsal READY status")


def start_supervisor() -> int:
    py = Path(sys.executable)
    pythonw = py.with_name("pythonw.exe")
    exe = pythonw if pythonw.is_file() else py
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    proc = subprocess.Popen(
        [str(exe), str(SUPERVISOR)],
        cwd=str(REPO),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        close_fds=True,
    )
    print(f"V49_SUPERVISOR_PID={proc.pid}")
    return proc.pid


def main() -> int:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"checkout {EXPECTED_BRANCH} first; actual={branch}")
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    print(f"BRANCH={branch}\nHEAD={head}")
    print("V49 MODE: Exness DEMO native orders only. REAL/non-DEMO is hard-refused by MQL OnInit.")

    run([sys.executable, SECRET_SCAN, REPO])
    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")

    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it and rerun the same one-shot command.")

    # Build + compile first while the accepted V48 runtime is still untouched.
    # A compile failure must not kill the currently running observer.
    source, source_sha = build_v49(data, expert_dir)
    compile_v49(source, source_sha, data)
    print("V49_PRETRANSITION_BUILD_COMPILE_PASS=1")

    # Only after compile acceptance do we transition the active V48 session.
    graceful_close_mt5_if_flat(common)
    transition_state = ensure_transition_flat(common)
    archive_old_v49(common)
    seed_v49_state(common, transition_state)
    ini = write_config(data)

    print("LAUNCH V49 ONE-SHOT DEMO REHEARSAL")
    proc = subprocess.Popen([str(base.TERMINAL_EXE), f"/config:{ini}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"TERMINAL_PID={proc.pid}")
    status = wait_ready(common)
    start_supervisor()

    print("V49_ONE_SHOT_STARTED=1")
    print(f"RUN_ID={status.get('run_id','')}")
    print(f"MARKET_DAYS={status.get('market_days','0')}")
    print(f"ROUND_TRIPS={status.get('round_trips','0')}")
    print("DEMO_BROKER_EXECUTION=1")
    print("REAL_MONEY_AUTHORIZED=0")
    print("Git Bash may now be closed. Keep this PC and MT5 running; the detached supervisor packages one ZIP after FINAL.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
