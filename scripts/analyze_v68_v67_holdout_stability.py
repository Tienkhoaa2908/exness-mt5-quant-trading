#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

NOISE_VARIANTS = {
    "s110_t300": (1.10, 3.00),
    "s110_t350": (1.10, 3.50),
    "s110_t400": (1.10, 4.00),
    "s135_t300": (1.35, 3.00),
    "s135_t350": (1.35, 3.50),
    "s135_t400": (1.35, 4.00),
    "s160_t300": (1.60, 3.00),
    "s160_t350": (1.60, 3.50),
    "s160_t400": (1.60, 4.00),
}
STAGE_EVENTS = (
    "MICRO_ENTRY_ARM",
    "MICRO_ENTRY_ZONE_TOUCH",
    "MICRO_ENTRY_PENETRATION",
    "POST_ZONE_REVERSAL_CONFIRM",
    "POST_ZONE_ENTRY_READY",
    "POST_ZONE_CONFIRM_RESET",
    "MICRO_ENTRY_INVALIDATE",
    "MICRO_ENTRY_EXPIRE",
    "REFINED_ENTRY",
    "PROFIT_LOCK",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def num(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except (TypeError, ValueError):
        return default


def integer(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "") or default))
    except (TypeError, ValueError):
        return default


def profit_factor(gp: float, gl: float) -> float:
    if gl > 1e-12:
        return gp / gl
    return 999.0 if gp > 1e-12 else 0.0


