#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DEVELOPMENT_MONTHS = tuple(f"2025-{m:02d}" for m in range(9, 13)) + tuple(f"2026-{m:02d}" for m in range(1, 6))
STAGES = (
    "PENDING_ARM",
    "MICRO_ENTRY_ARM",
    "MICRO_ENTRY_ZONE_TOUCH",
    "MICRO_ENTRY_PENETRATION",
    "POST_ZONE_REVERSAL_CONFIRM",
    "POST_CONFIRM_SEPARATION",
    "POST_CONFIRM_RETEST_READY",
    "POST_CONFIRM_ENTRY_READY",
    "REFINED_ENTRY",
)
TERMINAL_EVENTS = {
    "ENTRY_VETO",
    "MICRO_ENTRY_INVALIDATE",
    "MICRO_ENTRY_EXPIRE",
    "MICRO_ENTRY_BLOCK",
    "ORDER_PREFLIGHT",
    "PENDING_END",
    "MICRO_ENTRY_END",
}


def parse_time(value: str) -> datetime | None:
    value = (value or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float((row.get(key) or "0").strip()))
    except (TypeError, ValueError):
        return 0


def as_float(row: dict[str, str], key: str) -> float:
    try:
        return float((row.get(key) or "0").strip())
    except (TypeError, ValueError):
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def selector_context(rows: list[dict[str, str]]) -> dict:
    points: list[datetime] = []
    by_month = Counter()
    for row in rows:
        time = parse_time(row.get("time", ""))
        if time is None or time.strftime("%Y-%m") not in DEVELOPMENT_MONTHS:
            continue
        if as_int(row, "selected_direction") != 1:
            continue
        points.append(time)
        by_month[time.strftime("%Y-%m")] += 1
    points = sorted(set(points))
    streaks = 0
    previous: datetime | None = None
    for time in points:
        if previous is None or time - previous != timedelta(minutes=15):
            streaks += 1
        previous = time
    return {
        "long_selected_rows": len(points),
        "long_selector_streaks": streaks,
        "by_month": {month: by_month.get(month, 0) for month in DEVELOPMENT_MONTHS},
        "note": "selector rows/streaks are context, not one-to-one tradable setups",
    }


def initial_eval_context(rows: list[dict[str, str]]) -> dict:
    initial = [
        row for row in rows
        if (row.get("decision_reason") or "").strip() == "long_edge"
        and as_int(row, "selected_direction") == 1
    ]
    rejects = Counter((row.get("reject_reason") or "").strip() or "EMPTY" for row in initial)
    pending = sum(count for reason, count in rejects.items() if reason.startswith("pending_"))
    return {
        "rows": len(initial),
        "reject_reasons": dict(sorted(rejects.items())),
        "pending_eval_rows": pending,
        "pre_pending_reject_rows": len(initial) - pending,
    }


def build_cycles(events: list[dict[str, str]]) -> list[dict]:
    ordered = []
    for row in events:
        time = parse_time(row.get("time", ""))
        if time is not None:
            ordered.append((time, row))
    ordered.sort(key=lambda item: item[0])
    cycles: list[dict] = []
    current: dict | None = None
    for time, row in ordered:
        event = (row.get("event") or "").strip()
        detail = (row.get("detail") or "").strip()
        if event == "PENDING_ARM":
            if current is not None:
                cycles.append(current)
            current = {
                "started": time,
                "reached": {stage: False for stage in STAGES},
                "terminal": "",
                "refined_entry_sent": False,
            }
        if current is None:
            continue
        if event in current["reached"]:
            current["reached"][event] = True
        if event == "REFINED_ENTRY" and detail == "sent":
            current["refined_entry_sent"] = True
        if event in TERMINAL_EVENTS and detail:
            current["terminal"] = f"{event}:{detail}"
    if current is not None:
        cycles.append(current)
    return cycles


def deals_context(rows: list[dict[str, str]]) -> dict:
    exits = [row for row in rows if as_int(row, "entry") != 0]
    vals = [
        as_float(row, "profit")
        + as_float(row, "commission")
        + as_float(row, "swap")
        + as_float(row, "fee")
        for row in exits
    ]
    return {
        "trades": len(exits),
        "wins": sum(1 for value in vals if value > 1e-9),
        "losses": sum(1 for value in vals if value < -1e-9),
        "net_usd": round(sum(vals), 8),
    }


def analyze_run(run_dir: Path) -> dict:
    entry_eval = read_csv(run_dir / "V64_ENTRY_EVAL.csv")
    events = read_csv(run_dir / "V64_EVENTS.csv")
    deals = read_csv(run_dir / "V64_DEALS.csv")
    cycles = build_cycles(events)
    stage_reach = Counter()
    terminals = Counter()
    for cycle in cycles:
        for stage, reached in cycle["reached"].items():
            if reached:
                stage_reach[stage] += 1
        if cycle["terminal"]:
            terminals[cycle["terminal"]] += 1
    event_counts = Counter((row.get("event") or "").strip() for row in events)
    event_details = Counter(
        f"{(row.get('event') or '').strip()}:{(row.get('detail') or '').strip()}"
        for row in events
        if (row.get("detail") or "").strip()
    )
    return {
        "run_dir": run_dir.name,
        "initial_eval": initial_eval_context(entry_eval),
        "pending_arm_cycles": len(cycles),
        "cycle_stage_reach": {stage: stage_reach.get(stage, 0) for stage in STAGES},
        "refined_entry_sent_cycles": sum(1 for cycle in cycles if cycle["refined_entry_sent"]),
        "terminal_reasons": dict(sorted(terminals.items())),
        "event_counts": dict(sorted(event_counts.items())),
        "event_details": dict(sorted(event_details.items())),
        "deals": deals_context(deals),
    }


