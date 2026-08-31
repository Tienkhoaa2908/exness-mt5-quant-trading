#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-trade-quality-diagnostics"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_TRADE_QUALITY"
SNAPSHOT = OUT / "forward_snapshot"
HIST_SNAPSHOT = OUT / "historical_v69_development"
ZIP_OUT = OUT / "v69_trade_quality_diagnostics.zip"
ANALYZER = REPO / "scripts" / "analyze_v69_forward_trade_quality.py"
ANALYZER_TEST = REPO / "tests" / "test_v69_forward_trade_quality.py"
RUNTIME_TEST = REPO / "tests" / "test_v69_trade_quality_runtime_static.py"
HIST_ROOT = REPO / "runtime" / "v69_confirm_separation_retest" / "OUTPUT_V69"

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


def run(cmd: list[object]) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=REPO, check=True)


def capture(cmd: list[object]) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=REPO, text=True, encoding="utf-8", errors="replace"
    ).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_repo() -> tuple[str, str]:
    branch = capture(["git", "branch", "--show-current"])
    head = capture(["git", "rev-parse", "HEAD"])
    dirty = capture(["git", "status", "--porcelain"])
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before diagnostics; generated OUTPUT_* is ignored")
    return branch, head


def common_forward_root() -> Path:
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise RuntimeError("APPDATA is not set; cannot locate MT5 Common Files")
    return (
        Path(appdata)
        / "MetaQuotes"
        / "Terminal"
        / "Common"
        / "Files"
        / "mt5_quant"
        / "v69_frozen_forward_demo"
    )


def snapshot_complete_lines(src: Path, dst: Path) -> int:
    """Copy only complete newline-terminated records from a file that may be appended live."""
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


def snapshot_root(src_root: Path, dst_root: Path) -> list[dict]:
    dst_root.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []
    if not src_root.is_dir():
        return copied
    for name in TELEMETRY_FILES:
        src = src_root / name
        dst = dst_root / name
        size = snapshot_complete_lines(src, dst)
        if size > 0:
            copied.append({"name": name, "bytes": size, "sha256": sha256(dst)})
    return copied


def discover_historical_long_runs(root: Path = HIST_ROOT) -> list[Path]:
    if not root.is_dir():
        return []
    runs = []
    for p in sorted(root.iterdir()):
        if not p.is_dir() or not p.name.startswith("holdout_") or not p.name.endswith("_long"):
            continue
        if (p / "V64_DEALS.csv").is_file():
            runs.append(p)
    return runs


def aggregate_historical(results: list[dict]) -> dict:
    summaries = [r.get("summary", {}) for r in results]
    gp = sum(float(s.get("gross_profit_usd", 0.0)) for s in summaries)
    gl = sum(float(s.get("gross_loss_usd", 0.0)) for s in summaries)
    priorities = Counter(r.get("diagnosis", {}).get("priority", "UNKNOWN") for r in results)
    return {
        "development_only_not_independent": True,
        "run_count": len(results),
        "trades": sum(int(s.get("trades", 0)) for s in summaries),
        "wins": sum(int(s.get("wins", 0)) for s in summaries),
        "losses": sum(int(s.get("losses", 0)) for s in summaries),
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": gp - gl,
        "profit_factor": gp / gl if gl > 1e-12 else (999.0 if gp > 1e-12 else 0.0),
        "fast_losses_le_60s": sum(int(s.get("fast_losses", {}).get("60", 0)) for s in summaries),
        "positive_mfe_realized_loss_count": sum(
            int(s.get("mfe_mae", {}).get("positive_mfe_realized_loss_count", 0)) for s in summaries
        ),
        "sub2_peak_roundtrip_loss_count": sum(
            int(s.get("mfe_mae", {}).get("sub2_peak_roundtrip_loss_count", 0)) for s in summaries
        ),
        "mfe_ge_2_realized_below_1_count": sum(
            int(s.get("mfe_mae", {}).get("mfe_ge_2_realized_below_1_count", 0)) for s in summaries
        ),
        "diagnostic_priority_counts": dict(sorted(priorities.items())),
    }


