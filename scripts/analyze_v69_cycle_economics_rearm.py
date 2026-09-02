#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DEVELOPMENT_MONTHS = tuple(f"2025-{m:02d}" for m in range(9, 13)) + tuple(f"2026-{m:02d}" for m in range(1, 6))
TERMINAL_EVENTS = {
    "ENTRY_VETO", "MICRO_ENTRY_INVALIDATE", "MICRO_ENTRY_EXPIRE", "MICRO_ENTRY_BLOCK",
    "ORDER_PREFLIGHT", "PENDING_END", "MICRO_ENTRY_END",
}
HARD_STRUCTURAL_TOKENS = (
    "invalidated_before_entry", "micro_structural_stop_breached", "invalid_micro_structural_stop",
)
TTL_TOKENS = ("expired_first_arm_ttl", "expired_first_micro_arm_ttl")
CONTEXT_QUALITY_TOKENS = (
    "direction_or_archetype_changed_before_rearm", "momentum_double_opposed",
    "stale_h4_h1_regime", "weak_trend_chop", "m15_efficiency_weak", "opposite_current_selector",
)
REARM_WINDOWS_MIN = (15, 30, 60, 180)


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


def deal_pnl(row: dict[str, str]) -> float:
    return (
        as_float(row, "profit") + as_float(row, "commission")
        + as_float(row, "swap") + as_float(row, "fee")
    )


def classify_terminal(terminal: str, sent: bool) -> str:
    if sent:
        return "SENT_ORDER"
    text = terminal or ""
    if any(token in text for token in HARD_STRUCTURAL_TOKENS):
        return "HARD_STRUCTURAL"
    if any(token in text for token in TTL_TOKENS):
        return "TTL_EXPIRY"
    if any(token in text for token in CONTEXT_QUALITY_TOKENS):
        return "CONTEXT_QUALITY"
    if not text:
        return "UNTERMINATED"
    return "OTHER"


def build_cycles(events: list[dict[str, str]]) -> list[dict]:
    ordered: list[tuple[datetime, dict[str, str]]] = []
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
                current["terminal_family"] = classify_terminal(current["terminal"], current["sent"])
                cycles.append(current)
            current = {
                "started": time,
                "archetype": detail or "UNKNOWN",
                "pending_reference": as_float(row, "v1"),
                "pending_raw_stop": as_float(row, "v2"),
                "sent": False,
                "sent_at": None,
                "terminal": "",
                "terminal_time": None,
                "pnl": None,
                "exit_time": None,
            }
        if current is None:
            continue
        if event == "REFINED_ENTRY" and detail == "sent":
            current["sent"] = True
            current["sent_at"] = time
        if event in TERMINAL_EVENTS and detail:
            current["terminal"] = f"{event}:{detail}"
            current["terminal_time"] = time
    if current is not None:
        current["terminal_family"] = classify_terminal(current["terminal"], current["sent"])
        cycles.append(current)
    return cycles


def exit_deals(rows: list[dict[str, str]]) -> list[dict]:
    out = []
    for row in rows:
        if as_int(row, "entry") == 0:
            continue
        time = parse_time(row.get("time", ""))
        if time is not None:
            out.append({"time": time, "pnl": deal_pnl(row)})
    out.sort(key=lambda item: item["time"])
    return out


def pair_sent_cycles_with_deals(cycles: list[dict], deals: list[dict]) -> None:
    sent = [cycle for cycle in cycles if cycle["sent"]]
    if len(sent) != len(deals):
        raise RuntimeError(f"sent-cycle/deal mismatch sent={len(sent)} exit_deals={len(deals)}")
    for cycle, deal in zip(sent, deals):
        sent_at = cycle["sent_at"]
        if sent_at is None:
            raise RuntimeError("sent cycle missing sent_at")
        if deal["time"] < sent_at:
            raise RuntimeError(
                f"deal precedes sent cycle sent_at={sent_at.isoformat()} deal={deal['time'].isoformat()}"
            )
        cycle["pnl"] = float(deal["pnl"])
        cycle["exit_time"] = deal["time"]


def pf_from_values(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 1e-9)
    gross_loss = -sum(value for value in values if value < -1e-9)
    return None if gross_loss <= 1e-12 else round(gross_profit / gross_loss, 6)


