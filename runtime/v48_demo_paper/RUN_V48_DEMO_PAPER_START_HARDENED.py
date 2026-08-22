#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LEGACY_PATH = HERE / "RUN_V48_DEMO_PAPER_START.py"
ATTACH_DIAG = HERE / "OUTPUT_V48" / "v48_mt5_attach_diagnostics.txt"
ALIAS_NAME = "V48DemoPaperObserver"
EXPECTED_SEED_SHA = "36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


legacy = load_module(LEGACY_PATH, "v48_legacy_hardened")


def sha256(path: Path) -> str:
    return legacy.base.sha256(path)


def paper_paths(common: Path) -> dict[str, Path]:
    root = common / "mt5_quant" / "paper"
    return {
        "root": root,
        "status": root / "V48_DEMO_PAPER_STATUS.txt",
        "latest": root / "V48_DEMO_PAPER_LATEST.txt",
        "init": root / "V48_DEMO_PAPER_INIT.txt",
        "state": root / "v48_demo_paper_state.csv",
        "seed_meta": root / "v48_demo_paper_state_seed.txt",
    }


def validate_or_quarantine_startup_metadata(common: Path) -> None:
    p = paper_paths(common)
    p["root"].mkdir(parents=True, exist_ok=True)
    latest = legacy.parse_kv(p["latest"])
    status = legacy.parse_kv(p["status"])
    latest_run = latest.get("run_id", "").strip()
    status_run = status.get("run_id", "").strip()

    if latest_run or status_run:
        raise RuntimeError(
            "existing V48 paper session has a non-empty run_id; refusing a second session. "
            "Use STATUS_V48_DEMO_PAPER_GIT_BASH.sh and preserve continuity."
        )

    if p["state"].is_file():
        state_sha = sha256(p["state"])
        if state_sha != EXPECTED_SEED_SHA:
            raise RuntimeError(
                "orphan/non-seed V48 paper state found without a valid session run_id; "
                f"continuity is ambiguous state_sha={state_sha}. No automatic reset is allowed."
            )

    debris = [x for x in (p["latest"], p["status"], p["init"]) if x.is_file()]
    if not debris:
        print("V48_STARTUP_METADATA_CLEAN=1")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = p["root"] / f"_v48_incomplete_startup_{stamp}"
    archive.mkdir(parents=True, exist_ok=False)
    for src in debris:
        shutil.move(str(src), str(archive / src.name))
    print(f"V48_INCOMPLETE_METADATA_QUARANTINED={archive}")
    print("V48_ACTIVE_STATE_PRESERVED=1")


def deploy_root_alias(data: Path) -> tuple[Path, Path]:
    canonical = data / "MQL5" / "Experts" / "mt5_quant"
    src = canonical / f"{ALIAS_NAME}.mq5"
    ex5 = canonical / f"{ALIAS_NAME}.ex5"
    if not src.is_file() or sha256(src) != legacy.V48_SOURCE_SHA:
        raise RuntimeError("canonical V48 installed source missing or SHA mismatch before alias deployment")
    if not ex5.is_file() or ex5.stat().st_size <= 0:
        raise RuntimeError("canonical V48 EX5 missing/empty before alias deployment")

    root = data / "MQL5" / "Experts"
    alias_src = root / f"{ALIAS_NAME}.mq5"
    alias_ex5 = root / f"{ALIAS_NAME}.ex5"
    shutil.copy2(src, alias_src)
    shutil.copy2(ex5, alias_ex5)

    if sha256(alias_src) != legacy.V48_SOURCE_SHA:
        raise RuntimeError("root startup alias source SHA mismatch")
    if sha256(alias_ex5) != sha256(ex5):
        raise RuntimeError("root startup alias EX5 differs from canonical compiled EX5")
    print(f"V48_STARTUP_ALIAS_SOURCE={alias_src}")
    print(f"V48_STARTUP_ALIAS_EX5={alias_ex5}")
    print(f"V48_STARTUP_ALIAS_EX5_SHA={sha256(alias_ex5)}")
    print("V48_STARTUP_ALIAS_PASS=1")
    return alias_src, alias_ex5