def compact_forward(result: dict) -> dict:
    s = result["summary"]
    q = s["mfe_mae"]
    c15 = s["reentry_clusters"]["15"]
    return {
        "trades": s["trades"],
        "wins": s["wins"],
        "losses": s["losses"],
        "net_usd": s["net_usd"],
        "profit_factor": s["profit_factor"],
        "noise_match_rate": s["noise_match_rate"],
        "fast_losses_le_60s": s["fast_losses"]["60"],
        "median_mfe_losers_usd": q["median_mfe_losers_usd"],
        "median_winner_capture_ratio_of_mfe": q["median_winner_capture_ratio_of_mfe"],
        "positive_mfe_realized_loss_count": q["positive_mfe_realized_loss_count"],
        "sub2_peak_roundtrip_loss_count": q["sub2_peak_roundtrip_loss_count"],
        "mfe_ge_2_realized_below_1_count": q["mfe_ge_2_realized_below_1_count"],
        "loss_after_win_within_15m": c15["loss_after_win"],
        "loss_after_loss_within_15m": c15["loss_after_loss"],
        "explicit_commission_swap_fee_usd": s["turnover"]["explicit_commission_swap_fee_usd"],
        "priority": result["diagnosis"]["priority"],
        "signals": result["diagnosis"]["signals"],
    }