def month_from_run(run_dir: Path) -> str | None:
    name = run_dir.name.lower()
    if not name.startswith("holdout_") or not name.endswith("_long"):
        return None
    token = name[len("holdout_") : -len("_long")]
    parts = token.split("_")
    if len(parts) != 2:
        return None
    return f"{parts[0]}-{parts[1]}"


def dominant_drop(stage_reach: dict[str, int]) -> dict:
    pairs = []
    for left, right in zip(STAGES, STAGES[1:]):
        a = stage_reach.get(left, 0)
        b = stage_reach.get(right, 0)
        lost = max(0, a - b)
        pairs.append({
            "from": left,
            "to": right,
            "from_cycles": a,
            "to_cycles": b,
            "lost_cycles": lost,
            "conversion_pct": round(100.0 * b / a, 4) if a else 0.0,
        })
    if not pairs:
        return {}
    return max(pairs, key=lambda row: (row["lost_cycles"], -row["conversion_pct"]))


def analyze(screen_csv: Path, v69_root: Path) -> dict:
    screen_rows = read_csv(screen_csv)
    if not screen_rows:
        raise RuntimeError(f"screen CSV has no rows: {screen_csv}")
    runs = []
    for run_dir in sorted(v69_root.glob("holdout_*_long")):
        month = month_from_run(run_dir)
        if month in DEVELOPMENT_MONTHS:
            block = analyze_run(run_dir)
            block["month"] = month
            runs.append(block)
    if len(runs) != len(DEVELOPMENT_MONTHS):
        found = [run["month"] for run in runs]
        raise RuntimeError(f"expected 9 V69 LONG development run dirs, found={found}")

    selector = selector_context(screen_rows)
    total_initial = Counter()
    total_events = Counter()
    total_terminals = Counter()
    total_stage = Counter()
    total_deals = Counter()
    sent_cycles = 0
    by_month = {}
    for run in runs:
        for key, value in run["initial_eval"]["reject_reasons"].items():
            total_initial[key] += value
        total_events.update(run["event_counts"])
        total_terminals.update(run["terminal_reasons"])
        total_stage.update(run["cycle_stage_reach"])
        sent_cycles += run["refined_entry_sent_cycles"]
        total_deals["trades"] += run["deals"]["trades"]
        total_deals["wins"] += run["deals"]["wins"]
        total_deals["losses"] += run["deals"]["losses"]
        total_deals["net_usd"] += run["deals"]["net_usd"]
        by_month[run["month"]] = {
            "selector_long_rows": selector["by_month"].get(run["month"], 0),
            "initial_eval": run["initial_eval"],
            "pending_arm_cycles": run["pending_arm_cycles"],
            "cycle_stage_reach": run["cycle_stage_reach"],
            "refined_entry_sent_cycles": run["refined_entry_sent_cycles"],
            "deals": run["deals"],
        }

    initial_rows = sum(run["initial_eval"]["rows"] for run in runs)
    pending_eval_rows = sum(run["initial_eval"]["pending_eval_rows"] for run in runs)
    cycles = total_stage.get("PENDING_ARM", 0)
    stage_dict = {stage: total_stage.get(stage, 0) for stage in STAGES}
    return {
        "protocol": "v69_downstream_long_funnel_recovery_v1",
        "development_period": "2025-09_to_2026-05",
        "selector_context": selector,
        "initial_eval": {
            "rows": initial_rows,
            "pending_eval_rows": pending_eval_rows,
            "pre_pending_reject_rows": initial_rows - pending_eval_rows,
            "reject_reasons": dict(sorted(total_initial.items())),
        },
        "pending_arm_cycles": cycles,
        "cycle_stage_reach": stage_dict,
        "refined_entry_sent_cycles": sent_cycles,
        "event_counts": dict(sorted(total_events.items())),
        "terminal_reasons": dict(sorted(total_terminals.items())),
        "deals": {
            "trades": total_deals["trades"],
            "wins": total_deals["wins"],
            "losses": total_deals["losses"],
            "net_usd": round(float(total_deals["net_usd"]), 8),
        },
        "dominant_cycle_drop": dominant_drop(stage_dict),
        "by_month": by_month,
        "interpretation": {
            "selector_rows_are_not_setup_count": True,
            "cycle_denominator_starts_at_pending_arm": True,
            "development_only_not_independent_edge_evidence": True,
            "counterfactual_quality_of_rejected_cycles_not_proven_here": True,
            "strategy_changed": False,
            "orders_sent": 0,
            "real_money_authorized": False,
            "short_enabled": False,
        },
    }


def write_outputs(result: dict, output: Path, summary: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    drop = result["dominant_cycle_drop"]
    lines = [
        "V69_DOWNSTREAM_LONG_FUNNEL_RECOVERY=1",
        f"SELECTOR_LONG_ROWS={result['selector_context']['long_selected_rows']}",
        f"SELECTOR_LONG_STREAKS={result['selector_context']['long_selector_streaks']}",
        f"INITIAL_EVAL_ROWS={result['initial_eval']['rows']}",
        f"PENDING_ARM_CYCLES={result['pending_arm_cycles']}",
        f"REFINED_ENTRY_SENT_CYCLES={result['refined_entry_sent_cycles']}",
        f"DEALS={result['deals']['trades']}",
        f"DOMINANT_DROP={drop.get('from','NONE')}->{drop.get('to','NONE')}",
        "DEVELOPMENT_ONLY=1",
        "INDEPENDENT_EDGE_EVIDENCE=0",
        "STRATEGY_CHANGED=0",
        "ORDERS_SENT=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
