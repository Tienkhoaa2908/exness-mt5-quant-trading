#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

FUNNEL_STAGES = (
    "PENDING_ARM",
    "MICRO_ENTRY_ARM",
    "MICRO_ENTRY_ZONE_TOUCH",
    "MICRO_ENTRY_PENETRATION",
    "POST_ZONE_CONFIRM_WAIT",
    "POST_ZONE_REVERSAL_CONFIRM",
    "POST_CONFIRM_SEPARATION",
    "POST_CONFIRM_RETEST_READY",
    "POST_CONFIRM_ENTRY_READY",
)

AUX_EVENTS = (
    "POST_ZONE_CONFIRM_INVALIDATE",
    "POST_ZONE_CONFIRM_EXPIRE",
    "MICRO_ENTRY_WAIT",
)

KNOWN_CONFIRM_WAIT_REASONS = (
    "zone_penetration_not_ready",
    "m1_history_not_ready",
    "closed_bar_predates_zone_touch",
    "m1_atr_not_ready",
    "reclaim_body_too_small",
    "reclaim_body_fraction_weak",
    "reclaim_close_location_weak",
    "reclaim_candle_wrong_direction",
    "reclaim_no_close_progress",
    "reclaim_distance_from_extreme_weak",
)


def read_csv_snapshot(path: Path) -> list[dict[str, str]]:
    """Read a CSV without ever mutating it; discard a possibly partial live tail."""
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    raw = path.read_bytes()
    if not raw:
        return []
    # A live FILE_COMMON writer can be between writes. A non-newline final record is
    # treated as partial and ignored rather than guessed.
    if not raw.endswith((b"\n", b"\r")):
        cut = max(raw.rfind(b"\n"), raw.rfind(b"\r"))
        if cut < 0:
            return []
        raw = raw[: cut + 1]
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        return []
    return list(csv.DictReader(io.StringIO(text, newline="")))


def count_closed_deals(path: Path) -> int:
    total = 0
    for row in read_csv_snapshot(path):
        try:
            entry = int(float((row.get("entry") or "0").strip() or 0))
        except ValueError:
            entry = 0
        if entry != 0:
            total += 1
    return total


