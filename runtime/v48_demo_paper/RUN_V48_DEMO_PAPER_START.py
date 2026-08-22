#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_BRANCH = "agent/v48-demo-paper-forward"
V46_SOURCE_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
V47_SOURCE_SHA = "7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44"
V48_SOURCE_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
V46_STATE_SHA = "36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3"
EXPERT_NAME = "V48DemoPaperObserver"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V48"
LOG = OUT / "v48_demo_paper_start.log"
ATTACH_DIAG = OUT / "v48_mt5_attach_diagnostics.txt"

V45_BASE = REPO / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT.py"
V47_BUILDER = REPO / "scripts" / "build_v47_forward_regime_shadow_source.py"
V48_BUILDER = REPO / "scripts" / "build_v48_demo_paper_observer_source.py"
STATIC_TEST = REPO / "tests" / "test_v48_demo_paper_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load_module(V45_BASE, "v45_base_for_v48")


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


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def run(cmd, *, cwd=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file(): return out
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" not in raw: continue
        k, v = raw.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def find_exact(candidates: list[Path], expected_sha: str, label: str) -> Path:
    seen = []
    for p in candidates:
        if not p.is_file(): continue
        h = base.sha256(p); seen.append((str(p), h))
        if h == expected_sha:
            print(f"{label}_PASS path={p} sha256={h}")
            return p
    raise RuntimeError(f"{label} exact asset missing expected={expected_sha} seen={seen}")


def accepted_v46_source(expert_dir: Path) -> Path:
    return find_exact([
        REPO / "runtime" / "v46_expert_breadth" / "OUTPUT_V46" / "V46ExpertBreadthLab.base.a.mq5",
        REPO / "runtime" / "v46_expert_breadth" / "OUTPUT_V46" / "bundle" / "V46ExpertBreadthLab.base.a.mq5",
        expert_dir / "V46ExpertBreadthLab.mq5",
    ], V46_SOURCE_SHA, "V46_SOURCE")


def accepted_v46_state() -> Path:
    return find_exact([
        REPO / "runtime" / "v46_expert_breadth" / "OUTPUT_V46" / "checkpoint" / "data" / "state_after_v46.csv",
        REPO / "runtime" / "v46_expert_breadth" / "OUTPUT_V46" / "state_after_v46.csv",
        REPO / "runtime" / "v46_expert_breadth" / "OUTPUT_V46" / "bundle" / "state_after_v46.csv",
    ], V46_STATE_SHA, "V46_STATE")


def build_source(v46: Path) -> Path:
    v47 = OUT / "V48DemoPaperObserver.parent_v47.mq5"
    v48a = OUT / "V48DemoPaperObserver.base.a.mq5"
    v48b = OUT / "V48DemoPaperObserver.base.b.mq5"
    run([sys.executable, V47_BUILDER, "--source", v46, "--output", v47])
    if base.sha256(v47) != V47_SOURCE_SHA:
        raise RuntimeError("V47 parent identity lost")
    run([sys.executable, V48_BUILDER, "--source", v47, "--output", v48a])
    run([sys.executable, V48_BUILDER, "--source", v47, "--output", v48b])
    ha, hb = base.sha256(v48a), base.sha256(v48b)
    if ha != hb or ha != V48_SOURCE_SHA:
        raise RuntimeError(f"V48 deterministic source mismatch a={ha} b={hb}")
    print(f"V48_SOURCE_SHA={ha}")
    return v48a


def ensure_compile(source: Path, data: Path, expert_dir: Path) -> Path:
    installed = expert_dir / f"{EXPERT_NAME}.mq5"
    ex5 = installed.with_suffix(".ex5")
    log = installed.with_suffix(".log")
    marker = installed.with_suffix(".compile_source_sha256")

    if not installed.is_file() or base.sha256(installed) != V48_SOURCE_SHA:
        shutil.copy2(source, installed)

    def valid() -> bool:
        if not (installed.is_file() and ex5.is_file() and ex5.stat().st_size > 0 and log.is_file()): return False
        if base.sha256(installed) != V48_SOURCE_SHA: return False
        summary = base.compile_summary(log)
        if not summary or "0 errors, 0 warnings" not in summary.lower(): return False
        return marker.is_file() and marker.read_text(encoding="utf-8", errors="replace").strip() == V48_SOURCE_SHA

    if valid():
        print(f"REUSE V48 COMPILE source_sha={V48_SOURCE_SHA} summary={base.compile_summary(log)}")
        return ex5

    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it before starting V48 paper.")
    for p in (ex5, log, marker):
        try: p.unlink()
        except FileNotFoundError: pass
    cp = subprocess.run([str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data / 'MQL5'}", "/log"])
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")

    def ready():
        if not (ex5.is_file() and ex5.stat().st_size > 0 and log.is_file()): return False
        s = base.compile_summary(log)
        return bool(s and "0 errors, 0 warnings" in s.lower())

    base.wait_until(ready, 120, 0.5, "V48 MetaEditor 0/0 + EX5")
    marker.write_text(V48_SOURCE_SHA + "\n", encoding="utf-8")
    print(base.compile_summary(log))
    return ex5


def seed_paper_state(common: Path) -> Path:
    paper_dir = common / "mt5_quant" / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    paper_state = paper_dir / "v48_demo_paper_state.csv"
    if paper_state.is_file():
        print(f"REUSE V48 PAPER STATE sha256={base.sha256(paper_state)} path={paper_state}")
        return paper_state
    seed = accepted_v46_state()
    shutil.copy2(seed, paper_state)
    if base.sha256(paper_state) != V46_STATE_SHA:
        raise RuntimeError("paper state seed copy mismatch")
    meta = paper_dir / "v48_demo_paper_state_seed.txt"
    meta.write_text("\n".join([
        "schema=v48_demo_paper_state_seed_v1",
        f"seed_sha256={V46_STATE_SHA}",
        "seed_source=accepted_v46_state_after_2026_08_01",
        "historical_midmonth_catchup=0",
        "reason=no_midmonth_tester_EOM_contamination",
        "accepted_v46_state_not_modified=1",
        "",
    ]), encoding="utf-8")
    print(f"V48_PAPER_STATE_SEEDED sha256={V46_STATE_SHA} path={paper_state}")
    return paper_state


def write_startup_ini(data: Path) -> Path:
    ini = data / "config" / "v48_demo_paper_forward.ini"
    # MetaTrader distinguishes enabling EA execution (Enabled=1) from allowing
    # automated broker trading (AllowLiveTrading=0). We need the former so the
    # paper observer runs, and hard-disable the latter.
    text = """[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert=mt5_quant\\V48DemoPaperObserver\nSymbol=XAUUSDm\nPeriod=M15\n"""
    base.write_utf16_ini(ini, text)
    return ini


def decode_mt5_log(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or (raw[:200].count(b"\x00") > 20):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


def collect_attach_diagnostics(data: Path, init_path: Path, label: str) -> str:
    lines = [f"label={label}", f"time={time.strftime('%Y-%m-%d %H:%M:%S')}"]
    if init_path.is_file():
        lines.append("--- V48 INIT DIAGNOSTIC ---")
        lines.extend(init_path.read_text(encoding="utf-8-sig", errors="replace").splitlines())
    else:
        lines.append("V48_INIT_DIAGNOSTIC_MISSING=1")

    candidates = []
    for folder in (data / "logs", data / "MQL5" / "Logs"):
        if folder.is_dir():
            candidates.extend(p for p in folder.glob("*.log") if p.is_file())
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    needles = ("v48", "demopaper", "expert", "cannot load", "failed", "error", "autotrading", "algo trading", "dll", "xauusd")
    for p in candidates:
        try:
            text = decode_mt5_log(p)
        except Exception as exc:
            lines.append(f"LOG_READ_ERROR path={p} error={exc}")
            continue
        matched = [ln for ln in text.splitlines()[-800:] if any(n in ln.lower() for n in needles)]
        if matched:
            lines.append(f"--- LOG {p} ---")
            lines.extend(matched[-80:])

    ATTACH_DIAG.parent.mkdir(parents=True, exist_ok=True)
    ATTACH_DIAG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n=== V48 MT5 ATTACH DIAGNOSTICS ===")
    print("\n".join(lines[-120:]))
    print(f"ATTACH_DIAGNOSTICS_FILE={ATTACH_DIAG}")
    return "\n".join(lines)


def launch_and_verify(data: Path, common: Path) -> None:
    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is already open. Close it once, then rerun this starter so the paper observer can be attached by the startup config.")

    paper_dir = common / "mt5_quant" / "paper"
    status = paper_dir / "V48_DEMO_PAPER_STATUS.txt"
    latest = paper_dir / "V48_DEMO_PAPER_LATEST.txt"
    init_diag = paper_dir / "V48_DEMO_PAPER_INIT.txt"
    if latest.is_file():
        old = parse_kv(latest)
        raise RuntimeError(f"existing V48 paper session metadata found run_id={old.get('run_id','')}; do not silently start a second session. Use STATUS_V48_DEMO_PAPER_GIT_BASH.sh.")

    for p in (status, init_diag):
        try: p.unlink()
        except FileNotFoundError: pass

    ini = write_startup_ini(data)
    say("LAUNCH V48 DEMO-PAPER — real-time feed, virtual book, broker orders impossible")
    print(f"CONFIG={ini}")
    subprocess.Popen([str(base.TERMINAL_EXE), f"/config:{ini}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def status_ready() -> bool:
        if not status.is_file() or status.stat().st_size == 0: return False
        kv = parse_kv(status)
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
        return all(kv.get(k) == v for k, v in required.items())

    deadline = time.time() + 120
    while time.time() < deadline:
        if status_ready():
            break
        if init_diag.is_file():
            init = parse_kv(init_diag)
            if init.get("stage") == "REFUSED":
                collect_attach_diagnostics(data, init_diag, "EA_REFUSED_DURING_ONINIT")
                raise RuntimeError(
                    "V48 EA attached but refused initialization: "
                    f"reason={init.get('reason','')} terminal_trade_allowed={init.get('terminal_trade_allowed','')} "
                    f"mql_trade_allowed={init.get('mql_trade_allowed','')} "
                    f"terminal_dlls_allowed={init.get('terminal_dlls_allowed','')} "
                    f"mql_dlls_allowed={init.get('mql_dlls_allowed','')}"
                )
        if not base.task_running("terminal64.exe"):
            collect_attach_diagnostics(data, init_diag, "TERMINAL_EXITED_BEFORE_READY")
            raise RuntimeError("MT5 terminal exited before V48 paper observer became ready")
        time.sleep(1.0)
    else:
        collect_attach_diagnostics(data, init_diag, "TIMEOUT_WAITING_FOR_V48_READY")
        raise RuntimeError("timeout waiting for V48 paper status; diagnostics were collected above")

    kv = parse_kv(status)
    print("V48_DEMO_PAPER_RUNNING=1")
    print(f"RUN_ID={kv.get('run_id','')}")
    print(f"SESSION_START={kv.get('session_start','')}")
    print(f"BALANCE={kv.get('balance','')}")
    print(f"EQUITY={kv.get('equity','')}")
    print(f"HEALTHY_HL10_COUNT={kv.get('healthy_hl10_count','')}")
    print(f"TERMINAL_TRADE_ALLOWED={kv.get('terminal_trade_allowed','')}")
    print(f"MQL_TRADE_ALLOWED={kv.get('mql_trade_allowed','')} (informational; source contains no broker-order API)")
    print(f"TERMINAL_DLLS_ALLOWED={kv.get('terminal_dlls_allowed','')}")
    print(f"MQL_DLLS_ALLOWED={kv.get('mql_dlls_allowed','')} (informational; source contains no #import)")
    print(f"STATUS_FILE={status}")
    print(f"LATEST_FILE={latest}")
    print("CHART_DASHBOARD=ENABLED")
    print("REAL_MONEY_AUTHORIZED=0")
    print("Keep this terminal on the DEMO account. Do not enable terminal AutoTrading.")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    logf = LOG.open("a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(sys.__stdout__, logf); sys.stderr = Tee(sys.__stderr__, logf)
    say("V48 DEMO-PAPER FORWARD START")
    print("Frozen primary: V46 breadth4. No ADX/DI gate. No broker orders. REAL account refused.")

    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")

    for p in (V45_BASE, V47_BUILDER, V48_BUILDER, STATIC_TEST, SECRET_SCAN):
        if not p.is_file(): raise RuntimeError(f"required file missing: {p}")

    say("Static + secret gates before MetaEditor")
    run([sys.executable, "-m", "py_compile", V47_BUILDER, V48_BUILDER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    data, common, expert_dir, inputs = base.locate_mt5()
    print(f"MT5_DATA={data}")
    base.verify_tape(inputs)
    v46 = accepted_v46_source(expert_dir)
    source = build_source(v46)
    ensure_compile(source, data, expert_dir)
    seed_paper_state(common)
    launch_and_verify(data, common)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
