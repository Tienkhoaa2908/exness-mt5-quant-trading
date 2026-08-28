#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
OUT = HERE / "OUTPUT_V55"
V54_RUNNER = REPO / "runtime" / "v54_production_readiness" / "RUN_V54_PRODUCTION_READINESS.py"
BUILDER = REPO / "scripts" / "build_v55_account_agnostic_source.py"
PACKAGER = HERE / "PACKAGE_V55_EVIDENCE.py"
STATIC_TEST = REPO / "tests" / "test_v55_account_agnostic_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
EXPERT_NAME = "V55AccountAgnosticProduction"
REAL_ARM_CODE = "V55_REAL_ARMED"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v54 = load(V54_RUNNER, "v54_base_for_v55")
base = v54.base


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


def build_v55(expert_dir: Path) -> tuple[Path, str]:
    v46 = v54.v48.accepted_v46_source(expert_dir)
    parent = v54.v48.build_source(v46)
    if base.sha256(parent) != V48_SOURCE_SHA:
        raise RuntimeError("canonical V48 parent identity mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{EXPERT_NAME}.mq5"
    run([sys.executable, BUILDER, "--source", parent, "--output", out])
    digest = base.sha256(out)
    print(f"V55_SOURCE_SHA256={digest}")
    return out, digest


def compile_v55(source: Path, source_sha: str, data: Path) -> tuple[Path, Path]:
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

    base.wait_until(ready, 120, 0.5, "V55 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_copy = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(f"V55_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={base.sha256(ex5)}")
    return installed, ex5


def choose_state(common: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    for name in (
        "v55_demo_rehearsal_state.csv",
        "v54_demo_rehearsal_state.csv",
        "v53_demo_rehearsal_state.csv",
        "v50_execution_probe_state.csv",
        "v49_demo_rehearsal_state.csv",
        "v48_demo_paper_state.csv",
    ):
        p = paper / name
        if p.is_file() and p.stat().st_size > 0:
            print(f"V55_STATE_SOURCE={name} sha256={base.sha256(p)}")
            return p
    p = v54.v48.accepted_v46_state()
    print(f"V55_STATE_SOURCE=accepted_v46_state sha256={base.sha256(p)}")
    return p


def seed_state(common: Path, source: Path) -> Path:
    paper = common / "mt5_quant" / "paper"
    paper.mkdir(parents=True, exist_ok=True)
    dst = paper / "v55_demo_rehearsal_state.csv"
    if dst.is_file() and dst.stat().st_size > 0:
        print(f"V55_STATE_REUSE sha256={base.sha256(dst)}")
        return dst
    shutil.copy2(source, dst)
    if base.sha256(dst) != base.sha256(source):
        raise RuntimeError("V55 state copy mismatch")
    print(f"V55_STATE_SEEDED sha256={base.sha256(dst)}")
    return dst


def set_scalar(value: str, start: str, step: str, stop: str) -> str:
    """Return MetaTrader's native non-optimizing .set scalar format."""
    return f"{value}||{start}||{step}||{stop}||N"


def set_bool(value: bool) -> str:
    return set_scalar("true" if value else "false", "false", "0", "true")


def write_preset(data: Path, execution_mode: str) -> Path:
    presets = data / "MQL5" / "Presets"
    presets.mkdir(parents=True, exist_ok=True)
    preset = presets / f"v55_account_agnostic_{execution_mode}.set"
    real = execution_mode == "real"

    # MetaTrader-generated .set files use Value||Start||Step||Stop||N for numeric,
    # enum and bool inputs. String inputs remain plain name=value. We emit the native
    # form so StartUp/ExpertParameters is deterministic on both DEMO and REAL.
    lines = [
        "; V55 generated preset - optimization disabled",
        "InpV55Magic=" + set_scalar("550055", "550055", "1", "550055"),
        "InpV55AllowRealAccount=" + set_bool(real),
        "InpV55RealArmCode=" + (REAL_ARM_CODE if real else ""),
        "InpV55MaxRiskPct=" + set_scalar("0.50", "0.50", "0.01", "1.00"),
        "InpV55DailyLossPct=" + set_scalar("2.00", "2.00", "0.10", "10.00"),
        "InpV55MaxDrawdownPct=" + set_scalar("6.00", "6.00", "0.10", "20.00"),
        "InpV55MaxSpreadPoints=" + set_scalar("150", "150", "1", "1000"),
        "InpV55MaxTickAgeSeconds=" + set_scalar("15", "15", "1", "300"),
        "InpV55MaxStrategyStateAgeSeconds=" + set_scalar("30", "30", "1", "600"),
        "InpV55MaxConsecutiveRejects=" + set_scalar("3", "3", "1", "20"),
        "InpV55MaxMarginUsagePct=" + set_scalar("80.0", "80.0", "1.0", "95.0"),
        "",
    ]
    preset.write_text("\r\n".join(lines), encoding="utf-16")
    decoded = preset.read_text(encoding="utf-16")
    required = ["InpV55Magic=550055||", "InpV55MaxRiskPct=0.50||"]
    if real:
        required += ["InpV55AllowRealAccount=true||", f"InpV55RealArmCode={REAL_ARM_CODE}"]
    else:
        required += ["InpV55AllowRealAccount=false||", "InpV55RealArmCode="]
    for token in required:
        if token not in decoded:
            raise RuntimeError(f"V55 preset missing {token}")
    for line in decoded.splitlines():
        if line.startswith("InpV55") and "RealArmCode" not in line and "||" not in line:
            raise RuntimeError(f"V55 preset scalar not in native .set format: {line}")
    print(f"V55_PRESET_PASS mode={execution_mode} sha256={base.sha256(preset)} path={preset}")
    return preset


def write_config(data: Path, preset: Path) -> Path:
    ini = data / "config" / "v55_account_agnostic.ini"
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
ExpertParameters={preset.name}
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
        f"ExpertParameters={preset.name}",
        "Symbol=XAUUSDm",
        "Period=M15",
    ):
        if token not in decoded:
            raise RuntimeError(f"V55 config missing {token}")
    print(f"V55_CONFIG_PASS sha256={base.sha256(ini)} path={ini}")
    return ini


def wait_ready(common: Path, execution_mode: str) -> dict[str, str]:
    status = common / "mt5_quant" / "v55" / "V55_PRODUCTION_READINESS_STATUS.txt"
    expected_account = "REAL" if execution_mode == "real" else "DEMO"
    expected_activation = "REAL_ARMED" if execution_mode == "real" else "DEMO_ACTIVE"
    expected_real_auth = "1" if execution_mode == "real" else "0"
    deadline = time.time() + 120
    while time.time() < deadline:
        s = kv_retry(status, attempts=1)
        if s:
            if s.get("halted") == "1":
                raise RuntimeError(f"V55 halted during startup reason={s.get('halt_reason','')}")
            actual_account = s.get("account_mode", "")
            if actual_account and actual_account != expected_account:
                raise RuntimeError(
                    f"logged MT5 account mode mismatch expected={expected_account} actual={actual_account}"
                )
            if (
                actual_account == expected_account
                and s.get("terminal_trade_allowed") == "1"
                and s.get("mql_trade_allowed") == "1"
                and s.get("terminal_dlls_allowed") == "0"
                and s.get("real_money_authorized") == expected_real_auth
                and s.get("production_activation") == expected_activation
                and s.get("candidate") == "v52_b4_or_b3_trend_bos"
                and s.get("run_id", "").strip()
            ):
                print(f"V55_ACCOUNT_AGNOSTIC_READY=1 mode={execution_mode}")
                return s
        if not base.task_running("terminal64.exe"):
            raise RuntimeError("MT5 exited before V55 READY")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V55 READY")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--execution-mode",
        choices=("demo", "real"),
        default="demo",
        help="demo is default; real explicitly arms new real-money risk for this startup",
    )
    return ap.parse_args()


def main() -> int:
    ns = parse_args()
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"BRANCH={branch}\nHEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before V55 launch")

    run([sys.executable, "-m", "py_compile", BUILDER, PACKAGER, Path(__file__).resolve(), STATIC_TEST])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    source, source_sha = build_v55(expert_dir)
    compile_v55(source, source_sha, data)
    print("V55_PRESTART_BUILD_COMPILE_PASS=1")

    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it before V55 start.")

    seed_state(common, choose_state(common))
    preset = write_preset(data, ns.execution_mode)
    ini = write_config(data, preset)
    proc = subprocess.Popen(
        [str(base.TERMINAL_EXE), f"/config:{ini}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"TERMINAL_PID={proc.pid}")
    status = wait_ready(common, ns.execution_mode)

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
            f"startup_{ns.execution_mode}",
        ]
    )
    print("V55_STARTED=1")
    print(f"RUN_ID={status.get('run_id','')}")
    print(f"ACCOUNT_MODE={status.get('account_mode','')}")
    print(f"PRODUCTION_ACTIVATION={status.get('production_activation','')}")
    print(f"REAL_MONEY_AUTHORIZED={status.get('real_money_authorized','')}")
    print("SYMBOL=XAUUSDm")
    print("TIMEFRAME=M15")
    print("OWNED_MAGIC=550055")
    print("MAX_OWNED_STRATEGY_POSITIONS=1")
    print("CANDIDATE=v52_b4_or_b3_trend_bos")
    print("V53_NATURAL_MAPPING=NOT_OBSERVED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