def write_report(branch: str, head: str, forward_root: Path, forward_result: dict, hist_agg: dict) -> Path:
    f = compact_forward(forward_result)
    lines = [
        "V69 TRADE QUALITY DIAGNOSTICS",
        "",
        f"branch={branch}",
        f"head={head}",
        f"created_utc={datetime.now(timezone.utc).isoformat()}",
        "read_only=1",
        "strategy_changed=0",
        "mt5_compile_or_launch=0",
        "frozen_forward_must_remain_unchanged=1",
        "",
        "FORWARD PROSPECTIVE SNAPSHOT",
        f"source={forward_root}",
        f"trades={f['trades']} wins={f['wins']} losses={f['losses']} net_usd={f['net_usd']:.4f} pf={f['profit_factor']:.4f}",
        f"noise_match_rate={f['noise_match_rate']:.4f}",
        f"fast_losses_le_60s={f['fast_losses_le_60s']}",
        f"median_mfe_losers_usd={f['median_mfe_losers_usd']:.4f}",
        f"median_winner_capture_ratio_of_mfe={f['median_winner_capture_ratio_of_mfe']:.4f}",
        f"positive_mfe_realized_loss_count={f['positive_mfe_realized_loss_count']}",
        f"sub2_peak_roundtrip_loss_count={f['sub2_peak_roundtrip_loss_count']}",
        f"mfe_ge_2_realized_below_1_count={f['mfe_ge_2_realized_below_1_count']}",
        f"loss_after_win_within_15m={f['loss_after_win_within_15m']}",
        f"loss_after_loss_within_15m={f['loss_after_loss_within_15m']}",
        f"explicit_commission_swap_fee_usd={f['explicit_commission_swap_fee_usd']:.4f}",
        f"priority={f['priority']}",
        "signals=" + (",".join(f["signals"]) if f["signals"] else "NONE"),
        "",
        "HISTORICAL V69 DEVELOPMENT DIAGNOSTIC (NOT INDEPENDENT)",
        f"runs={hist_agg['run_count']} trades={hist_agg['trades']} wins={hist_agg['wins']} losses={hist_agg['losses']}",
        f"net_usd={hist_agg['net_usd']:.4f} pf={hist_agg['profit_factor']:.4f}",
        f"fast_losses_le_60s={hist_agg['fast_losses_le_60s']}",
        f"positive_mfe_realized_loss_count={hist_agg['positive_mfe_realized_loss_count']}",
        f"sub2_peak_roundtrip_loss_count={hist_agg['sub2_peak_roundtrip_loss_count']}",
        f"mfe_ge_2_realized_below_1_count={hist_agg['mfe_ge_2_realized_below_1_count']}",
        "priority_counts=" + json.dumps(hist_agg["diagnostic_priority_counts"], sort_keys=True),
        "",
        "DECISION RULE",
        "Do not mutate V69 frozen parameters from this run. Use prospective forward evidence for promotion/failure decisions.",
        "Historical output is development diagnosis only and may guide architecture hypotheses, not claim a new holdout.",
        "MFE/MAE are price-PnL excursions from OrderCalcProfit and are interpreted separately from explicit commission/swap/fee.",
    ]
    path = OUT / "V69_TRADE_QUALITY_REPORT.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest_and_zip() -> tuple[Path, str]:
    manifest = OUT / "V69_TRADE_QUALITY_MANIFEST_SHA256.txt"
    files = [p for p in sorted(OUT.rglob("*")) if p.is_file() and p not in (manifest, ZIP_OUT)]
    rows = [f"{sha256(p)}  {p.relative_to(OUT).as_posix()}" for p in files]
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")

    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        got = sha256(OUT / rel)
        if got != expected:
            raise RuntimeError(f"manifest mismatch: {rel}")

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    members = files + [manifest]
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in members:
            zf.write(p, p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(ZIP_OUT) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure first_bad={bad}")
    return ZIP_OUT, sha256(ZIP_OUT)


def main() -> int:
    branch, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", ANALYZER, ANALYZER_TEST, RUNTIME_TEST, Path(__file__)])
    run([sys.executable, ANALYZER_TEST])
    run([sys.executable, RUNTIME_TEST])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    analyzer = load(ANALYZER, "v69_trade_quality_analyzer")
    forward_root = common_forward_root()
    copied = snapshot_root(forward_root, SNAPSHOT)
    print(f"FORWARD_ROOT={forward_root}")
    print(f"FORWARD_SNAPSHOT_FILES={len(copied)}")
    forward_result = analyzer.analyze(SNAPSHOT)
    (OUT / "V69_FORWARD_TRADE_QUALITY.json").write_text(
        json.dumps(forward_result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    historical_results: list[dict] = []
    historical_runs = discover_historical_long_runs()
    for src in historical_runs:
        dst = HIST_SNAPSHOT / src.name
        snapshot_root(src, dst)
        result = analyzer.analyze(dst)
        result["historical_source_run"] = src.name
        result["development_only_not_independent"] = True
        historical_results.append(result)
    hist_agg = aggregate_historical(historical_results)
    (OUT / "V69_HISTORICAL_DEVELOPMENT_TRADE_QUALITY.json").write_text(
        json.dumps({"aggregate": hist_agg, "runs": historical_results}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "protocol": "v69_trade_quality_diagnostics_v1",
        "branch": branch,
        "head": head,
        "read_only": True,
        "strategy_changed": False,
        "mt5_compile_or_launch": False,
        "forward_source": str(forward_root),
        "forward_snapshot_files": copied,
        "forward": compact_forward(forward_result),
        "historical_v69_development": hist_agg,
    }
    (OUT / "V69_TRADE_QUALITY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(branch, head, forward_root, forward_result, hist_agg)
    zip_path, zip_sha = write_manifest_and_zip()

    f = summary["forward"]
    print(
        "V69_TRADE_QUALITY_DONE=1 "
        f"forward_trades={f['trades']} priority={f['priority']} "
        f"historical_runs={hist_agg['run_count']} historical_trades={hist_agg['trades']}"
    )
    print(f"V69_TRADE_QUALITY_ZIP={zip_path}")
    print(f"V69_TRADE_QUALITY_ZIP_SHA256={zip_sha}")
    print("MT5_DEMO_CAN_REMAIN_RUNNING=1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