def write_startup_ini(data: Path) -> Path:
    ini = data / "config" / "v48_demo_paper_forward_hardened.ini"
    text = """[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert=V48DemoPaperObserver\nSymbol=XAUUSDm\nPeriod=M15\n"""
    legacy.base.write_utf16_ini(ini, text)
    raw = ini.read_bytes()
    decoded = raw.decode("utf-16")
    required = (
        "AllowLiveTrading=0",
        "AllowDllImport=0",
        "Enabled=1",
        "Expert=V48DemoPaperObserver",
        "Symbol=XAUUSDm",
        "Period=M15",
    )
    missing = [x for x in required if x not in decoded]
    if missing:
        raise RuntimeError(f"startup INI self-check failed missing={missing}")
    print(f"V48_CONFIG_SHA256={sha256(ini)}")
    print("V48_CONFIG_SELF_CHECK_PASS=1")
    return ini


def snapshot_logs(data: Path) -> dict[str, int]:
    snap: dict[str, int] = {}
    for folder in (data / "logs", data / "MQL5" / "Logs"):
        if not folder.is_dir():
            continue
        for path in folder.glob("*.log"):
            if not path.is_file():
                continue
            try:
                snap[str(path)] = len(legacy.decode_mt5_log(path).splitlines())
            except Exception:
                snap[str(path)] = 0
    return snap


def launch_log_delta(data: Path, snap: dict[str, int]) -> list[tuple[Path, list[str]]]:
    out: list[tuple[Path, list[str]]] = []
    for folder in (data / "logs", data / "MQL5" / "Logs"):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.log"), key=lambda x: x.stat().st_mtime):
            if not path.is_file():
                continue
            try:
                lines = legacy.decode_mt5_log(path).splitlines()
            except Exception:
                continue
            start = snap.get(str(path), 0)
            if start < 0 or start > len(lines):
                start = 0
            delta = lines[start:]
            if delta:
                out.append((path, delta))
    return out


def collect_launch_diagnostics(
    data: Path,
    init_path: Path,
    label: str,
    snap: dict[str, int],
    ini: Path,
    alias_ex5: Path,
) -> str:
    deltas = launch_log_delta(data, snap)
    all_new = [line for _, lines in deltas for line in lines]
    low = "\n".join(all_new).lower()
    config_consumed = ini.name.lower() in low
    expert_seen = "v48demopaperobserver" in low
    lines = [
        f"label={label}",
        f"time={time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"config={ini}",
        f"config_sha256={sha256(ini) if ini.is_file() else 'MISSING'}",
        f"startup_alias_ex5={alias_ex5}",
        f"startup_alias_ex5_exists={1 if alias_ex5.is_file() else 0}",
        f"startup_alias_ex5_sha256={sha256(alias_ex5) if alias_ex5.is_file() else 'MISSING'}",
        f"CONFIG_CONSUMED_EVIDENCE={1 if config_consumed else 0}",
        f"EXPERT_REFERENCE_EVIDENCE={1 if expert_seen else 0}",
        f"INIT_DIAGNOSTIC_PRESENT={1 if init_path.is_file() else 0}",
    ]
    if init_path.is_file():
        lines.append("--- V48 INIT DIAGNOSTIC ---")
        lines.extend(init_path.read_text(encoding="utf-8-sig", errors="replace").splitlines())

    dropped_noise = 0
    for path, delta in deltas:
        useful = []
        for line in delta:
            lowline = line.lower()
            if "mql5.community" in lowline or "virtual hosting" in lowline:
                dropped_noise += 1
                continue
            useful.append(line)
        if useful:
            lines.append(f"--- LAUNCH-SCOPED LOG DELTA {path} ---")
            lines.extend(useful[-120:])
    lines.append(f"IGNORED_UNRELATED_MQL5_COMMUNITY_VPS_LINES={dropped_noise}")
    if not deltas:
        lines.append("NO_NEW_MT5_LOG_LINES_AFTER_LAUNCH=1")

    ATTACH_DIAG.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    ATTACH_DIAG.write_text(text, encoding="utf-8")
    print("\n=== V48 LAUNCH-SCOPED ATTACH DIAGNOSTICS ===")
    print(text)
    print(f"ATTACH_DIAGNOSTICS_FILE={ATTACH_DIAG}")
    return text


