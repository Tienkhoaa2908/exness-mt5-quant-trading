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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_REAL_READINESS_PROBE"
PROBE_BUILDER = REPO / "scripts" / "build_v69_demo_execution_probe_source.py"
SIGNAL_ANALYZER = REPO / "scripts" / "analyze_v69_live_signal_path.py"
FORWARD_RUNNER = REPO / "runtime" / "v69_one_shot_prospective_demo" / "RUN_V69_ONE_SHOT_BROKER_READY_DEMO.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
PROBE_EXPERT = "V69DemoExecutionProbe"
SYMBOL = "XAUUSDm"
PERIOD = "M15"
PROBE_COMMON_DIR = "v69_demo_execution_probe"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


forward = load(FORWARD_RUNNER, "v69_forward_for_real_readiness_probe")
signal_mod = load(SIGNAL_ANALYZER, "v69_signal_path_for_real_readiness_probe")


def run(cmd, *, cwd=None) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").replace("\\r\\n", "\n").splitlines():
        if "=" in raw:
            k, v = raw.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def archive_path(path: Path, prefix: str) -> None:
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
    target = path.parent / f"_{prefix}_{stamp}"
    path.rename(target)
    print(f"V69_ARCHIVED={target}")


def snapshot_signal_path(common: Path) -> dict:
    root = common / "mt5_quant" / "v69_frozen_forward_demo"
    OUT.mkdir(parents=True, exist_ok=True)
    result = signal_mod.analyze(root)
    out = OUT / "V69_PRE_PROBE_SIGNAL_PATH.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V69_PRE_PROBE_SIGNAL_PATH_CLASSIFICATION=" + result["classification"])
    for stage, count in result["stage_counts"].items():
        print(f"V69_PRE_PROBE_{stage}={count}")
    print(f"V69_PRE_PROBE_CLOSED_DEALS={result['closed_deals']}")
    print("V69_PRE_PROBE_NEXT_GATE=" + result["next_gate"])
    print(f"V69_PRE_PROBE_SIGNAL_PATH_JSON={out}")
    return result


