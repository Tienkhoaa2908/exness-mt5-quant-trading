#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "RUN_V55_ACCOUNT_AGNOSTIC.py"
FIXED_BUILDER = HERE.parents[1] / "scripts" / "build_v55_account_agnostic_source_windows_fixed.py"
READY_TIMEOUT_SECONDS = 60
DIAG_AFTER_SECONDS = 15


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(TARGET, "v55_account_agnostic_base")
# Windows/runtime launches must use the corrected builder that removes the
# inherited V48 DEMO-only OnInit guard before the V55 same-binary transform.
v55.BUILDER = FIXED_BUILDER


def decode_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-16", "utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def print_relevant_tail(path: Path, max_lines: int = 40) -> None:
    try:
        lines = decode_text(path).splitlines()
    except (OSError, PermissionError) as exc:
        print(f"V55_DIAG_LOG_READ_FAILED path={path} error={type(exc).__name__}:{exc}")
        return
    tail = lines[-160:]
    tokens = (
        "v55",
        "v50",
        "expert",
        "xauusdm",
        "m15",
        "algo",
        "auto",
        "trade",
        "initialized",
        "initialization",
        "failed",
        "error",
        "refused",
        "removed",
    )
    relevant = [line for line in tail if any(tok in line.lower() for tok in tokens)]
    show = relevant[-max_lines:] if relevant else tail[-min(max_lines, 20):]
    print(f"--- V55_DIAG_LOG path={path} lines={len(show)} ---")
    for line in show:
        print(line)


def latest_mt5_logs(data: Path) -> None:
    for log_dir in (data / "MQL5" / "Logs", data / "logs"):
        if not log_dir.is_dir():
            print(f"V55_DIAG_LOG_DIR_MISSING={log_dir}")
            continue
        try:
            logs = sorted(
                (p for p in log_dir.glob("*.log") if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:2]
        except OSError as exc:
            print(f"V55_DIAG_LOG_LIST_FAILED path={log_dir} error={type(exc).__name__}:{exc}")
            continue
        if not logs:
            print(f"V55_DIAG_NO_LOGS={log_dir}")
            continue
        for path in logs:
            print_relevant_tail(path)


def recent_common_diagnostics(common: Path, started: float) -> None:
    root = common / "mt5_quant"
    if not root.is_dir():
        print(f"V55_DIAG_COMMON_ROOT_MISSING={root}")
        return
    candidates: list[Path] = []
    try:
        for p in root.rglob("*.txt"):
            if not p.is_file():
                continue
            upper = p.name.upper()
            if "STATUS" not in upper and "INIT" not in upper and "FINAL" not in upper:
                continue
            try:
                if p.stat().st_mtime >= started - 120:
                    candidates.append(p)
            except OSError:
                continue
    except OSError as exc:
        print(f"V55_DIAG_COMMON_SCAN_FAILED error={type(exc).__name__}:{exc}")
        return
    for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:8]:
        print_relevant_tail(path, max_lines=30)


def diagnostic_snapshot(common: Path, started: float) -> None:
    print("============================================================")
    print("=== V55 WINDOWS STARTUP DIAGNOSTICS ===")
    print(f"TERMINAL64_RUNNING={1 if v55.base.task_running('terminal64.exe') else 0}")
    status = common / "mt5_quant" / "v55" / "V55_PRODUCTION_READINESS_STATUS.txt"
    if status.is_file():
        try:
            print(f"V55_STATUS_PATH={status}")
            print(f"V55_STATUS_MTIME={status.stat().st_mtime}")
            print_relevant_tail(status, max_lines=60)
        except OSError as exc:
            print(f"V55_STATUS_READ_FAILED={type(exc).__name__}:{exc}")
    else:
        print(f"V55_STATUS_MISSING={status}")
    try:
        data, _, _, _ = v55.base.locate_mt5()
        print(f"V55_DIAG_MT5_DATA={data}")
        latest_mt5_logs(data)
    except Exception as exc:
        print(f"V55_DIAG_LOCATE_MT5_FAILED={type(exc).__name__}:{exc}")
    recent_common_diagnostics(common, started)
    print("=== END V55 WINDOWS STARTUP DIAGNOSTICS ===")
    print("============================================================")


