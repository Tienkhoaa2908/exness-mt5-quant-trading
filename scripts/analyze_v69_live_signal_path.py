#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

STAGES = (
    "POST_ZONE_REVERSAL_CONFIRM",
    "POST_CONFIRM_SEPARATION",
    "POST_CONFIRM_RETEST_READY",
    "POST_CONFIRM_ENTRY_READY",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def count_closed_deals(path: Path) -> int:
    rows = read_csv(path)
    total = 0
    for row in rows:
        try:
            entry = int(float(row.get("entry", "0") or 0))
        except ValueError:
            entry = 0
        if entry != 0:
            total += 1
    return total


def analyze(root: Path) -> dict:
    events_path = root / "V64_EVENTS.csv"
    deals_path = root / "V64_DEALS.csv"
    events = read_csv(events_path)
    event_counts = Counter((r.get("event") or "").strip() for r in events)
    details = Counter((r.get("detail") or "").strip() for r in events if (r.get("detail") or "").strip())
    stage_counts = {stage: int(event_counts.get(stage, 0)) for stage in STAGES}
    closed = count_closed_deals(deals_path)

    confirm = stage_counts["POST_ZONE_REVERSAL_CONFIRM"]
    sep = stage_counts["POST_CONFIRM_SEPARATION"]
    retest = stage_counts["POST_CONFIRM_RETEST_READY"]
    ready = stage_counts["POST_CONFIRM_ENTRY_READY"]

    if ready > 0 and closed == 0:
        classification = "ENTRY_READY_WITHOUT_CLOSED_TRADE_ORDER_PATH_REVIEW"
        next_gate = "inspect order/preflight/send events around POST_CONFIRM_ENTRY_READY"
    elif retest > 0 and ready == 0:
        classification = "RETEST_REACHED_ENTRY_BUILD_OR_PREFLIGHT_BLOCK"
        next_gate = "inspect reject/detail counters after retest"
    elif sep > 0 and retest == 0:
        classification = "SEPARATION_REACHED_RETEST_NOT_REACHED"
        next_gate = "cash-risk-zone/age/retest gate is suppressing entries"
    elif confirm > 0 and sep == 0:
        classification = "RECLAIM_CONFIRM_REACHED_SEPARATION_NOT_REACHED"
        next_gate = "post-confirm separation gate is suppressing entries"
    elif confirm == 0:
        classification = "NO_V69_RECLAIM_CONFIRM_OBSERVED"
        next_gate = "upstream setup/reclaim conditions did not reach V69 confirmation"
    elif closed > 0:
        classification = "NATURAL_EXECUTION_OBSERVED"
        next_gate = "review trade quality"
    else:
        classification = "SIGNAL_PATH_INDETERMINATE"
        next_gate = "inspect full event/detail counters"

    suspicious_details = {
        k: v
        for k, v in details.most_common(40)
        if any(token in k.lower() for token in ("wait", "reject", "risk", "spread", "confirm", "retest", "separation", "zone"))
    }

    return {
        "root": str(root),
        "events_file_present": events_path.is_file(),
        "deals_file_present": deals_path.is_file(),
        "events_rows": len(events),
        "closed_deals": closed,
        "stage_counts": stage_counts,
        "classification": classification,
        "next_gate": next_gate,
        "top_event_counts": dict(event_counts.most_common(50)),
        "diagnostic_detail_counts": suspicious_details,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = analyze(args.root)
    print("V69_SIGNAL_PATH_CLASSIFICATION=" + result["classification"])
    for stage, value in result["stage_counts"].items():
        print(f"V69_SIGNAL_STAGE_{stage}={value}")
    print(f"V69_SIGNAL_CLOSED_DEALS={result['closed_deals']}")
    print("V69_SIGNAL_NEXT_GATE=" + result["next_gate"])
    if result["diagnostic_detail_counts"]:
        print("V69_SIGNAL_TOP_DIAGNOSTIC_DETAILS=" + json.dumps(result["diagnostic_detail_counts"], ensure_ascii=False, sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"V69_SIGNAL_PATH_JSON={args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
