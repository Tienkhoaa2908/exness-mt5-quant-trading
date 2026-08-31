#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"
FROZEN_V69_RESEARCH_HEAD = "0569701be7846605ac01f94d8b5fc4ec2a6f8dd1"
ACCEPTED_V69_EVIDENCE_SHA256 = "e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb"
FROZEN_FORWARD_SOURCE_SHA256 = "0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93"
EXPERT_NAME = "V69FrozenForwardSmokeDashboardLong"
SYMBOL = "XAUUSDm"
PERIOD = "M15"
COMMON_DIR = "v69_frozen_forward_demo"
SMOKE_MIN_CLOSED_TRADES = 2
SMOKE_HARD_CAP_HOURS = 48

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_ONE_SHOT"
BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_dashboard_source.py"
FORWARD_STATIC = REPO / "tests" / "test_v69_frozen_forward_demo_static.py"
DASHBOARD_STATIC = REPO / "tests" / "test_v69_frozen_forward_demo_dashboard_static.py"
ONE_SHOT_STATIC = REPO / "tests" / "test_v69_one_shot_prospective_demo_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V69_RUNNER = REPO / "runtime" / "v69_confirm_separation_retest" / "RUN_V69_CONFIRM_SEPARATION_RETEST.py"
SUPERVISOR = HERE / "SUPERVISE_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def run(cmd, *, cwd=None) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").replace("\\r\\n", "\n").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def ensure_repo() -> tuple[str, str]:
    expected_head = os.environ.get("V69_ONE_SHOT_EXPECTED_HEAD", "").strip()
    if not expected_head:
        raise RuntimeError("V69_ONE_SHOT_EXPECTED_HEAD is required")
    origin = capture(["git", "remote", "get-url", "origin"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected_head}")
    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError("wrong repository")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected_head:
        raise RuntimeError(f"wrong HEAD expected={expected_head} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return branch, head


def configure_runtime():
    v69 = load(V69_RUNNER, "v69_runtime_for_one_shot_forward")
    runner = v69.configure_runtime()
    runner.OUT = OUT
    return runner


def archive_forward_common(common: Path) -> Path:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / COMMON_DIR
    if root.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
        archive = parent / f"_v69_forward_previous_{stamp}"
        root.rename(archive)
        print(f"V69_PREVIOUS_FORWARD_ARCHIVED={archive}")
    root.mkdir(parents=True, exist_ok=False)
    return root


def build_compile_install(runner, data: Path, expert_dir: Path) -> tuple[Path, Path, str, str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    source_a = OUT / f"{EXPERT_NAME}.base.a.mq5"
    source_b = OUT / f"{EXPERT_NAME}.base.b.mq5"
    run([sys.executable, BUILDER, "--output", source_a])
    run([sys.executable, BUILDER, "--output", source_b])
    sha_a, sha_b = runner.sha(source_a), runner.sha(source_b)
    if sha_a != sha_b:
        raise RuntimeError(f"dashboard deterministic build mismatch a={sha_a} b={sha_b}")
    print(f"V69_FROZEN_PARENT_SOURCE_SHA256={FROZEN_FORWARD_SOURCE_SHA256}")
    print(f"V69_DASHBOARD_SOURCE_SHA256={sha_a}")
    print("V69_DASHBOARD_UI_ONLY=1")
    print("V69_STRATEGY_CHANGED=0")

    compile_log = runner.compile_source(source_a, sha_a, data, expert_dir, EXPERT_NAME)
    installed_source = expert_dir / f"{EXPERT_NAME}.mq5"
    installed_ex5 = expert_dir / f"{EXPERT_NAME}.ex5"
    if not installed_source.is_file() or runner.sha(installed_source) != sha_a:
        raise RuntimeError("installed dashboard MQ5 identity mismatch")
    if not installed_ex5.is_file() or installed_ex5.stat().st_size <= 0:
        raise RuntimeError("compiled dashboard EX5 missing")
    ex5_sha = runner.sha(installed_ex5)

    startup_source = Path(data) / "MQL5" / "Experts" / f"{EXPERT_NAME}.mq5"
    startup_ex5 = startup_source.with_suffix(".ex5")
    shutil.copy2(installed_source, startup_source)
    shutil.copy2(installed_ex5, startup_ex5)
    if runner.sha(startup_source) != sha_a or runner.sha(startup_ex5) != ex5_sha:
        raise RuntimeError("startup dashboard expert byte-copy verification failed")

    print(f"V69_DASHBOARD_EX5_SHA256={ex5_sha}")
    print("V69_STARTUP_EXPERT_COPY_PASS=1")
    return startup_source, startup_ex5, sha_a, ex5_sha, compile_log


def write_start_config(runner, data: Path) -> Path:
    ini = Path(data) / "config" / "v69_frozen_forward_one_shot.ini"
    text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert={EXPERT_NAME}\nSymbol={SYMBOL}\nPeriod={PERIOD}\n"""
    runner.base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    for token in (
        "AllowLiveTrading=1", "AllowDllImport=0", "Enabled=1",
        f"Expert={EXPERT_NAME}", f"Symbol={SYMBOL}", f"Period={PERIOD}",
    ):
        if token not in decoded:
            raise RuntimeError(f"startup config self-check missing {token}")
    print(f"V69_START_CONFIG_SHA256={runner.sha(ini)}")
    return ini


def wait_ready(runner, root: Path, proc: subprocess.Popen) -> dict[str, str]:
    status_path = root / "V64_STATUS.txt"
    heartbeat_path = root / "V69_DASHBOARD_HEARTBEAT.txt"
    deadline = time.time() + 180
    while time.time() < deadline:
        s = parse_kv(status_path)
        hb = parse_kv(heartbeat_path)
        if s and hb:
            state = s.get("state", "")
            ticks = int(hb.get("tick_count", "0") or 0)
            if (
                state == "READY"
                and s.get("symbol") == SYMBOL
                and s.get("fixed_lot") in {"0.01", "0.010"}
                and hb.get("symbol") == SYMBOL
                and hb.get("period") == "PERIOD_M15"
                and hb.get("account_mode") == "0"
                and hb.get("real_money_authorized") == "0"
                and ticks > 0
            ):
                print(f"V69_FORWARD_DEMO_READY=1 ticks={ticks}")
                print("V69_RUNTIME_SMOKE_VERIFIED=1")
                return {"status": s, "heartbeat": hb}
            if state == "STOPPED":
                raise RuntimeError(f"V69 stopped during startup detail={s.get('detail','')}")
        if proc.poll() is not None and not runner.base.task_running("terminal64.exe"):
            raise RuntimeError(f"MT5 exited before V69 READY rc={proc.returncode}")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V69 READY + live tick heartbeat on Exness DEMO")


def start_supervisor(session_path: Path) -> int:
    py = Path(sys.executable)
    pythonw = py.with_name("pythonw.exe")
    exe = pythonw if pythonw.is_file() else py
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
        )
    proc = subprocess.Popen(
        [str(exe), str(SUPERVISOR), "--session", str(session_path)],
        cwd=str(REPO), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags, close_fds=True,
    )
    print(f"V69_FORWARD_SUPERVISOR_PID={proc.pid}")
    return proc.pid


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, FORWARD_STATIC, DASHBOARD_STATIC, ONE_SHOT_STATIC, SUPERVISOR, Path(__file__)])
    run([sys.executable, FORWARD_STATIC])
    run([sys.executable, DASHBOARD_STATIC])
    run([sys.executable, ONE_SHOT_STATIC])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = configure_runtime()
    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError(
            "MetaTrader 5 is already running. Close MT5 once, then rerun this SAME one-shot command; "
            "the runner will relaunch and pin the dashboard automatically."
        )
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is already running. Close MetaEditor once, then rerun this SAME one-shot command.")

    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    startup_source, startup_ex5, source_sha, ex5_sha, compile_log = build_compile_install(runner, Path(data), expert_dir)
    root = archive_forward_common(Path(common))
    ini = write_start_config(runner, Path(data))

    launched_at = datetime.now(timezone.utc)
    print("LAUNCH_V69_FROZEN_FORWARD_SMOKE_DASHBOARD=1")
    proc = subprocess.Popen([str(runner.base.TERMINAL_EXE), f"/config:{ini}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"TERMINAL_PID={proc.pid}")
    ready = wait_ready(runner, root, proc)

    session = {
        "protocol": "v69_frozen_forward_smoke_dashboard_v2",
        "started_at_utc": launched_at.isoformat(),
        "branch": branch,
        "head": head,
        "frozen_v69_research_head": FROZEN_V69_RESEARCH_HEAD,
        "accepted_v69_evidence_sha256": ACCEPTED_V69_EVIDENCE_SHA256,
        "frozen_parent_source_sha256": FROZEN_FORWARD_SOURCE_SHA256,
        "dashboard_source_sha256": source_sha,
        "dashboard_ex5_sha256": ex5_sha,
        "dashboard_ui_only": True,
        "startup_source": str(startup_source),
        "startup_ex5": str(startup_ex5),
        "compile_log": str(compile_log),
        "file_common_root": str(root),
        "symbol": SYMBOL,
        "period": PERIOD,
        "direction": "LONG_ONLY",
        "demo_only": True,
        "real_money_authorized": False,
        "short_enabled": False,
        "strategy_changed": False,
        "strategy_threshold_tuning_allowed": False,
        "smoke_min_closed_trades": SMOKE_MIN_CLOSED_TRADES,
        "smoke_hard_cap_hours": SMOKE_HARD_CAP_HOURS,
        "real_money_auto_promotion": False,
        "ready_evidence": ready,
    }
    session_path = OUT / "V69_ONE_SHOT_SESSION.json"
    session_path.write_text(json.dumps(session, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    start_supervisor(session_path)

    print("V69_ONE_SHOT_STARTED=1")
    print("V69_CHART_DASHBOARD_PINNED=1")
    print(f"V69_QUICK_REVIEW_MIN_CLOSED_TRADES={SMOKE_MIN_CLOSED_TRADES}")
    print(f"V69_QUICK_REVIEW_HARD_CAP_HOURS={SMOKE_HARD_CAP_HOURS}")
    print("V69_FORWARD_DIRECTION=LONG_ONLY")
    print("V69_FORWARD_DEMO_ONLY=1")
    print("V69_FORWARD_REAL_MONEY_AUTHORIZED=0")
    print("V69_FORWARD_SHORT_ENABLED=0")
    print("V69_STRATEGY_CHANGED=0")
    print(f"V69_FORWARD_ROOT={root}")
    print(f"V69_ONE_SHOT_SESSION={session_path}")
    print("Git Bash may be closed after PASS. Watch the pinned MT5 panel for progress and OUTPUT=EXPORTED.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
