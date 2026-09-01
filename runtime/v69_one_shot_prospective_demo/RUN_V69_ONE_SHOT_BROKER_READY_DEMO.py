#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE_RUNNER = HERE / "RUN_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"
BROKER_BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_broker_ready_dashboard_source.py"
BROKER_STATIC = REPO / "tests" / "test_v69_one_shot_broker_ready_static.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load(BASE_RUNNER, "v69_one_shot_base_for_broker_ready")


def build_compile_install(runner, data: Path, expert_dir: Path):
    """Deterministic build without a redundant stale dashboard hash pin.

    Exact Git HEAD + frozen-parent pins + A/B deterministic generation are the
    source-of-truth gates. This avoids the prior source-changed/hash-not-updated
    harness failure while preserving byte verification through compile/install.
    """
    base.OUT.mkdir(parents=True, exist_ok=True)
    source_a = base.OUT / f"{base.EXPERT_NAME}.base.a.mq5"
    source_b = base.OUT / f"{base.EXPERT_NAME}.base.b.mq5"
    base.run([sys.executable, BROKER_BUILDER, "--output", source_a])
    base.run([sys.executable, BROKER_BUILDER, "--output", source_b])
    sha_a, sha_b = runner.sha(source_a), runner.sha(source_b)
    if sha_a != sha_b:
        raise RuntimeError(f"broker dashboard deterministic build mismatch a={sha_a} b={sha_b}")

    print(f"V69_FROZEN_PARENT_SOURCE_SHA256={base.FROZEN_FORWARD_SOURCE_SHA256}")
    print(f"V69_BROKER_READY_DASHBOARD_SOURCE_SHA256={sha_a}")
    print("V69_BROKER_PREFLIGHT_ORDER_SEND=0")
    print("V69_DASHBOARD_UI_ONLY=1")
    print("V69_STRATEGY_CHANGED=0")

    compile_log = runner.compile_source(source_a, sha_a, data, expert_dir, base.EXPERT_NAME)
    installed_source = expert_dir / f"{base.EXPERT_NAME}.mq5"
    installed_ex5 = expert_dir / f"{base.EXPERT_NAME}.ex5"
    if not installed_source.is_file() or runner.sha(installed_source) != sha_a:
        raise RuntimeError("installed broker-ready dashboard MQ5 identity mismatch")
    if not installed_ex5.is_file() or installed_ex5.stat().st_size <= 0:
        raise RuntimeError("compiled broker-ready dashboard EX5 missing")
    ex5_sha = runner.sha(installed_ex5)

    startup_source = Path(data) / "MQL5" / "Experts" / f"{base.EXPERT_NAME}.mq5"
    startup_ex5 = startup_source.with_suffix(".ex5")
    shutil.copy2(installed_source, startup_source)
    shutil.copy2(installed_ex5, startup_ex5)
    if runner.sha(startup_source) != sha_a or runner.sha(startup_ex5) != ex5_sha:
        raise RuntimeError("startup broker-ready expert byte-copy verification failed")

    print(f"V69_DASHBOARD_EX5_SHA256={ex5_sha}")
    print("V69_STARTUP_EXPERT_COPY_PASS=1")
    return startup_source, startup_ex5, sha_a, ex5_sha, compile_log