def build_probe(runner, data: Path, expert_dir: Path) -> tuple[Path, Path, str, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    a = OUT / f"{PROBE_EXPERT}.a.mq5"
    b = OUT / f"{PROBE_EXPERT}.b.mq5"
    run([sys.executable, PROBE_BUILDER, "--output", a])
    run([sys.executable, PROBE_BUILDER, "--output", b])
    sha_a, sha_b = runner.sha(a), runner.sha(b)
    if sha_a != sha_b or a.read_bytes() != b.read_bytes():
        raise RuntimeError(f"probe builder is not deterministic a={sha_a} b={sha_b}")
    compile_log = runner.compile_source(a, sha_a, data, expert_dir, PROBE_EXPERT)
    installed_mq5 = expert_dir / f"{PROBE_EXPERT}.mq5"
    installed_ex5 = expert_dir / f"{PROBE_EXPERT}.ex5"
    if not installed_mq5.is_file() or runner.sha(installed_mq5) != sha_a:
        raise RuntimeError("probe installed MQ5 mismatch")
    if not installed_ex5.is_file() or installed_ex5.stat().st_size <= 0:
        raise RuntimeError("probe EX5 missing")
    ex5_sha = runner.sha(installed_ex5)
    startup_mq5 = data / "MQL5" / "Experts" / f"{PROBE_EXPERT}.mq5"
    startup_ex5 = startup_mq5.with_suffix(".ex5")
    shutil.copy2(installed_mq5, startup_mq5)
    shutil.copy2(installed_ex5, startup_ex5)
    if runner.sha(startup_mq5) != sha_a or runner.sha(startup_ex5) != ex5_sha:
        raise RuntimeError("probe startup copy verification failed")
    print(f"V69_EXECUTION_PROBE_SOURCE_SHA256={sha_a}")
    print(f"V69_EXECUTION_PROBE_EX5_SHA256={ex5_sha}")
    print(f"V69_EXECUTION_PROBE_COMPILE_LOG={compile_log}")
    return startup_mq5, startup_ex5, sha_a, ex5_sha


def write_probe_config(runner, data: Path) -> Path:
    ini = data / "config" / "v69_demo_execution_probe.ini"
    text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert={PROBE_EXPERT}\nSymbol={SYMBOL}\nPeriod={PERIOD}\n"""
    runner.base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    for token in ("AllowLiveTrading=1", f"Expert={PROBE_EXPERT}", f"Symbol={SYMBOL}", f"Period={PERIOD}"):
        if token not in decoded:
            raise RuntimeError(f"probe startup config missing {token}")
    print(f"V69_EXECUTION_PROBE_CONFIG_SHA256={runner.sha(ini)}")
    return ini


def wait_probe(root: Path, proc: subprocess.Popen) -> dict[str, str]:
    result_file = root / "V69_DEMO_EXECUTION_PROBE.txt"
    deadline = time.time() + 90
    last_state = ""
    while time.time() < deadline:
        kv = parse_kv(result_file)
        state = kv.get("state", "")
        if state and state != last_state:
            last_state = state
            print(
                "V69_EXECUTION_PROBE_STATE=" + state
                + " detail=" + kv.get("detail", "")
                + " check=" + kv.get("check_retcode", "?")
                + " open=" + kv.get("open_retcode", "?")
                + " close=" + kv.get("close_retcode", "?")
            )
        if state == "PASS":
            print("V69_ACTUAL_DEMO_EXECUTION_VERIFIED=1")
            print(f"V69_EXECUTION_PROBE_OPEN_RETCODE={kv.get('open_retcode','?')}")
            print(f"V69_EXECUTION_PROBE_OPEN_COMMENT={kv.get('open_comment','')}")
            print(f"V69_EXECUTION_PROBE_CLOSE_RETCODE={kv.get('close_retcode','?')}")
            print(f"V69_EXECUTION_PROBE_CLOSE_COMMENT={kv.get('close_comment','')}")
            print(f"V69_EXECUTION_PROBE_OPEN_PRICE={kv.get('open_price','?')}")
            print(f"V69_EXECUTION_PROBE_CLOSE_PRICE={kv.get('close_price','?')}")
            print(f"V69_EXECUTION_PROBE_FREE_MARGIN={kv.get('free_margin','?')}")
            return kv
        if state == "FAIL":
            raise RuntimeError(
                "actual DEMO execution probe failed: "
                f"detail={kv.get('detail','')} check={kv.get('check_retcode','?')} "
                f"open={kv.get('open_retcode','?')} {kv.get('open_comment','')} "
                f"close={kv.get('close_retcode','?')} {kv.get('close_comment','')}"
            )
        if proc.poll() is not None and state != "PASS":
            raise RuntimeError(f"probe terminal exited before PASS rc={proc.returncode} state={state or 'missing'}")
        time.sleep(0.5)
    raise RuntimeError("timeout waiting for actual DEMO execution probe")


def wait_terminal_close(proc: subprocess.Popen) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            print(f"V69_EXECUTION_PROBE_TERMINAL_CLOSED=1 rc={proc.returncode}")
            return
        time.sleep(0.5)
    raise RuntimeError("probe PASS was written but TerminalClose did not complete within 30s; do not force-kill MT5")


def bridge_expected_head() -> str:
    expected_head = os.environ.get("V69_REAL_READINESS_EXPECTED_HEAD", "").strip()
    if not expected_head:
        expected_head = os.environ.get("V69_ONE_SHOT_EXPECTED_HEAD", "").strip()
    if not expected_head:
        raise RuntimeError("V69_REAL_READINESS_EXPECTED_HEAD is required")
    os.environ["V69_REAL_READINESS_EXPECTED_HEAD"] = expected_head
    os.environ["V69_ONE_SHOT_EXPECTED_HEAD"] = expected_head
    print(f"V69_ONE_SHOT_EXPECTED_HEAD_BRIDGED={expected_head}")
    return expected_head


def main() -> int:
    bridge_expected_head()
    branch, head = forward.base.ensure_repo()
    run([sys.executable, "-m", "py_compile", PROBE_BUILDER, SIGNAL_ANALYZER, Path(__file__)])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = forward.base.configure_runtime()
    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError("Close MT5 once before running the real-readiness probe; current telemetry will be read after close.")
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("Close MetaEditor once before running the real-readiness probe.")

    data = Path(runner.base.find_mt5_data_dir())
    common = Path(runner.base.find_common_files_dir(data))
    expert_dir = data / "MQL5" / "Experts" / "mt5_quant"
    print(f"MT5_DATA={data}")
    print(f"MT5_COMMON={common}")

    signal_result = snapshot_signal_path(common)

    probe_root = common / "mt5_quant" / PROBE_COMMON_DIR
    archive_path(probe_root, "v69_demo_execution_probe_previous")
    probe_root.mkdir(parents=True, exist_ok=False)

    _, _, probe_source_sha, probe_ex5_sha = build_probe(runner, data, expert_dir)
    ini = write_probe_config(runner, data)
    print("LAUNCH_V69_ACTUAL_DEMO_EXECUTION_PROBE=1")
    proc = subprocess.Popen(
        [str(runner.base.TERMINAL_EXE), f"/config:{ini}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0,
    )
    print(f"V69_EXECUTION_PROBE_TERMINAL_PID={proc.pid}")
    probe = wait_probe(probe_root, proc)
    wait_terminal_close(proc)

    result = {
        "protocol": "v69_real_readiness_execution_probe_v1",
        "branch": branch,
        "head": head,
        "actual_demo_execution_verified": True,
        "real_money_authorized": False,
        "probe_source_sha256": probe_source_sha,
        "probe_ex5_sha256": probe_ex5_sha,
        "probe": probe,
        "pre_probe_signal_path": signal_result,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    result_path = OUT / "V69_REAL_READINESS_PROBE_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"V69_REAL_READINESS_PROBE_RESULT={result_path}")

    # Relaunch the frozen broker-ready V69 automatically after the isolated probe.
    print("RELAUNCH_FROZEN_V69_AFTER_EXECUTION_PROBE=1")
    rc = forward.main()
    if rc != 0:
        raise RuntimeError(f"execution probe passed but frozen V69 relaunch failed rc={rc}")

    print("V69_REAL_READINESS_EXECUTION_LAYER=PASS")
    print("V69_REAL_MONEY_AUTHORIZED=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