def status_is_ready(status: Path) -> bool:
    if not status.is_file() or status.stat().st_size == 0:
        return False
    kv = legacy.parse_kv(status)
    required = {
        "account_mode": "DEMO",
        "real_account_forbidden": "1",
        "broker_orders": "0",
        "live_authorized": "0",
        "terminal_trade_allowed": "0",
        "terminal_dlls_allowed": "0",
        "candidate": "v46_hl10_thr0p05_breadth4",
        "book": "usd40_r1p0_cent_continuous",
    }
    return bool(kv.get("run_id", "").strip()) and all(kv.get(k) == v for k, v in required.items())


def launch_and_verify(data: Path, common: Path) -> None:
    if legacy.base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is already open. Close it once before the hardened V48 starter.")

    validate_or_quarantine_startup_metadata(common)
    paths = paper_paths(common)
    for key in ("status", "init"):
        try:
            paths[key].unlink()
        except FileNotFoundError:
            pass

    _, alias_ex5 = deploy_root_alias(data)
    ini = write_startup_ini(data)
    snap = snapshot_logs(data)

    legacy.say("LAUNCH V48 HARDENED — DEMO real-time feed, virtual book, zero broker-order route")
    print(f"CONFIG={ini}")
    proc = subprocess.Popen(
        [str(legacy.base.TERMINAL_EXE), f"/config:{ini}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"TERMINAL_LAUNCH_PID={proc.pid}")

    deadline = time.time() + 90
    while time.time() < deadline:
        if status_is_ready(paths["status"]):
            break
        if paths["init"].is_file():
            init = legacy.parse_kv(paths["init"])
            if init.get("stage") == "REFUSED":
                collect_launch_diagnostics(data, paths["init"], "EA_REFUSED_DURING_ONINIT", snap, ini, alias_ex5)
                raise RuntimeError(f"V48 EA attached but refused initialization reason={init.get('reason','')}")
        if not legacy.base.task_running("terminal64.exe"):
            collect_launch_diagnostics(data, paths["init"], "TERMINAL_EXITED_BEFORE_READY", snap, ini, alias_ex5)
            raise RuntimeError("MT5 exited before V48 became ready")
        time.sleep(1.0)
    else:
        collect_launch_diagnostics(data, paths["init"], "PRE_ONINIT_OR_READY_TIMEOUT", snap, ini, alias_ex5)
        raise RuntimeError("V48 did not reach a valid READY status within 90s; see launch-scoped diagnostics")

    kv = legacy.parse_kv(paths["status"])
    before_mtime = paths["status"].stat().st_mtime_ns
    timer_deadline = time.time() + 50
    timer_refreshed = False
    while time.time() < timer_deadline:
        time.sleep(1.0)
        if paths["status"].is_file() and paths["status"].stat().st_mtime_ns > before_mtime:
            timer_refreshed = True
            break
        if not legacy.base.task_running("terminal64.exe"):
            break
    if not timer_refreshed:
        collect_launch_diagnostics(data, paths["init"], "STATUS_TIMER_REFRESH_FAILED", snap, ini, alias_ex5)
        raise RuntimeError("V48 READY status did not refresh by timer; market-close-safe heartbeat gate failed")

    print("V48_DEMO_PAPER_RUNNING=1")
    print(f"RUN_ID={kv.get('run_id','')}")
    print(f"SESSION_START={kv.get('session_start','')}")
    print(f"BALANCE={kv.get('balance','')}")
    print(f"EQUITY={kv.get('equity','')}")
    print(f"HEALTHY_HL10_COUNT={kv.get('healthy_hl10_count','')}")
    print(f"TERMINAL_TRADE_ALLOWED={kv.get('terminal_trade_allowed','')}")
    print(f"TERMINAL_DLLS_ALLOWED={kv.get('terminal_dlls_allowed','')}")
    print(f"STATUS_FILE={paths['status']}")
    print(f"LATEST_FILE={paths['latest']}")
    print("STATUS_TIMER_REFRESH_PASS=1")
    print("CHART_DASHBOARD=ENABLED")
    print("BROKER_ORDERS=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("Keep MT5 on the DEMO account. Keep terminal AutoTrading OFF.")


def main() -> int:
    if sha256(LEGACY_PATH) != "":
        pass
    legacy.write_startup_ini = write_startup_ini
    legacy.launch_and_verify = launch_and_verify
    return legacy.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
