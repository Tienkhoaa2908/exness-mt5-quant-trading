#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

EVAL_FILE = "V64_ENTRY_EVAL.csv"


def read_csv_snapshot(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a live CSV defensively and ignore a partial final record."""
    if not path.is_file() or path.stat().st_size <= 0:
        return [], []
    raw = path.read_bytes()
    if not raw:
        return [], []
    if not raw.endswith((b"\n", b"\r")):
        cut = max(raw.rfind(b"\n"), raw.rfind(b"\r"))
        if cut < 0:
            return [], []
        raw = raw[: cut + 1]
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        return [], []
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def int_value(row: dict[str, str], key: str) -> int:
    try:
        return int(float((row.get(key) or "0").strip() or 0))
    except ValueError:
        return 0


def analyze(root: Path) -> dict:
    path = root / EVAL_FILE
    fields, rows = read_csv_snapshot(path)
    decision = Counter((r.get("decision_reason") or "").strip() for r in rows if (r.get("decision_reason") or "").strip())
    reject = Counter((r.get("reject_reason") or "").strip() for r in rows if (r.get("reject_reason") or "").strip())
    selected = Counter(str(int_value(r, "selected_direction")) for r in rows)
    long_scores = [int_value(r, "long_score") for r in rows]
    short_scores = [int_value(r, "short_score") for r in rows]

    rejection_rows = sum(reject.values())
    no_arch = reject.get("no_complete_archetype", 0)
    bad_stop = reject.get("invalid_arm_structural_stop", 0)
    isolated = reject.get("direction_isolated_out", 0)
    pending = sum(v for k, v in reject.items() if k.startswith("pending_"))

    if rows and no_arch > 0 and no_arch >= max(bad_stop, isolated, pending):
        classification = "ARCHETYPE_COMPLETION_BLOCK_BEFORE_PENDING_ARM"
        blocker = "no_complete_archetype"
        next_action = "inspect pullback-sweep and breakout-retest component availability on M15"
    elif rows and bad_stop > 0 and bad_stop >= max(no_arch, isolated, pending):
        classification = "STRUCTURAL_STOP_BLOCK_BEFORE_PENDING_ARM"
        blocker = "invalid_arm_structural_stop"
        next_action = "inspect raw M15 swing stop geometry versus current entry"
    elif rows and isolated > 0 and isolated >= max(no_arch, bad_stop, pending):
        classification = "DIRECTION_ISOLATION_BLOCK_BEFORE_PENDING_ARM"
        blocker = "direction_isolated_out"
        next_action = "count selector LONG versus rejected opposite-direction candidates"
    elif rows and pending > 0:
        classification = "PENDING_EVAL_LOGGED_BUT_PENDING_EVENT_MISSING_REVIEW_TELEMETRY"
        blocker = "pending_eval_without_pending_event"
        next_action = "compare ENTRY_EVAL timestamps with V64_EVENTS writer and pending-state mutation"
    elif rows:
        classification = "PRE_PENDING_DIRECTIONAL_EVAL_OBSERVED"
        blocker = reject.most_common(1)[0][0] if reject else "directional_eval_without_reject_reason"
        next_action = "review decision/reject distributions before adding new live instrumentation"
    else:
        classification = "NO_PRE_PENDING_DIRECTIONAL_EVAL_ROWS"
        blocker = "selector_or_feature_gate_unobserved"
        next_action = "instrument V69 EvaluateBar before d==0 return to distinguish feature readiness, HTF regime, trigger, score and edge gates"

    return {
        "root": str(root),
        "eval_path": str(path),
        "eval_file_present": path.is_file(),
        "header": fields,
        "rows": len(rows),
        "classification": classification,
        "dominant_blocker": blocker,
        "next_action": next_action,
        "decision_reason_counts": dict(decision.most_common(30)),
        "reject_reason_counts": dict(reject.most_common(30)),
        "selected_direction_counts": dict(selected.most_common()),
        "rejection_rows": rejection_rows,
        "long_score_min": min(long_scores) if long_scores else None,
        "long_score_max": max(long_scores) if long_scores else None,
        "short_score_min": min(short_scores) if short_scores else None,
        "short_score_max": max(short_scores) if short_scores else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = analyze(args.root)
    print(f"V69_PRE_PENDING_EVAL_ROWS={result['rows']}")
    print("V69_PRE_PENDING_CLASSIFICATION=" + result["classification"])
    print("V69_PRE_PENDING_TOP_BLOCKER=" + result["dominant_blocker"])
    print("V69_PRE_PENDING_NEXT_ACTION=" + result["next_action"])
    print("V69_PRE_PENDING_DECISION_REASONS=" + json.dumps(result["decision_reason_counts"], sort_keys=True))
    print("V69_PRE_PENDING_REJECT_REASONS=" + json.dumps(result["reject_reason_counts"], sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"V69_PRE_PENDING_JSON={args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