def summarize_economics(cycles: list[dict]) -> dict:
    values = [float(cycle["pnl"]) for cycle in cycles if cycle["pnl"] is not None]
    sent = [cycle for cycle in cycles if cycle["sent"]]
    return {
        "cycles": len(cycles),
        "sent": len(sent),
        "conversion_pct": round(100.0 * len(sent) / len(cycles), 4) if cycles else 0.0,
        "wins": sum(1 for value in values if value > 1e-9),
        "losses": sum(1 for value in values if value < -1e-9),
        "net_usd": round(sum(values), 8),
        "gross_profit_usd": round(sum(value for value in values if value > 1e-9), 8),
        "gross_loss_usd": round(-sum(value for value in values if value < -1e-9), 8),
        "profit_factor": pf_from_values(values),
        "terminal_families": dict(sorted(Counter(cycle["terminal_family"] for cycle in cycles).items())),
        "terminal_reasons": dict(sorted(Counter(cycle["terminal"] or "UNTERMINATED" for cycle in cycles).items())),
    }


def rearm_summary(cycles: list[dict]) -> dict:
    accum: dict[str, dict] = defaultdict(
        lambda: {
            "eligible_rejected": 0,
            "has_next_cycle": 0,
            "same_archetype_next": 0,
            "next_cycle_sent": 0,
            "next_cycle_wins": 0,
            "next_cycle_losses": 0,
            "next_cycle_net_usd": 0.0,
            **{f"rearm_within_{window}m": 0 for window in REARM_WINDOWS_MIN},
        }
    )
    for index, cycle in enumerate(cycles):
        if cycle["sent"] or cycle["terminal_time"] is None:
            continue
        bucket = accum[cycle["terminal_family"]]
        bucket["eligible_rejected"] += 1
        if index + 1 >= len(cycles):
            continue
        nxt = cycles[index + 1]
        delay = (nxt["started"] - cycle["terminal_time"]).total_seconds() / 60.0
        if delay < -1e-9:
            raise RuntimeError("cycle chronology invalid: next arm precedes prior terminal")
        bucket["has_next_cycle"] += 1
        if nxt["archetype"] == cycle["archetype"]:
            bucket["same_archetype_next"] += 1
        for window in REARM_WINDOWS_MIN:
            if delay <= window + 1e-9:
                bucket[f"rearm_within_{window}m"] += 1
        if nxt["sent"]:
            bucket["next_cycle_sent"] += 1
            pnl = float(nxt["pnl"] or 0.0)
            bucket["next_cycle_net_usd"] += pnl
            if pnl > 1e-9:
                bucket["next_cycle_wins"] += 1
            elif pnl < -1e-9:
                bucket["next_cycle_losses"] += 1
    merged = {}
    for family, bucket in sorted(accum.items()):
        bucket["next_cycle_net_usd"] = round(float(bucket["next_cycle_net_usd"]), 8)
        merged[family] = dict(bucket)
    return {
        "by_terminal_family": merged,
        "same_archetype_is_not_setup_identity": True,
        "cross_month_rearms_not_linked": True,
    }


def trade_transition_summary(cycles: list[dict]) -> dict:
    trades = [cycle for cycle in cycles if cycle["sent"] and cycle["pnl"] is not None]
    trades.sort(key=lambda cycle: cycle["sent_at"])
    counts = Counter()
    nets = defaultdict(float)
    previous_outcome = None
    for trade in trades:
        outcome = "W" if trade["pnl"] > 1e-9 else "L" if trade["pnl"] < -1e-9 else "F"
        if previous_outcome is not None:
            key = f"{previous_outcome}->{outcome}"
            counts[key] += 1
            nets[key] += float(trade["pnl"])
        previous_outcome = outcome
    return {
        "counts": dict(sorted(counts.items())),
        "destination_trade_net_usd": {key: round(value, 8) for key, value in sorted(nets.items())},
    }


def analyze_run(run_dir: Path) -> dict:
    cycles = build_cycles(read_csv(run_dir / "V64_EVENTS.csv"))
    pair_sent_cycles_with_deals(cycles, exit_deals(read_csv(run_dir / "V64_DEALS.csv")))
    archetypes = {
        archetype: summarize_economics([cycle for cycle in cycles if cycle["archetype"] == archetype])
        for archetype in sorted({cycle["archetype"] for cycle in cycles})
    }
    return {
        "run_dir": run_dir.name,
        "cycles": cycles,
        "economics": summarize_economics(cycles),
        "by_archetype": archetypes,
        "rearm": rearm_summary(cycles),
    }