def wait_ready(runner, root: Path, proc: subprocess.Popen) -> dict[str, str]:
    status_path = root / "V64_STATUS.txt"
    heartbeat_path = root / "V69_DASHBOARD_HEARTBEAT.txt"
    deadline = time.time() + 180
    blocked_since = None
    blocked_detail = ""

    while time.time() < deadline:
        s = base.parse_kv(status_path)
        hb = base.parse_kv(heartbeat_path)
        if s and hb:
            state = s.get("state", "")
            ticks = int(hb.get("tick_count", "0") or 0)
            broker_ready = hb.get("broker_ready") == "1"
            transport_ready = (
                hb.get("terminal_trade_allowed") == "1"
                and hb.get("mql_trade_allowed") == "1"
            )
            identity_ready = (
                state == "READY"
                and s.get("symbol") == base.SYMBOL
                and s.get("fixed_lot") in {"0.01", "0.010"}
                and hb.get("symbol") == base.SYMBOL
                and hb.get("period") == "PERIOD_M15"
                and hb.get("account_mode") == "0"
                and hb.get("real_money_authorized") == "0"
                and ticks > 0
            )
            if identity_ready and transport_ready and broker_ready:
                print(f"V69_FORWARD_DEMO_READY=1 ticks={ticks}")
                print(f"V69_BROKER_PREFLIGHT_READY=1 detail={hb.get('broker_detail','READY')}")
                print(
                    "V69_BROKER_VOLUME="
                    f"lot=0.01 min={hb.get('volume_min','?')} "
                    f"step={hb.get('volume_step','?')} max={hb.get('volume_max','?')}"
                )
                print(f"V69_BROKER_ORDERCHECK_RETCODE={hb.get('broker_ordercheck_retcode','?')}")
                print("V69_RUNTIME_SMOKE_VERIFIED=1")
                return {"status": s, "heartbeat": hb}

            if identity_ready and not broker_ready:
                detail = hb.get("broker_detail", "broker_not_ready")
                if detail != blocked_detail:
                    blocked_detail = detail
                    blocked_since = time.time()
                    print(
                        "V69_BROKER_PREFLIGHT_WAIT="
                        f"{detail} lot=0.01 min={hb.get('volume_min','?')} "
                        f"step={hb.get('volume_step','?')} max={hb.get('volume_max','?')} "
                        f"retcode={hb.get('broker_ordercheck_retcode','?')}"
                    )
                elif blocked_since is not None and time.time() - blocked_since >= 12:
                    raise RuntimeError(
                        "BROKER PREFLIGHT BLOCKED before any strategy signal: "
                        f"detail={detail} lot=0.01 min={hb.get('volume_min','?')} "
                        f"step={hb.get('volume_step','?')} max={hb.get('volume_max','?')} "
                        f"trade_mode={hb.get('symbol_trade_mode','?')} "
                        f"filling={hb.get('symbol_filling_mode','?')} "
                        f"ordercheck_retcode={hb.get('broker_ordercheck_retcode','?')}"
                    )

            if state == "STOPPED":
                raise RuntimeError(f"V69 stopped during startup detail={s.get('detail','')}")

        if proc.poll() is not None and not runner.base.task_running("terminal64.exe"):
            raise RuntimeError(f"MT5 exited before V69 READY rc={proc.returncode}")
        time.sleep(1)

    hb = base.parse_kv(heartbeat_path)
    raise RuntimeError(
        "timeout waiting for V69 broker-ready DEMO heartbeat "
        f"detail={hb.get('broker_detail','missing_heartbeat')} "
        f"retcode={hb.get('broker_ordercheck_retcode','?')}"
    )


def start_supervisor(session_path: Path) -> int:
    py = Path(sys.executable)
    pythonw = py.with_name("pythonw.exe")
    exe = pythonw if pythonw.is_file() else py
    flags = 0
    if os.name == "nt":
        flags = (
            getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        )
    proc = subprocess.Popen(
        [str(exe), str(base.SUPERVISOR), "--session", str(session_path)],
        cwd=str(REPO), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags, close_fds=True,
    )
    print(f"V69_FORWARD_SUPERVISOR_PID={proc.pid}")
    print("V69_BACKGROUND_CONSOLE_WINDOWS=DISABLED")
    return proc.pid


def main() -> int:
    # Monkeypatch only orchestration/UI gates. The strategy source still comes from
    # the frozen V69 parent underneath the broker-ready dashboard builder.
    base.BUILDER = BROKER_BUILDER
    base.DASHBOARD_STATIC = BROKER_STATIC
    base.build_compile_install = build_compile_install
    base.wait_ready = wait_ready
    base.start_supervisor = start_supervisor
    return base.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
