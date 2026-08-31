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
ZIP_PATH = OUT / "v69_forward_prospective_latest.zip"
LOG = OUT / "V69_FORWARD_SUPERVISOR.log"

TELEMETRY_FILES = (
    "V64_ENTRY_EVAL.csv",
    "V64_EVENTS.csv",
    "V64_DEALS.csv",
    "V64_SHADOW_RR.csv",
    "V64_NOISE_SHADOW.csv",
    "V64_STATUS.txt",
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
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return image.lower() in cp.stdout.lower()


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


def package(session_path: Path, summary_path: Path, analysis_path: Path, status_path: Path) -> str:
    files = [session_path, summary_path, analysis_path, status_path, LOG]
    files += [p for p in sorted(SNAPSHOT.rglob("*")) if p.is_file()]
    files = [p for p in files if p.is_file()]
    manifest = OUT / "V69_FORWARD_PROSPECTIVE_MANIFEST_SHA256.txt"
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, type=Path)
    args = ap.parse_args()
    session = json.loads(args.session.read_text(encoding="utf-8"))
    root = Path(session["file_common_root"])
    started = datetime.fromisoformat(session["started_at_utc"])
    min_trades = int(session["early_review_min_closed_trades"])
    min_days = int(session["early_review_min_elapsed_days"])
    analyzer = load(ANALYZER, "v69_forward_analyzer_for_supervisor")

    ROLLING.mkdir(parents=True, exist_ok=True)
    last_trades = -1
    last_package = 0.0
    log(f"SUPERVISOR_START root={root} min_trades={min_trades} min_days={min_days}")

    while True:
        copied = snapshot_root(root)
        result = analyzer.analyze(SNAPSHOT)
        summary = result.get("summary", {})
        trades = int(summary.get("trades", 0))
        elapsed_days = max(0.0, (datetime.now(timezone.utc) - started).total_seconds() / 86400.0)
        noise_match = float(summary.get("noise_match_rate", 0.0))
        priority = result.get("diagnosis", {}).get("priority", "INSUFFICIENT_SAMPLE")

        if trades >= min_trades and elapsed_days >= min_days:
            review_state = "EARLY_REVIEW_READY" if noise_match >= 0.70 else "TELEMETRY_MATCH_TOO_LOW"
        else:
            review_state = "COLLECTING"

        running = task_running("terminal64.exe")
        status = {
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "review_state": review_state,
            "closed_trades": trades,
            "elapsed_days": elapsed_days,
            "minimum_closed_trades": min_trades,
            "minimum_elapsed_days": min_days,
            "noise_match_rate": noise_match,
            "diagnostic_priority": priority,
            "terminal_running": running,
            "snapshot_files": copied,
            "real_money_authorized": False,
            "real_money_auto_promotion": False,
            "strategy_changed": False,
        }
        summary_path = ROLLING / "V69_FORWARD_ROLLING_SUMMARY.json"
        analysis_path = ROLLING / "V69_FORWARD_ROLLING_ANALYSIS.json"
        status_path = OUT / "V69_FORWARD_REVIEW_STATUS.txt"
        summary_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        analysis_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        status_path.write_text(
            "\n".join([
                "V69 FROZEN PROSPECTIVE DEMO",
                f"review_state={review_state}",
                f"closed_trades={trades}",
                f"elapsed_days={elapsed_days:.3f}",
                f"noise_match_rate={noise_match:.4f}",
                f"diagnostic_priority={priority}",
                f"terminal_running={int(running)}",
                "strategy_changed=0",
                "real_money_authorized=0",
                "real_money_auto_promotion=0",
                "note=EARLY_REVIEW_READY means evidence is ready for review; it is not automatic real-money authorization.",
            ]) + "\n",
            encoding="utf-8",
        )

        now = time.time()
        if trades != last_trades or now - last_package >= 3600 or not running:
            digest = package(args.session, summary_path, analysis_path, status_path)
            log(
                f"PACKAGE trades={trades} elapsed_days={elapsed_days:.3f} state={review_state} "
                f"priority={priority} zip_sha256={digest}"
            )
            last_trades = trades
            last_package = now

        if not running:
            log("TERMINAL_STOPPED supervisor final package complete")
            return 0

        time.sleep(60)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"FATAL {type(exc).__name__}: {exc}")
        raise
