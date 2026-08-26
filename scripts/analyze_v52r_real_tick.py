#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
V52_ANALYZER = REPO / "scripts" / "analyze_v52_source_aware.py"
BASELINE = "v46_hl10_thr0p05_breadth4"
ACCEPTED_V51_BASELINE_TRADES = 825
MAX_PRICE_RATIO = 1.25
MAX_ABS_R = 10.0


def data_integrity(trades: pd.DataFrame) -> dict:
    required = ("entry", "exit", "r_multiple", "entry_time", "exit_time", "candidate", "book")
    missing = [c for c in required if c not in trades.columns]
    if missing:
        return {
            "pass": False,
            "reason": "missing_columns",
            "missing_columns": missing,
            "anomaly_rows": None,
        }

    entry = pd.to_numeric(trades["entry"], errors="coerce")
    exit_ = pd.to_numeric(trades["exit"], errors="coerce")
    r = pd.to_numeric(trades["r_multiple"], errors="coerce")

    finite = entry.map(math.isfinite) & exit_.map(math.isfinite) & r.map(math.isfinite)
    positive = (entry > 0) & (exit_ > 0)
    safe_entry = entry.where(entry > 0)
    safe_exit = exit_.where(exit_ > 0)
    ratio = pd.concat([safe_exit / safe_entry, safe_entry / safe_exit], axis=1).max(axis=1)

    bad_ratio = ratio > MAX_PRICE_RATIO
    bad_r = r.abs() > MAX_ABS_R
    bad = (~finite) | (~positive) | bad_ratio.fillna(True) | bad_r.fillna(True)

    bad_rows = trades.loc[bad, ["entry_time", "exit_time", "candidate", "book", "entry", "exit", "r_multiple"]].copy()
    if not bad_rows.empty:
        bad_rows["price_ratio"] = ratio.loc[bad_rows.index]

    max_ratio = float(ratio.max()) if len(ratio) and ratio.notna().any() else None
    max_abs_r = float(r.abs().max()) if len(r) and r.notna().any() else None

    sample = bad_rows.head(100).to_dict(orient="records")
    return {
        "pass": bool(bad.sum() == 0),
        "reason": "clean" if int(bad.sum()) == 0 else "pathological_trade_price_or_r",
        "rows": int(len(trades)),
        "anomaly_rows": int(bad.sum()),
        "max_price_ratio": max_ratio,
        "max_abs_r": max_abs_r,
        "limits": {
            "max_price_ratio": MAX_PRICE_RATIO,
            "max_abs_r": MAX_ABS_R,
        },
        "anomaly_sample": sample,
    }


def write_fail_outputs(output: Path, summary_csv: Path, monthly_csv: Path, report: dict) -> None:
    payload = {
        "schema": "v52r_real_tick_repro_v1",
        "status": "V52R_DATA_INTEGRITY_FAIL",
        "selected_candidate": BASELINE,
        "tester_model": 4,
        "data_integrity": report,
        "decision": "No alpha conclusion is permitted from a contaminated historical run.",
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame([{
        "status": payload["status"],
        "selected_candidate": BASELINE,
        "anomaly_rows": report.get("anomaly_rows"),
        "max_price_ratio": report.get("max_price_ratio"),
        "max_abs_r": report.get("max_abs_r"),
    }]).to_csv(summary_csv, index=False)
    pd.DataFrame(columns=["candidate", "month"]).to_csv(monthly_csv, index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-folder", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary-csv", required=True)
    ap.add_argument("--monthly-csv", required=True)
    ap.add_argument("--integrity-json", required=True)
    ns = ap.parse_args()

    run = Path(ns.run_folder)
    output = Path(ns.output)
    summary_csv = Path(ns.summary_csv)
    monthly_csv = Path(ns.monthly_csv)
    integrity_json = Path(ns.integrity_json)

    trades_path = run / "trades.csv"
    if not trades_path.is_file() or trades_path.stat().st_size == 0:
        raise RuntimeError(f"missing trades.csv: {trades_path}")

    trades = pd.read_csv(trades_path)
    report = data_integrity(trades)
    integrity_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"V52R_DATA_INTEGRITY_PASS={1 if report.get('pass') else 0}")
    print(f"V52R_ANOMALY_ROWS={report.get('anomaly_rows')}")
    print(f"V52R_MAX_PRICE_RATIO={report.get('max_price_ratio')}")
    print(f"V52R_MAX_ABS_R={report.get('max_abs_r')}")

    if not report.get("pass"):
        write_fail_outputs(output, summary_csv, monthly_csv, report)
        print("STATUS=V52R_DATA_INTEGRITY_FAIL")
        print(f"SELECTED={BASELINE}")
        return 0

    subprocess.run([
        sys.executable,
        str(V52_ANALYZER),
        "--run-folder", str(run),
        "--output", str(output),
        "--summary-csv", str(summary_csv),
        "--monthly-csv", str(monthly_csv),
    ], check=True)

    payload = json.loads(output.read_text(encoding="utf-8"))
    raw_status = payload.get("status", "")
    if raw_status == "V52_CHALLENGER_SELECTED":
        status = "V52R_CHALLENGER_SELECTED"
    elif raw_status == "V52_KEEP_BREADTH4":
        status = "V52R_KEEP_BREADTH4"
    else:
        raise RuntimeError(f"unexpected V52 analyzer status: {raw_status}")

    baseline = next((x for x in payload.get("candidates", []) if x.get("candidate") == BASELINE), None)
    baseline_trades = int(baseline.get("trades")) if baseline and baseline.get("trades") is not None else None
    payload["schema"] = "v52r_real_tick_repro_v1"
    payload["v52_raw_status"] = raw_status
    payload["status"] = status
    payload["tester_model"] = 4
    payload["data_integrity"] = report
    payload["accepted_v51_baseline_trades_reference"] = ACCEPTED_V51_BASELINE_TRADES
    payload["real_tick_baseline_trades"] = baseline_trades
    payload["baseline_trade_delta_vs_v51"] = None if baseline_trades is None else baseline_trades - ACCEPTED_V51_BASELINE_TRADES
    payload["decision_note"] = (
        "V52R keeps the V52 source-aware hypothesis frozen and changes only the tester tick model to real ticks. "
        "Selection is relative to the clean breadth4 baseline inside this same real-tick run."
    )
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"STATUS={status}")
    print(f"SELECTED={payload.get('selected_candidate')}")
    print(f"REAL_TICK_BASELINE_TRADES={baseline_trades}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