def normalize_reason(detail: str) -> str:
    value = (detail or "").strip()
    low = value.lower()
    for reason in KNOWN_CONFIRM_WAIT_REASONS:
        if reason in low:
            return reason
    match = re.search(r"(?:^|[\s,;|])reason=([^\s,;|]+)", value, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    if value and len(value) <= 96 and "=" not in value:
        return value.lower()
    return "unclassified_detail"


def classify(stage: dict[str, int], wait_reasons: Counter[str], closed: int) -> tuple[str, str, str]:
    pending = stage["PENDING_ARM"]
    micro = stage["MICRO_ENTRY_ARM"]
    touch = stage["MICRO_ENTRY_ZONE_TOUCH"]
    penetration = stage["MICRO_ENTRY_PENETRATION"]
    wait = stage["POST_ZONE_CONFIRM_WAIT"]
    confirm = stage["POST_ZONE_REVERSAL_CONFIRM"]
    separation = stage["POST_CONFIRM_SEPARATION"]
    retest = stage["POST_CONFIRM_RETEST_READY"]
    ready = stage["POST_CONFIRM_ENTRY_READY"]

    top_wait = wait_reasons.most_common(1)[0][0] if wait_reasons else "none"

    if ready > 0 and closed == 0:
        return (
            "ENTRY_READY_WITHOUT_NATURAL_CLOSE_ORDER_PATH_REVIEW",
            "POST_CONFIRM_ENTRY_READY",
            "inspect integrated V69 preflight/send events",
        )
    if retest > 0 and ready == 0:
        return (
            "RETEST_REACHED_ENTRY_READY_NOT_REACHED",
            "POST_CONFIRM_ENTRY_READY",
            "inspect confirmation-age/risk/build/preflight gating",
        )
    if separation > 0 and retest == 0:
        return (
            "SEPARATION_REACHED_RETEST_NOT_REACHED",
            "POST_CONFIRM_RETEST_READY",
            "retest into unchanged cash-risk zone did not complete",
        )
    if confirm > 0 and separation == 0:
        return (
            "RECLAIM_CONFIRM_REACHED_SEPARATION_NOT_REACHED",
            "POST_CONFIRM_SEPARATION",
            "post-confirm favorable-separation gate is suppressing entries",
        )
    if wait > 0 and confirm == 0:
        return (
            "RECLAIM_CONFIRM_QUALITY_BLOCK",
            top_wait,
            "closed-M1 reclaim quality did not produce POST_ZONE_REVERSAL_CONFIRM",
        )
    if penetration > 0 and wait == 0:
        return (
            "PENETRATION_REACHED_CONFIRM_EVALUATION_NOT_OBSERVED",
            "POST_ZONE_CONFIRM_WAIT",
            "inspect post-zone confirmation evaluation/telemetry transition",
        )
    if touch > 0 and penetration == 0:
        return (
            "ZONE_TOUCH_REACHED_PENETRATION_NOT_REACHED",
            "MICRO_ENTRY_PENETRATION",
            "price touched the cash-risk zone but did not satisfy penetration depth",
        )
    if micro > 0 and touch == 0:
        return (
            "MICRO_ENTRY_ARMED_ZONE_NOT_TOUCHED",
            "MICRO_ENTRY_ZONE_TOUCH",
            "micro-entry was armed but price never returned into the cash-risk zone",
        )
    if pending > 0 and micro == 0:
        return (
            "PENDING_ARM_REACHED_MICRO_ENTRY_NOT_ARMED",
            "MICRO_ENTRY_ARM",
            "initial candidate armed but microstructure/BOS transition did not arm entry",
        )
    return (
        "INITIAL_SETUP_OR_PENDING_ARM_BLOCK",
        "PENDING_ARM",
        "no pending-arm event observed; inspect upstream HTF/setup/BOS eligibility gates",
    )


def analyze(root: Path) -> dict:
    events_path = root / "V64_EVENTS.csv"
    deals_path = root / "V64_DEALS.csv"
    events = read_csv_snapshot(events_path)
    event_counts = Counter((row.get("event") or "").strip() for row in events)
    stage_counts = {name: int(event_counts.get(name, 0)) for name in FUNNEL_STAGES}
    aux_counts = {name: int(event_counts.get(name, 0)) for name in AUX_EVENTS}

    wait_reasons: Counter[str] = Counter()
    detail_counts: Counter[str] = Counter()
    for row in events:
        detail = (row.get("detail") or "").strip()
        event = (row.get("event") or "").strip()
        if detail:
            detail_counts[detail] += 1
        if event == "POST_ZONE_CONFIRM_WAIT":
            wait_reasons[normalize_reason(detail)] += 1

    closed = count_closed_deals(deals_path)
    classification, blocker, next_action = classify(stage_counts, wait_reasons, closed)

    return {
        "root": str(root),
        "events_file_present": events_path.is_file(),
        "deals_file_present": deals_path.is_file(),
        "events_rows": len(events),
        "closed_deals": closed,
        "stage_counts": stage_counts,
        "aux_event_counts": aux_counts,
        "classification": classification,
        "dominant_blocker": blocker,
        "next_action": next_action,
        "confirm_wait_reason_counts": dict(wait_reasons.most_common(30)),
        "top_event_counts": dict(event_counts.most_common(60)),
        "top_detail_counts": dict(detail_counts.most_common(40)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = analyze(args.root)
    print("V69_UPSTREAM_SOURCE_ROOT=" + result["root"])
    for name, value in result["stage_counts"].items():
        print(f"V69_UPSTREAM_{name}={value}")
    print(f"V69_UPSTREAM_CLOSED_DEALS={result['closed_deals']}")
    print("V69_UPSTREAM_CLASSIFICATION=" + result["classification"])
    print("V69_UPSTREAM_TOP_BLOCKER=" + result["dominant_blocker"])
    print("V69_UPSTREAM_NEXT_ACTION=" + result["next_action"])
    print("V69_UPSTREAM_CONFIRM_WAIT_REASONS=" + json.dumps(result["confirm_wait_reason_counts"], ensure_ascii=False, sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"V69_UPSTREAM_JSON={args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
