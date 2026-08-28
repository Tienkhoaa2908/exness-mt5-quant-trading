#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_BRANCH = "agent/v54-production-readiness-hardening"
V48_SOURCE_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V54"
V48_RUNNER = REPO / "runtime" / "v48_demo_paper" / "RUN_V48_DEMO_PAPER_START.py"
BUILDER = REPO / "scripts" / "build_v54_production_readiness_source.py"
PACKAGER = HERE / "PACKAGE_V54_EVIDENCE.py"
STATIC_TEST = REPO / "tests" / "test_v54_production_readiness_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
EXPERT_NAME = "V54ProductionReadiness"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v48 = load(V48_RUNNER, "v48_base_for_v54")
base = v48.base


def run(cmd, *, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def kv_retry(path: Path, attempts: int = 100, delay: float = 0.1) -> dict[str, str]:
    for i in range(attempts):
        try:
            if not path.is_file():
                time.sleep(delay)
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            out: dict[str, str] = {}
            for line in text.replace("\\r\\n", "\n").splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
            if out:
                return out
        except (PermissionError, OSError):
            if i + 1 >= attempts:
                raise
        time.sleep(delay)
    return {}


def build_v54(expert_dir: Path) -> tuple[Path, str]:
    v46 = v48.accepted_v46_source(expert_dir)
    parent = v48.build_source(v46)
    if base.sha256(parent) != V48_SOURCE_SHA:
        raise RuntimeError("canonical V48 parent identity mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{EXPERT_NAME}.mq5"
    run([sys.executable, BUILDER, "--source", parent, "--output", out])
    digest = base.sha256(out)
    print(f"V54_SOURCE_SHA256={digest}")
    return out, digest


def compile_v54(source: Path, source_sha: str, data: Path) -> tuple[Path, Path]:
    root = data / "MQL5" / "Experts"
    root.mkdir(parents=True, exist_ok=True)
    installed = root / f"{EXPERT_NAME}.mq5"
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
        raise RuntimeError("MetaEditor is open. Close it and rerun.")
    cp = subprocess.run(
        [str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"]
    )
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")

    def ready():
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, "V54 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_copy = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(f"V54_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={base.sha256(ex5)}")
    return installed, ex5


def choose_state(common: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    for name in (
        "v53_demo_rehearsal_state.csv",
        "v50_execution_probe_state.csv",
        "v49_demo_rehearsal_state.csv",
        "v48_demo_paper_state.csv",
    ):
        p = paper / name
        if p.is_file() and p.stat().st_size > 0:
            print(f"V54_STATE_SOURCE={name} sha256={base.sha256(p)}")
            return p
    p = v48.accepted_v46_state()
    print(f"V54_STATE_SOURCE=accepted_v46_state sha256={base.sha256(p)}")
    return p


def seed_state(common: Path, source: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    paper.mkdir(parents=True, exist_ok=True)
    dst = paper / "v54_demo_rehearsal_state.csv"
    shutil.copy2(source, dst)
    if base.sha256(dst) != base.sha256(source):
        raise RuntimeError("V54 state copy mismatch")
    print(f"V54_STATE_SEEDED sha256={base.sha256(dst)}")
    return dst


def write_config(data: Path) -> Path:
    ini = data / "config" / "v54_production_readiness.ini"
    text = f'''[Common]
KeepPrivate=1
NewsEnable=0
[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=1
Account=0
Profile=0
[StartUp]
Expert={EXPERT_NAME}
Symbol=XAUUSDm
Period=M15
'''
    base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    for token in (
        "AllowLiveTrading=1",
        "AllowDllImport=0",
        "Enabled=1",
        f"Expert={EXPERT_NAME}",
        "Symbol=XAUUSDm",
        "Period=M15",
    ):
        if token not in decoded:
            raise RuntimeError(f"V54 config missing {token}")
    print(f"V54_CONFIG_PASS sha256={base.sha256(ini)} path={ini}")
    return ini


def wait_ready(common: Path) -> dict[str, str]:
    status = common / "mt5_quant" / "v54" / "V54_PRODUCTION_READINESS_STATUS.txt"
    deadline = time.time() + 120
    while time.time() < deadline:
        s = kv_retry(status, attempts=1)
        if s:
            if s.get("halted") == "1":
                raise RuntimeError(f"V54 halted during startup reason={s.get('halt_reason','')}")
            if (
                s.get("account_mode") == "DEMO"
                and s.get("terminal_trade_allowed") == "1"
                and s.get("mql_trade_allowed") == "1"
                and s.get("terminal_dlls_allowed") == "0"
                and s.get("real_money_authorized") == "0"
                and s.get("production_activation") == "DISABLED_DEMO_SAFE"
                and s.get("candidate") == "v52_b4_or_b3_trend_bos"
                and s.get("run_id", "").strip()
            ):
                print("V54_PRODUCTION_READINESS_READY=1")
                return s
        if not base.task_running("terminal64.exe"):
            raise RuntimeError("MT5 exited before V54 READY")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V54 READY")


def main() -> int:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"BRANCH={branch}\nHEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before V54 launch")

    run([sys.executable, "-m", "py_compile", BUILDER, PACKAGER, Path(__file__).resolve(), STATIC_TEST])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    source, source_sha = build_v54(expert_dir)
    compile_v54(source, source_sha, data)
    print("V54_PRESTART_BUILD_COMPILE_PASS=1")

    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it before V54 start.")

    seed_state(common, choose_state(common))
    ini = write_config(data)
    proc = subprocess.Popen(
        [str(base.TERMINAL_EXE), f"/config:{ini}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"TERMINAL_PID={proc.pid}")
    status = wait_ready(common)

    run(
        [
            sys.executable,
            PACKAGER,
            "--repo",
            REPO,
            "--common",
            common,
            "--output-dir",
            OUT,
            "--label",
            "startup",
        ]
    )
    print("V54_STARTED=1")
    print(f"RUN_ID={status.get('run_id','')}")
    print("SYMBOL=XAUUSDm")
    print("TIMEFRAME=M15")
    print("OWNED_MAGIC=540054")
    print("MAX_OWNED_STRATEGY_POSITIONS=1")
    print("CANDIDATE=v52_b4_or_b3_trend_bos")
    print("PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V53_NATURAL_MAPPING=NOT_OBSERVED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