def readiness_mismatches(s: dict[str, str], execution_mode: str) -> list[str]:
    expected_account = "REAL" if execution_mode == "real" else "DEMO"
    expected_activation = "REAL_ARMED" if execution_mode == "real" else "DEMO_ACTIVE"
    expected_real_auth = "1" if execution_mode == "real" else "0"
    expected = {
        "account_mode": expected_account,
        "terminal_trade_allowed": "1",
        "mql_trade_allowed": "1",
        "terminal_dlls_allowed": "0",
        "real_money_authorized": expected_real_auth,
        "production_activation": expected_activation,
        "candidate": "v52_b4_or_b3_trend_bos",
    }
    out = [
        f"{key}={s.get(key, '<missing>')} expected={value}"
        for key, value in expected.items()
        if s.get(key) != value
    ]
    if not s.get("run_id", "").strip():
        out.append("run_id=<missing>")
    return out


def fast_wait_ready(common: Path, execution_mode: str) -> dict[str, str]:
    status = common / "mt5_quant" / "v55" / "V55_PRODUCTION_READINESS_STATUS.txt"
    started = time.time()
    deadline = started + READY_TIMEOUT_SECONDS
    next_progress = started
    diag_printed = False

    while time.time() < deadline:
        now = time.time()
        s: dict[str, str] = {}
        fresh = False
        try:
            if status.is_file() and status.stat().st_mtime >= started - 5:
                fresh = True
                s = v55.kv_retry(status, attempts=1)
        except (OSError, PermissionError):
            s = {}

        if s:
            if s.get("halted") == "1":
                diagnostic_snapshot(common, started)
                raise RuntimeError(f"V55 halted during startup reason={s.get('halt_reason','')}")

            expected_account = "REAL" if execution_mode == "real" else "DEMO"
            actual_account = s.get("account_mode", "")
            if actual_account and actual_account != expected_account:
                diagnostic_snapshot(common, started)
                raise RuntimeError(
                    f"logged MT5 account mode mismatch expected={expected_account} actual={actual_account}"
                )

            for key, bad_value, message in (
                ("terminal_trade_allowed", "0", "MT5 Algo Trading is disabled at terminal level"),
                ("mql_trade_allowed", "0", "EA live-trading permission is disabled"),
                ("terminal_dlls_allowed", "1", "DLL permission must be OFF"),
            ):
                if s.get(key) == bad_value:
                    diagnostic_snapshot(common, started)
                    raise RuntimeError(f"V55 startup preflight failed: {message}")

            mismatches = readiness_mismatches(s, execution_mode)
            if not mismatches:
                print(f"V55_ACCOUNT_AGNOSTIC_READY=1 mode={execution_mode}")
                return s

            if now >= next_progress:
                print("V55_READY_WAIT=" + "; ".join(mismatches))
                next_progress = now + 5
        elif now >= next_progress:
            age = int(now - started)
            stale_note = "fresh_status=0" if not fresh else "fresh_status=1_empty"
            print(
                f"V55_READY_WAIT_SECONDS={age} {stale_note} "
                f"terminal_running={1 if v55.base.task_running('terminal64.exe') else 0}"
            )
            next_progress = now + 5

        if not v55.base.task_running("terminal64.exe"):
            diagnostic_snapshot(common, started)
            raise RuntimeError("MT5 exited before V55 READY")

        if not diag_printed and now - started >= DIAG_AFTER_SECONDS and not s:
            diagnostic_snapshot(common, started)
            diag_printed = True

        time.sleep(1)

    diagnostic_snapshot(common, started)
    raise RuntimeError(f"V55 READY timeout after {READY_TIMEOUT_SECONDS}s; diagnostics printed above")


def main() -> int:
    if not FIXED_BUILDER.is_file():
        raise RuntimeError(f"V55 fixed builder missing: {FIXED_BUILDER}")
    if v55.base.task_running("terminal64.exe"):
        raise RuntimeError(
            "MetaTrader 5 is already open. Close the existing terminal first; "
            "the V55 gate refuses to kill or replace a running account session."
        )
    if v55.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is already open. Close it before V55 start.")

    print(f"V55_WINDOWS_BUILDER={FIXED_BUILDER}")
    v55.wait_ready = fast_wait_ready
    return v55.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
