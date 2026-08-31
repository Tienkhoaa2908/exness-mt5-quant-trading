#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_ONE_SHOT"
ROLLING = OUT / "rolling"
SNAPSHOT = ROLLING / "forward_snapshot"
ANALYZER = REPO / "scripts" / "analyze_v69_forward_trade_quality.py"
ZIP_PATH = OUT / "v69_forward_smoke_final.zip"
LOG = OUT / "V69_FORWARD_SUPERVISOR.log"
OUTPUT_MARKER = OUT / "V69_FORWARD_OUTPUT_READY.txt"

TELEMETRY_FILES = (
    "V64_ENTRY_EVAL.csv",
    "V64_EVENTS.csv",
    "V64_DEALS.csv",
    "V64_SHADOW_RR.csv",
    "V64_NOISE_SHADOW.csv",
    "V64_STATUS.txt",
    "V69_DASHBOARD_HEARTBEAT.txt",
    "V69_SMOKE_PROGRESS.txt",
)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def task_running(image: str) -> bool:
    cp = subprocess.run(
        ["tasklist.exe", "/FI", f"IMAGENAME eq {image}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return image.lower() in cp.stdout.lower()


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").replace("\\r\\n", "\n").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def snapshot_complete_lines(src: Path, dst: Path) -> int:
    if not src.is_file() or src.stat().st_size <= 0:
        return 0
    data = src.read_bytes()
    cut = data.rfind(b"\n")
    if cut < 0:
        return 0
    payload = data[: cut + 1]
    if not payload:
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(payload)
    return len(payload)


def snapshot_root(src_root: Path) -> list[dict]:
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []
    for name in TELEMETRY_FILES:
        src = src_root / name
        dst = SNAPSHOT / name
        size = snapshot_complete_lines(src, dst)
        if size > 0:
            copied.append({"name": name, "bytes": size, "sha256": sha256(dst)})
    return copied


def write_progress(root: Path, *, progress: int, done: str, need: str, output: str,
                   state: str, trades: int, min_trades: int, elapsed_hours: float, hard_cap_hours: int) -> Path:
    path = root / "V69_SMOKE_PROGRESS.txt"
    path.write_text(
        "\n".join([
            f"panel_progress={progress}% | {state} | trades {trades}/{min_trades} | {elapsed_hours:.1f}/{hard_cap_hours}h",
            f"panel_done={done}",
            f"panel_need={need}",
            f"panel_output={output}",
            f"state={state}",
            f"progress_pct={progress}",
            f"closed_trades={trades}",
            f"minimum_closed_trades={min_trades}",
            f"elapsed_hours={elapsed_hours:.3f}",
            f"hard_cap_hours={hard_cap_hours}",
            "real_money_authorized=0",
            "real_money_auto_promotion=0",
        ]) + "\n",
        encoding="utf-8",
    )
    return path


def package(session_path: Path, summary_path: Path, analysis_path: Path, status_path: Path,
            progress_path: Path) -> str:
    files = [session_path, summary_path, analysis_path, status_path, progress_path, LOG, OUTPUT_MARKER]
    files += [p for p in sorted(SNAPSHOT.rglob("*")) if p.is_file()]
    files = [p for p in files if p.is_file()]
    manifest = OUT / "V69_FORWARD_SMOKE_MANIFEST_SHA256.txt"
    rows = []
    for p in files:
        try:
            rel = p.relative_to(OUT).as_posix()
        except ValueError:
            rel = "external/" + p.name
        rows.append(f"{sha256(p)}  {rel}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    files.append(manifest)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in files:
            try:
                arc = p.relative_to(OUT).as_posix()
            except ValueError:
                arc = "external/" + p.name
            zf.write(p, arc)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure first_bad={bad}")
    return sha256(ZIP_PATH)


def notify_output(zip_path: Path) -> None:
    # Best-effort local notice only. Never affects trading or evidence state.
    msg = f"V69 smoke review da xuat xong. ZIP: {zip_path}"
    ps = (
        "Add-Type -AssemblyName PresentationFramework; "
        f"[System.Windows.MessageBox]::Show('{msg.replace(chr(39), chr(39)*2)}','V69 OUTPUT EXPORTED') | Out-Null"
    )
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        log(f"NOTIFY_SKIPPED {type(exc).__name__}: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, type=Path)
    args = ap.parse_args()
    session = json.loads(args.session.read_text(encoding="utf-8"))
    root = Path(session["file_common_root"])
    started = datetime.fromisoformat(session["started_at_utc"])
    min_trades = int(session["smoke_min_closed_trades"])
    hard_cap_hours = int(session["smoke_hard_cap_hours"])
    analyzer = load(ANALYZER, "v69_forward_analyzer_for_smoke_supervisor")

    ROLLING.mkdir(parents=True, exist_ok=True)
    log(f"SUPERVISOR_START root={root} min_trades={min_trades} hard_cap_hours={hard_cap_hours}")
    last_trades = -1
    last_package = 0.0

    while True:
        copied = snapshot_root(root)
        result = analyzer.analyze(SNAPSHOT)
        summary = result.get("summary", {})
        trades = int(summary.get("trades", 0))
        noise_match = float(summary.get("noise_match_rate", 0.0))
        priority = result.get("diagnosis", {}).get("priority", "INSUFFICIENT_SAMPLE")
        elapsed_hours = max(0.0, (datetime.now(timezone.utc) - started).total_seconds() / 3600.0)
        running = task_running("terminal64.exe")
        hb = parse_kv(root / "V69_DASHBOARD_HEARTBEAT.txt")
        ticks = int(hb.get("tick_count", "0") or 0)
        runtime_verified = (
            running and ticks > 0 and hb.get("symbol") == session["symbol"]
            and hb.get("period") == "PERIOD_M15" and hb.get("account_mode") == "0"
            and hb.get("real_money_authorized") == "0"
        )
        trade_gate = trades >= min_trades
        time_cap = elapsed_hours >= hard_cap_hours
        output_ready = runtime_verified and (trade_gate or time_cap)

        if output_ready:
            state = "QUICK_REVIEW_READY" if trade_gate else "TIME_CAP_REVIEW_READY"
            progress = 100
            done = f"runtime verified; telemetry active; {trades} closed trade(s); evidence packaged"
            need = "nothing for DEMO smoke review; review output before any next-stage decision"
            output_text = f"EXPORTED -> {ZIP_PATH.name}"
        elif runtime_verified:
            state = "RUNTIME_VERIFIED_COLLECTING"
            progress = 75 if trades == 0 else 88
            done = f"DEMO init; live ticks={ticks}; telemetry active; strategy frozen"
            remaining = max(0, min_trades - trades)
            need = f"{remaining} more closed trade(s), or wait until {hard_cap_hours}h cap"
            output_text = "NOT YET - rolling evidence saved"
        elif hb:
            state = "HEARTBEAT_WAITING_TICKS"
            progress = 50
            done = "dashboard initialized; heartbeat file exists"
            need = "live market tick / valid DEMO runtime"
            output_text = "NOT YET"
        else:
            state = "STARTING"
            progress = 25
            done = "one-shot launched"
            need = "dashboard heartbeat + live tick"
            output_text = "NOT YET"

        progress_path = write_progress(
            root, progress=progress, done=done, need=need, output=output_text,
            state=state, trades=trades, min_trades=min_trades,
            elapsed_hours=elapsed_hours, hard_cap_hours=hard_cap_hours,
        )
        copied = snapshot_root(root)

        status = {
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "review_state": state,
            "progress_pct": progress,
            "runtime_verified": runtime_verified,
            "closed_trades": trades,
            "minimum_closed_trades": min_trades,
            "elapsed_hours": elapsed_hours,
            "hard_cap_hours": hard_cap_hours,
            "trade_gate_reached": trade_gate,
            "time_cap_reached": time_cap,
            "output_ready": output_ready,
            "noise_match_rate": noise_match,
            "diagnostic_priority": priority,
            "terminal_running": running,
            "dashboard_tick_count": ticks,
            "snapshot_files": copied,
            "real_money_authorized": False,
            "real_money_auto_promotion": False,
            "strategy_changed": False,
        }
        summary_path = ROLLING / "V69_FORWARD_SMOKE_SUMMARY.json"
        analysis_path = ROLLING / "V69_FORWARD_SMOKE_ANALYSIS.json"
        status_path = OUT / "V69_FORWARD_REVIEW_STATUS.txt"
        summary_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        analysis_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        status_path.write_text(
            "\n".join([
                "V69 FROZEN FORWARD DEMO SMOKE REVIEW",
                f"review_state={state}",
                f"progress_pct={progress}",
                f"runtime_verified={int(runtime_verified)}",
                f"closed_trades={trades}",
                f"minimum_closed_trades={min_trades}",
                f"elapsed_hours={elapsed_hours:.3f}",
                f"hard_cap_hours={hard_cap_hours}",
                f"output_ready={int(output_ready)}",
                f"noise_match_rate={noise_match:.4f}",
                f"diagnostic_priority={priority}",
                f"terminal_running={int(running)}",
                f"dashboard_tick_count={ticks}",
                "strategy_changed=0",
                "real_money_authorized=0",
                "real_money_auto_promotion=0",
            ]) + "\n",
            encoding="utf-8",
        )

        now = time.time()
        if output_ready:
            OUTPUT_MARKER.write_text(
                "\n".join([
                    "V69_FORWARD_OUTPUT_READY=1",
                    f"review_state={state}",
                    f"closed_trades={trades}",
                    f"elapsed_hours={elapsed_hours:.3f}",
                    f"zip={ZIP_PATH}",
                    "real_money_authorized=0",
                ]) + "\n",
                encoding="utf-8",
            )
            # Rewrite panel after marker exists, then package final bytes.
            progress_path = write_progress(
                root, progress=100, done=done, need=need,
                output=f"EXPORTED -> {ZIP_PATH.name}", state=state,
                trades=trades, min_trades=min_trades,
                elapsed_hours=elapsed_hours, hard_cap_hours=hard_cap_hours,
            )
            snapshot_root(root)
            digest = package(args.session, summary_path, analysis_path, status_path, progress_path)
            log(f"OUTPUT_EXPORTED state={state} trades={trades} hours={elapsed_hours:.3f} zip_sha256={digest}")
            notify_output(ZIP_PATH)
            return 0

        if trades != last_trades or now - last_package >= 300 or not running:
            digest = package(args.session, summary_path, analysis_path, status_path, progress_path)
            log(f"ROLLING_PACKAGE trades={trades} state={state} progress={progress} zip_sha256={digest}")
            last_trades = trades
            last_package = now

        if not running:
            log("TERMINAL_STOPPED_BEFORE_OUTPUT_READY partial evidence packaged")
            return 0

        time.sleep(15)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"FATAL {type(exc).__name__}: {exc}")
        raise
