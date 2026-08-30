#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "analyze_v66_post_bos_cash_zone.py"

STAGE3_EVENTS = (
    "MICRO_ENTRY_ARM",
    "MICRO_ENTRY_ZONE_TOUCH",
    "MICRO_ENTRY_PENETRATION",
    "POST_ZONE_CONFIRM_WAIT",
    "POST_ZONE_REVERSAL_CONFIRM",
    "POST_ZONE_CONFIRM_RESET",
    "POST_ZONE_ENTRY_READY",
    "MICRO_ENTRY_INVALIDATE",
    "MICRO_ENTRY_EXPIRE",
    "MICRO_ENTRY_BLOCK",
    "MICRO_ENTRY_END",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_time(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y.%m.%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def as_int(v: str | int | float | None) -> int:
    try:
        return int(float(v or 0))
    except (TypeError, ValueError):
        return 0


def as_float(v: str | int | float | None) -> float:
    try:
        return float(v or 0.0)
    except (TypeError, ValueError):
        return 0.0


def duration_summary(run_dir: Path) -> dict:
    rows = read_csv(run_dir / "V64_DEALS.csv")
    open_time: datetime | None = None
    records: list[tuple[float, float]] = []
    for row in rows:
        t = parse_time(row.get("time", ""))
        entry = as_int(row.get("entry"))
        if entry == 0:
            open_time = t
            continue
        if t is None or open_time is None:
            continue
        pnl = sum(as_float(row.get(k)) for k in ("profit", "commission", "swap", "fee"))
        seconds = max(0.0, (t - open_time).total_seconds())
        records.append((pnl, seconds))
        open_time = None

    losers = [sec for pnl, sec in records if pnl < -1e-9]
    winners = [sec for pnl, sec in records if pnl > 1e-9]
    return {
        "trades": len(records),
        "losses": len(losers),
        "wins": len(winners),
        "losses_le_15s": sum(sec <= 15 for sec in losers),
        "losses_le_30s": sum(sec <= 30 for sec in losers),
        "losses_le_60s": sum(sec <= 60 for sec in losers),
        "loss_median_seconds": statistics.median(losers) if losers else 0.0,
        "win_median_seconds": statistics.median(winners) if winners else 0.0,
    }


def lane_consistency(values: list[float]) -> dict:
    if not values:
        return {
            "weeks": 0,
            "positive_weeks": 0,
            "negative_weeks": 0,
            "net_usd": 0.0,
            "median_week_usd": 0.0,
            "worst_week_usd": 0.0,
            "best_week_usd": 0.0,
            "weekly_stdev_usd": 0.0,
        }
    return {
        "weeks": len(values),
        "positive_weeks": sum(v > 1e-9 for v in values),
        "negative_weeks": sum(v < -1e-9 for v in values),
        "net_usd": sum(values),
        "median_week_usd": statistics.median(values),
        "worst_week_usd": min(values),
        "best_week_usd": max(values),
        "weekly_stdev_usd": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


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
    stage_by_run: dict[str, dict] = {}
    stage_total = Counter()
    stage_details = Counter()
    duration_by_run: dict[str, dict] = {}

    for rd in args.run_dir:
        events = read_csv(rd / "V64_EVENTS.csv")
        ec = Counter((r.get("event") or "") for r in events)
        dc = Counter(
            f"{r.get('event','')}:{r.get('detail','')}"
            for r in events
            if (r.get("event") or "") in STAGE3_EVENTS
        )
        stage_by_run[rd.name] = {
            "events": {k: ec.get(k, 0) for k in STAGE3_EVENTS},
            "details": dict(sorted(dc.items())),
        }
        for k in STAGE3_EVENTS:
            stage_total[k] += ec.get(k, 0)
        stage_details.update(dc)
        duration_by_run[rd.name] = duration_summary(rd)

    benchmark = data.get("benchmark_weeks", {})
    long_weeks: list[float] = []
    short_weeks: list[float] = []
    for _, block in sorted(benchmark.items()):
        if block.get("LONG"):
            long_weeks.append(float(block["LONG"]["actual"]["net_usd"]))
        if block.get("SHORT"):
            short_weeks.append(float(block["SHORT"]["actual"]["net_usd"]))

    bearish_short_weeks: list[float] = []
    for run in data.get("runs", []):
        if run.get("kind") == "bearish" and run.get("direction") == "SHORT":
            bearish_short_weeks.append(float(run["actual"]["net_usd"]))

    legacy_goals = data.get("benchmark", {}).pop("goals", {})
    data["v67_post_zone_reclaim_quality"] = {
        "contract": {
            "fixed_lot": 0.01,
            "planned_risk_band_cash": [0.85, 1.10],
            "emergency_loss_cash": 1.20,
            "actual_target_cash": 3.50,
            "min_risk_spread_ratio": 4.0,
            "micro_entry_ttl_minutes": 30,
            "penetration_risk_cash": 0.92,
            "post_zone_reversal_confirmation": True,
            "first_zone_touch_can_send_order": False,
        },
        "research_objective": (
            "stable_positive_expectancy_and_loss_control; no fixed trades-per-week "
            "or fixed weekly-profit promotion quota"
        ),
        "stage3_by_run": stage_by_run,
        "stage3_total_events": dict(stage_total),
        "stage3_total_details": dict(sorted(stage_details.items())),
        "duration_by_run": duration_by_run,
        "consistency": {
            "benchmark_long": lane_consistency(long_weeks),
            "benchmark_short": lane_consistency(short_weeks),
            "bearish_short": lane_consistency(bearish_short_weeks),
        },
        "legacy_v64_frequency_profit_diagnostics_not_promotion_gate": legacy_goals,
    }
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    text = args.summary.read_text(encoding="utf-8", errors="replace")
    text = text.replace("V66_POST_BOS_CASH_ZONE_ANALYSIS", "V67_POST_ZONE_RECLAIM_QUALITY_ANALYSIS")
    text = text.replace("PLANNED_RISK_BAND_CASH=0.85,1.25", "PLANNED_RISK_BAND_CASH=0.85,1.10")
    text = text.replace(
        "WEEKLY_RESEARCH_GOAL=about_3_quality_trades_and_6_usd_not_a_guarantee\n",
        "",
    )
    text += "\nRESEARCH_OBJECTIVE=stable_positive_expectancy_and_loss_control_no_fixed_trade_or_weekly_profit_quota\n"
    text += "V67_STAGE3_TOTAL=" + json.dumps(dict(stage_total), sort_keys=True) + "\n"
    text += "V67_STAGE3_DETAILS=" + json.dumps(dict(sorted(stage_details.items())), sort_keys=True) + "\n"
    text += "V67_CONSISTENCY=" + json.dumps(data["v67_post_zone_reclaim_quality"]["consistency"], sort_keys=True) + "\n"
    text += "V67_DURATION=" + json.dumps(duration_by_run, sort_keys=True) + "\n"
    args.summary.write_text(text, encoding="utf-8")

    print("V67_ANALYZER_PASS=1")
    print("V67_STAGE3_TOTAL=" + json.dumps(dict(stage_total), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
