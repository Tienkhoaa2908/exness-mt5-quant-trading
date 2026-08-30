#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "analyze_v64_microstructure_trigger_shadow.py"

STAGE_EVENTS = (
    "MICRO_ENTRY_ARM",
    "MICRO_ENTRY_REFRESH",
    "MICRO_ENTRY_WAIT",
    "MICRO_ENTRY_ZONE_TOUCH",
    "MICRO_ENTRY_INVALIDATE",
    "MICRO_ENTRY_EXPIRE",
    "MICRO_ENTRY_BLOCK",
    "MICRO_ENTRY_END",
)


def read_events(run_dir: Path):
    p = run_dir / "V64_EVENTS.csv"
    if not p.is_file():
        return []
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args = ap.parse_args()

    cmd = [sys.executable, str(BASE)]
    for rd in args.run_dir:
        cmd += ["--run-dir", str(rd)]
    cmd += ["--output", str(args.output), "--summary", str(args.summary)]
    subprocess.run(cmd, check=True)

    data = json.loads(args.output.read_text(encoding="utf-8"))
    stage = {}
    total_events = Counter()
    total_details = Counter()
    for rd in args.run_dir:
        rows = read_events(rd)
        ec = Counter(r.get("event", "") for r in rows)
        dc = Counter(
            f"{r.get('event','')}:{r.get('detail','')}"
            for r in rows
            if r.get("event", "") in STAGE_EVENTS
        )
        stage[rd.name] = {
            "events": {k: ec.get(k, 0) for k in STAGE_EVENTS},
            "details": dict(sorted(dc.items())),
        }
        for k in STAGE_EVENTS:
            total_events[k] += ec.get(k, 0)
        total_details.update(dc)

    data["v66_post_bos_cash_zone"] = {
        "contract": {
            "fixed_lot": 0.01,
            "planned_risk_band_cash": [0.85, 1.25],
            "emergency_loss_cash": 1.20,
            "actual_target_cash": 3.50,
            "min_risk_spread_ratio": 4.0,
            "micro_entry_ttl_minutes": 30,
        },
        "stage2_by_run": stage,
        "stage2_total_events": dict(total_events),
        "stage2_total_details": dict(sorted(total_details.items())),
    }
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    text = args.summary.read_text(encoding="utf-8", errors="replace")
    text = text.replace("V64_MICROSTRUCTURE_TRIGGER_SHADOW_ANALYSIS", "V66_POST_BOS_CASH_ZONE_ANALYSIS")
    text = text.replace("PLANNED_RISK_BAND_CASH=0.85,1.20", "PLANNED_RISK_BAND_CASH=0.85,1.25")
    text = text.replace("EMERGENCY_LOSS_CASH=1.15", "EMERGENCY_LOSS_CASH=1.20")
    text += "\nV66_STAGE2_TOTAL=" + json.dumps(dict(total_events), sort_keys=True) + "\n"
    text += "V66_STAGE2_DETAILS=" + json.dumps(dict(sorted(total_details.items())), sort_keys=True) + "\n"
    args.summary.write_text(text, encoding="utf-8")
    print("V66_ANALYZER_PASS=1")
    print("V66_STAGE2_TOTAL=" + json.dumps(dict(total_events), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