def month_from_run(run_dir: Path) -> str | None:
    name = run_dir.name.lower()
    if not name.startswith("holdout_") or not name.endswith("_long"):
        return None
    token = name[len("holdout_") : -len("_long")]
    parts = token.split("_")
    return f"{parts[0]}-{parts[1]}" if len(parts) == 2 else None


def merge_rearm(blocks: list[dict]) -> dict:
    counts: dict[str, Counter] = defaultdict(Counter)
    nets: dict[str, float] = defaultdict(float)
    for block in blocks:
        for family, stats in block["rearm"]["by_terminal_family"].items():
            for key, value in stats.items():
                if key == "next_cycle_net_usd":
                    nets[family] += float(value)
                else:
                    counts[family][key] += int(value)
    merged = {}
    for family in sorted(set(counts) | set(nets)):
        row = dict(counts[family])
        row["next_cycle_net_usd"] = round(nets[family], 8)
        merged[family] = row
    return {
        "by_terminal_family": merged,
        "same_archetype_is_not_setup_identity": True,
        "cross_month_rearms_not_linked": True,
    }


def analyze(v69_root: Path) -> dict:
    blocks = []
    for run_dir in sorted(v69_root.glob("holdout_*_long")):
        month = month_from_run(run_dir)
        if month not in DEVELOPMENT_MONTHS:
            continue
        block = analyze_run(run_dir)
        block["month"] = month
        blocks.append(block)
    found = tuple(block["month"] for block in blocks)
    if found != DEVELOPMENT_MONTHS:
        raise RuntimeError(f"expected exact Sep-May V69 LONG development months, found={list(found)}")

    all_cycles = [cycle for block in blocks for cycle in block["cycles"]]
    overall = summarize_economics(all_cycles)
    archetypes = {
        archetype: summarize_economics([cycle for cycle in all_cycles if cycle["archetype"] == archetype])
        for archetype in sorted({cycle["archetype"] for cycle in all_cycles})
    }
    family_counts = Counter(cycle["terminal_family"] for cycle in all_cycles)
    hard = family_counts.get("HARD_STRUCTURAL", 0)
    candidate = family_counts.get("TTL_EXPIRY", 0) + family_counts.get("CONTEXT_QUALITY", 0)
    by_month = {
        block["month"]: {
            "economics": block["economics"],
            "by_archetype": block["by_archetype"],
            "rearm": block["rearm"],
        }
        for block in blocks
    }
    return {
        "protocol": "v69_cycle_economics_rearm_v1",
        "development_period": "2025-09_to_2026-05",
        "overall": overall,
        "terminal_family_counts": dict(sorted(family_counts.items())),
        "hard_structural_share_pct": round(100.0 * hard / len(all_cycles), 4) if all_cycles else 0.0,
        "ttl_plus_context_cycles": candidate,
        "ttl_plus_context_share_pct": round(100.0 * candidate / len(all_cycles), 4) if all_cycles else 0.0,
        "by_archetype": archetypes,
        "rearm": merge_rearm(blocks),
        "trade_transitions": trade_transition_summary(all_cycles),
        "by_month": by_month,
        "interpretation": {
            "hard_structural_failures_are_not_counterfactual_missed_wins": True,
            "ttl_and_context_are_research_candidates_not_proven_false_negatives": True,
            "same_archetype_rearm_does_not_prove_same_setup_identity": True,
            "reused_history_development_only": True,
            "independent_edge_evidence": False,
            "counterfactual_reject_edge_proven": False,
            "strategy_changed": False,
            "orders_sent": 0,
            "real_money_authorized": False,
            "short_enabled": False,
        },
    }


def write_outputs(result: dict, output: Path, summary: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        "V69_CYCLE_ECONOMICS_REARM=1",
        f"CYCLES={result['overall']['cycles']}",
        f"SENT={result['overall']['sent']}",
        f"NET_USD={result['overall']['net_usd']}",
        f"HARD_STRUCTURAL_SHARE_PCT={result['hard_structural_share_pct']}",
        f"TTL_PLUS_CONTEXT_CYCLES={result['ttl_plus_context_cycles']}",
        f"TTL_PLUS_CONTEXT_SHARE_PCT={result['ttl_plus_context_share_pct']}",
        "DEVELOPMENT_ONLY=1",
        "INDEPENDENT_EDGE_EVIDENCE=0",
        "COUNTERFACTUAL_REJECT_EDGE_PROVEN=0",
        "STRATEGY_CHANGED=0",
        "ORDERS_SENT=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