def summarize_pnl(vals: list[float]) -> dict:
    wins = [x for x in vals if x > 1e-9]
    losses = [x for x in vals if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    running = peak = max_dd = 0.0
    for x in vals:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    return {
        "trades": len(vals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(vals) if vals else 0.0,
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": sum(vals),
        "profit_factor": profit_factor(gp, gl),
        "avg_win_usd": gp / len(wins) if wins else 0.0,
        "avg_loss_usd": sum(losses) / len(losses) if losses else 0.0,
        "max_single_loss_usd": min(losses) if losses else 0.0,
        "max_realized_dd_usd": max_dd,
    }


def parse_run_name(run_dir: Path) -> tuple[str, str]:
    name = run_dir.name.lower()
    if not name.startswith("holdout_"):
        raise RuntimeError(f"V68 unexpected run name {run_dir.name}")
    if name.endswith("_long"):
        direction = "LONG"
        stem = name[:-5]
    elif name.endswith("_short"):
        direction = "SHORT"
        stem = name[:-6]
    else:
        raise RuntimeError(f"V68 run direction missing in {run_dir.name}")
    month = stem.removeprefix("holdout_")
    return month, direction


def deal_metrics(rows: list[dict[str, str]]) -> tuple[dict, list[dict]]:
    entries = [r for r in rows if integer(r, "entry") == 0]
    exits = [r for r in rows if integer(r, "entry") != 0]
    vals = [num(r, "profit") + num(r, "commission") + num(r, "swap") + num(r, "fee") for r in exits]
    out = summarize_pnl(vals)
    fmt = "%Y.%m.%d %H:%M:%S"
    durations = []
    trade_rows = []
    for idx, ex in enumerate(exits):
        pnl = vals[idx]
        duration = None
        if idx < len(entries):
            try:
                duration = (datetime.strptime(ex["time"], fmt) - datetime.strptime(entries[idx]["time"], fmt)).total_seconds()
            except Exception:
                duration = None
        if duration is not None:
            durations.append((pnl, duration))
        trade_rows.append({
            "entry_time": entries[idx]["time"] if idx < len(entries) else "",
            "exit_time": ex.get("time", ""),
            "pnl_usd": pnl,
            "duration_seconds": duration,
            "exit_reason": integer(ex, "reason"),
        })
    loss_durations = [d for p, d in durations if p < -1e-9]
    win_durations = [d for p, d in durations if p > 1e-9]
    out["duration"] = {
        "losses_le_15s": sum(1 for d in loss_durations if d <= 15),
        "losses_le_30s": sum(1 for d in loss_durations if d <= 30),
        "losses_le_60s": sum(1 for d in loss_durations if d <= 60),
        "loss_median_seconds": statistics.median(loss_durations) if loss_durations else 0.0,
        "win_median_seconds": statistics.median(win_durations) if win_durations else 0.0,
    }
    return out, trade_rows


def noise_metrics(rows: list[dict[str, str]]) -> dict:
    out = {}
    for key, (stop, target) in NOISE_VARIANTS.items():
        states = [integer(r, key) for r in rows]
        wins = sum(1 for x in states if x == 1)
        losses = sum(1 for x in states if x == -1)
        unresolved = len(states) - wins - losses
        vals = [target] * wins + [-stop] * losses
        block = summarize_pnl(vals)
        block.update({
            "resolved": wins + losses,
            "unresolved": unresolved,
            "stop_then_later_target": sum(
                1 for r in rows if integer(r, key) == -1 and num(r, "max_pnl") >= target - 1e-9
            ),
        })
        out[key] = block
    return out


def analyze_run(run_dir: Path) -> dict:
    month, direction = parse_run_name(run_dir)
    deals = read_csv(run_dir / "V64_DEALS.csv")
    events = read_csv(run_dir / "V64_EVENTS.csv")
    noise = read_csv(run_dir / "V64_NOISE_SHADOW.csv")
    actual, trades = deal_metrics(deals)
    ec = Counter((r.get("event") or "") for r in events)
    details = Counter(
        f"{r.get('event','')}:{r.get('detail','')}"
        for r in events
        if (r.get("event") or "") in STAGE_EVENTS
    )
    return {
        "month": month,
        "direction": direction,
        "run_dir": run_dir.name,
        "actual": actual,
        "trades_detail": trades,
        "stage_events": {k: ec.get(k, 0) for k in STAGE_EVENTS},
        "stage_details": dict(sorted(details.items())),
        "noise_shadow": noise_metrics(noise),
        "noise_shadow_rows": len(noise),
    }


def max_negative_streak(vals: list[float]) -> int:
    best = cur = 0
    for x in vals:
        if x < -1e-9:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def lane_summary(runs: list[dict]) -> dict:
    ordered = sorted(runs, key=lambda x: x["month"])
    pnl = []
    all_trades = []
    totals = Counter()
    for r in ordered:
        pnl.extend(t["pnl_usd"] for t in r["trades_detail"])
        all_trades.extend(r["trades_detail"])
        totals.update(r["stage_events"])
    actual = summarize_pnl(pnl)
    losses = [t for t in all_trades if t["pnl_usd"] < -1e-9 and t["duration_seconds"] is not None]
    month_net = [r["actual"]["net_usd"] for r in ordered]
    active_months = [x for x in month_net if abs(x) > 1e-9]
    actual.update({
        "losses_le_15s": sum(1 for t in losses if t["duration_seconds"] <= 15),
        "losses_le_30s": sum(1 for t in losses if t["duration_seconds"] <= 30),
        "losses_le_60s": sum(1 for t in losses if t["duration_seconds"] <= 60),
    })
    return {
        "actual": actual,
        "months": len(ordered),
        "active_months": len(active_months),
        "positive_months": sum(1 for x in month_net if x > 1e-9),
        "negative_months": sum(1 for x in month_net if x < -1e-9),
        "flat_months": sum(1 for x in month_net if abs(x) <= 1e-9),
        "best_month_usd": max(month_net) if month_net else 0.0,
        "worst_month_usd": min(month_net) if month_net else 0.0,
        "median_month_usd": statistics.median(month_net) if month_net else 0.0,
        "monthly_stdev_usd": statistics.pstdev(month_net) if len(month_net) > 1 else 0.0,
        "max_consecutive_negative_months": max_negative_streak(month_net),
        "stage_events": dict(totals),
        "month_net_usd": {r["month"]: r["actual"]["net_usd"] for r in ordered},
    }


def analyze(run_dirs: list[Path]) -> dict:
    runs = [analyze_run(p) for p in run_dirs]
    long_runs = [r for r in runs if r["direction"] == "LONG"]
    short_runs = [r for r in runs if r["direction"] == "SHORT"]
    return {
        "protocol": "v68_v67_decision_logic_holdout_calendar_months_model4",
        "runs": runs,
        "lanes": {
            "LONG": lane_summary(long_runs),
            "SHORT": lane_summary(short_runs),
        },
        "interpretation": {
            "fixed_trade_count_quota": False,
            "fixed_weekly_profit_quota": False,
            "lanes_evaluated_independently": True,
            "primary_objective": "stable_positive_expectancy_consistency_drawdown_and_fast_loss_control",
        },
    }


def fmt_lane(name: str, lane: dict) -> str:
    a = lane["actual"]
    return (
        f"LANE={name} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
        f"win_rate={a['win_rate']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
        f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
        f"max_single_loss_usd={a['max_single_loss_usd']:.4f} max_realized_dd_usd={a['max_realized_dd_usd']:.4f} "
        f"positive_months={lane['positive_months']} negative_months={lane['negative_months']} flat_months={lane['flat_months']} "
        f"worst_month_usd={lane['worst_month_usd']:.4f} median_month_usd={lane['median_month_usd']:.4f} "
        f"losses_le_15s={a['losses_le_15s']} losses_le_30s={a['losses_le_30s']} losses_le_60s={a['losses_le_60s']}"
    )


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V68_V67_HOLDOUT_STABILITY_ANALYSIS=1",
        "V67_DECISION_LOGIC_CHANGED=0",
        "HOLDOUT_PERIOD=2025.09.01_to_2026.06.01",
        "MODEL4_PASSES=18",
        "FIXED_TRADE_COUNT_PROMOTION_QUOTA=0",
        "FIXED_WEEKLY_PROFIT_PROMOTION_QUOTA=0",
    ]
    for lane_name in ("LONG", "SHORT"):
        lane = result["lanes"][lane_name]
        lines.append(fmt_lane(lane_name, lane))
        lines.append(f"LANE={lane_name} MONTH_NET=" + json.dumps(lane["month_net_usd"], sort_keys=True))
        lines.append(f"LANE={lane_name} STAGE=" + json.dumps(lane["stage_events"], sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args = ap.parse_args()
    result = analyze(args.run_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.summary)
    print("V68_ANALYZER_PASS=1")
    print(f"V68_ANALYSIS={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
