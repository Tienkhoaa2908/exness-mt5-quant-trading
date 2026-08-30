#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PREFIX = "V63"
WEEKLY_TRADE_GOAL = 3
WEEKLY_PROFIT_GOAL_USD = 6.0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except (TypeError, ValueError):
        return default


def i(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "") or default))
    except (TypeError, ValueError):
        return default


def pf(gp: float, gl: float) -> float:
    return gp / gl if gl > 1e-12 else (999.0 if gp > 1e-12 else 0.0)


def summarize_values(vals: list[float]) -> dict:
    wins = [x for x in vals if x > 1e-9]
    losses = [x for x in vals if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    return {
        "trades": len(vals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(vals) if vals else 0.0,
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": sum(vals),
        "profit_factor": pf(gp, gl),
        "avg_win_usd": gp / len(wins) if wins else 0.0,
        "avg_loss_usd": sum(losses) / len(losses) if losses else 0.0,
        "max_single_loss_usd": min(losses) if losses else 0.0,
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p10_usd": sum(1 for x in losses if x < -1.10 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
    }


def actual_summary(deals: list[dict[str, str]]) -> dict:
    all_net: list[float] = []
    exits: list[float] = []
    reasons = Counter()
    for row in deals:
        net = f(row, "profit") + f(row, "commission") + f(row, "swap") + f(row, "fee")
        all_net.append(net)
        if i(row, "entry") != 0:
            exits.append(net)
            reasons[str(i(row, "reason"))] += 1
    out = summarize_values(exits)
    running = peak = max_dd = 0.0
    for x in all_net:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    out.update({
        "all_deal_net_usd": sum(all_net),
        "entry_deals": sum(1 for row in deals if i(row, "entry") == 0),
        "exit_deals": len(exits),
        "max_realized_dd_usd": max_dd,
        "exit_reason_codes": dict(reasons),
    })
    return out


def shadow_summary(rows: list[dict[str, str]], col: str) -> dict:
    return summarize_values([f(row, col) for row in rows])


def parse_run_name(run_dir: Path) -> tuple[str, str, str]:
    name = run_dir.name.lower()
    direction = "LONG" if name.endswith("_long") else "SHORT" if name.endswith("_short") else ""
    if not direction:
        raise RuntimeError(f"V63 run directory must end in _long or _short: {run_dir}")
    stem = name.rsplit("_", 1)[0]
    if stem.startswith("benchmark_"):
        return "benchmark", stem.removeprefix("benchmark_"), direction
    if stem.startswith("bearish"):
        return "bearish", stem, direction
    raise RuntimeError(f"V63 unknown run label: {run_dir.name}")


def analyze_run(run_dir: Path) -> dict:
    kind, week, direction = parse_run_name(run_dir)
    evals = read_csv(run_dir / "V63_ENTRY_EVAL.csv")
    events = read_csv(run_dir / "V63_EVENTS.csv")
    deals = read_csv(run_dir / "V63_DEALS.csv")
    shadows = read_csv(run_dir / "V63_SHADOW_RR.csv")

    event_counts = Counter((row.get("event") or "") for row in events)
    pending_end = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "PENDING_END")
    risk_zone_wait = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "RISK_ZONE_WAIT")
    refine_wait = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "REFINE_WAIT")
    entry_veto = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "ENTRY_VETO")
    refined = [row for row in events if (row.get("event") or "") == "REFINED_ENTRY"]
    sent = [row for row in refined if (row.get("detail") or "") == "sent"]
    locks = [row for row in events if (row.get("event") or "") == "PROFIT_LOCK"]
    hard_loss = [row for row in events if (row.get("event") or "") == "HARD_CASH_LOSS"]
    preflight = [row for row in events if (row.get("event") or "") == "ORDER_PREFLIGHT"]

    allowed = 1 if direction == "LONG" else -1
    selected_allowed = [row for row in evals if i(row, "selected_direction") == allowed]
    selected_opposite = [row for row in evals if i(row, "selected_direction") == -allowed]
    feasible = [row for row in selected_allowed if i(row, "feasible") == 1]
    risk = [f(row, "risk_cash") for row in feasible if f(row, "risk_cash") > 0]
    stop_sources = Counter((row.get("stop_source") or "unknown") for row in feasible)

    return {
        "kind": kind,
        "week": week,
        "direction": direction,
        "run_dir": run_dir.name,
        "directional_rows_allowed": len(selected_allowed),
        "directional_rows_opposite_filtered": len(selected_opposite),
        "pending_arms": event_counts["PENDING_ARM"],
        "pending_refreshes": event_counts["PENDING_REFRESH"],
        "pending_end_reasons": dict(pending_end),
        "risk_zone_wait_reasons": dict(risk_zone_wait),
        "refine_wait_reasons": dict(refine_wait),
        "entry_veto_reasons": dict(entry_veto),
        "refined_entry_attempts": len(refined),
        "refined_entries_sent": len(sent),
        "feasible_eval_rows": len(feasible),
        "stop_source_counts": dict(stop_sources),
        "planned_risk_cash": {
            "min": min(risk) if risk else 0.0,
            "avg": sum(risk) / len(risk) if risk else 0.0,
            "max": max(risk) if risk else 0.0,
        },
        "profit_lock_modified": sum(1 for row in locks if (row.get("detail") or "") == "modified"),
        "profit_lock_failed": sum(1 for row in locks if (row.get("detail") or "") != "modified"),
        "hard_cash_loss_closed": sum(1 for row in hard_loss if (row.get("detail") or "") == "closed"),
        "hard_cash_loss_failed": sum(1 for row in hard_loss if (row.get("detail") or "") != "closed"),
        "order_preflight_blocks": len(preflight),
        "order_preflight_details": dict(Counter((row.get("detail") or "") for row in preflight)),
        "actual": actual_summary(deals),
        "shadow_2": shadow_summary(shadows, "result_cash_2"),
        "shadow_3": shadow_summary(shadows, "result_cash_3"),
        "shadow_4": shadow_summary(shadows, "result_cash_4"),
    }


def combine_actual(parts: list[dict]) -> dict:
    gp = sum(x["actual"]["gross_profit_usd"] for x in parts)
    gl = sum(x["actual"]["gross_loss_usd"] for x in parts)
    trades = sum(x["actual"]["trades"] for x in parts)
    wins = sum(x["actual"]["wins"] for x in parts)
    losses = sum(x["actual"]["losses"] for x in parts)
    max_loss = min((x["actual"]["max_single_loss_usd"] for x in parts), default=0.0)
    return {
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / trades if trades else 0.0,
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": gp - gl,
        "profit_factor": pf(gp, gl),
        "avg_win_usd": gp / wins if wins else 0.0,
        "avg_loss_usd": -gl / losses if losses else 0.0,
        "max_single_loss_usd": max_loss,
        "note": "sum_of_direction_isolated_passes_not_concurrent_portfolio_equity",
    }


def analyze(run_dirs: list[Path]) -> dict:
    runs = [analyze_run(rd) for rd in run_dirs]
    benchmark_runs = [x for x in runs if x["kind"] == "benchmark"]
    bearish_runs = [x for x in runs if x["kind"] == "bearish"]

    benchmark_groups: defaultdict[str, list[dict]] = defaultdict(list)
    for run in benchmark_runs:
        benchmark_groups[run["week"]].append(run)

    benchmark_weeks: dict[str, dict] = {}
    for week, parts in sorted(benchmark_groups.items()):
        long = next((x for x in parts if x["direction"] == "LONG"), None)
        short = next((x for x in parts if x["direction"] == "SHORT"), None)
        benchmark_weeks[week] = {
            "LONG": long,
            "SHORT": short,
            "combined_isolated_sum": combine_actual(parts),
        }

    benchmark_combined = combine_actual(benchmark_runs)
    weekly_combined = [block["combined_isolated_sum"] for _, block in sorted(benchmark_weeks.items())]
    benchmark_goals = {
        "weekly_trade_goal": WEEKLY_TRADE_GOAL,
        "weekly_profit_goal_usd": WEEKLY_PROFIT_GOAL_USD,
        "avg_trades_per_week": benchmark_combined["trades"] / len(weekly_combined) if weekly_combined else 0.0,
        "weeks_at_least_3_trades": sum(1 for x in weekly_combined if x["trades"] >= WEEKLY_TRADE_GOAL),
        "weeks_net_positive": sum(1 for x in weekly_combined if x["net_usd"] > 0),
        "weeks_net_at_least_5_usd": sum(1 for x in weekly_combined if x["net_usd"] >= 5.0),
        "weeks_net_at_least_6_usd": sum(1 for x in weekly_combined if x["net_usd"] >= WEEKLY_PROFIT_GOAL_USD),
        "trade_frequency_goal_met": bool(weekly_combined) and benchmark_combined["trades"] / len(weekly_combined) >= WEEKLY_TRADE_GOAL,
    }

    bearish_short = [x for x in bearish_runs if x["direction"] == "SHORT"]
    bearish_summary = {
        "actual": combine_actual(bearish_short),
        "signals": sum(x["directional_rows_allowed"] for x in bearish_short),
        "pending_arms": sum(x["pending_arms"] for x in bearish_short),
        "refined_entries": sum(x["refined_entries_sent"] for x in bearish_short),
        "short_execution_observed": sum(x["actual"]["trades"] for x in bearish_short) > 0,
        "avg_trades_per_selected_bearish_week": (
            sum(x["actual"]["trades"] for x in bearish_short) / len(bearish_short) if bearish_short else 0.0
        ),
    }

    return {
        "protocol": "four_fixed_august_weeks_long_short_plus_pnl_independent_bearish_short_validation",
        "runs": runs,
        "benchmark_weeks": benchmark_weeks,
        "benchmark": {
            "LONG": combine_actual([x for x in benchmark_runs if x["direction"] == "LONG"]),
            "SHORT": combine_actual([x for x in benchmark_runs if x["direction"] == "SHORT"]),
            "combined_isolated_sum": benchmark_combined,
            "goals": benchmark_goals,
        },
        "bearish_short_validation": bearish_summary,
    }


def fmt_actual(prefix: str, a: dict) -> str:
    return (
        f"{prefix} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
        f"win_rate={a['win_rate']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
        f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
        f"max_single_loss_usd={a['max_single_loss_usd']:.4f}"
    )


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V63_PROFIT_QUALITY_RISK_ZONE_ANALYSIS=1",
        "ACTUAL_TARGET_CASH=3.50",
        "PLANNED_RISK_BAND_CASH=0.60,1.05",
        "EMERGENCY_LOSS_CASH=1.10",
        "WEEKLY_RESEARCH_GOAL=about_3_quality_trades_and_6_usd_not_a_guarantee",
    ]

    for week, block in sorted(result["benchmark_weeks"].items()):
        for direction in ("LONG", "SHORT"):
            run = block.get(direction)
            if not run:
                continue
            lines.append(fmt_actual(f"BENCHMARK WEEK={week} DIR={direction}", run["actual"]))
            lines.append(
                f"BENCHMARK WEEK={week} DIR={direction} signals={run['directional_rows_allowed']} "
                f"arms={run['pending_arms']} refreshes={run['pending_refreshes']} refined_sent={run['refined_entries_sent']}"
            )
            lines.append(f"BENCHMARK WEEK={week} DIR={direction} ENTRY_VETO=" + json.dumps(run["entry_veto_reasons"], sort_keys=True))
            lines.append(f"BENCHMARK WEEK={week} DIR={direction} RISK_ZONE_WAIT=" + json.dumps(run["risk_zone_wait_reasons"], sort_keys=True))
            lines.append(f"BENCHMARK WEEK={week} DIR={direction} PENDING_END=" + json.dumps(run["pending_end_reasons"], sort_keys=True))
        lines.append(fmt_actual(f"BENCHMARK WEEK={week} COMBINED_ISOLATED_SUM", block["combined_isolated_sum"]))

    benchmark = result["benchmark"]
    lines.append(fmt_actual("BENCHMARK MONTH DIR=LONG", benchmark["LONG"]))
    lines.append(fmt_actual("BENCHMARK MONTH DIR=SHORT", benchmark["SHORT"]))
    lines.append(fmt_actual("BENCHMARK MONTH COMBINED_ISOLATED_SUM", benchmark["combined_isolated_sum"]))
    goals = benchmark["goals"]
    lines += [
        f"BENCHMARK_AVG_TRADES_PER_WEEK={goals['avg_trades_per_week']:.4f}",
        f"BENCHMARK_WEEKS_AT_LEAST_3_TRADES={goals['weeks_at_least_3_trades']}",
        f"BENCHMARK_WEEKS_NET_POSITIVE={goals['weeks_net_positive']}",
        f"BENCHMARK_WEEKS_NET_AT_LEAST_5_USD={goals['weeks_net_at_least_5_usd']}",
        f"BENCHMARK_WEEKS_NET_AT_LEAST_6_USD={goals['weeks_net_at_least_6_usd']}",
        f"BENCHMARK_TRADE_FREQUENCY_GOAL_MET={int(goals['trade_frequency_goal_met'])}",
    ]

    for run in [x for x in result["runs"] if x["kind"] == "bearish"]:
        lines.append(fmt_actual(f"BEARISH WINDOW={run['week']} DIR={run['direction']}", run["actual"]))
        lines.append(
            f"BEARISH WINDOW={run['week']} signals={run['directional_rows_allowed']} arms={run['pending_arms']} "
            f"refined_sent={run['refined_entries_sent']}"
        )
        lines.append(f"BEARISH WINDOW={run['week']} ENTRY_VETO=" + json.dumps(run["entry_veto_reasons"], sort_keys=True))
        lines.append(f"BEARISH WINDOW={run['week']} RISK_ZONE_WAIT=" + json.dumps(run["risk_zone_wait_reasons"], sort_keys=True))

    bearish = result["bearish_short_validation"]
    lines.append(fmt_actual("BEARISH SHORT TOTAL", bearish["actual"]))
    lines += [
        f"BEARISH_SHORT_SIGNALS={bearish['signals']}",
        f"BEARISH_SHORT_PENDING_ARMS={bearish['pending_arms']}",
        f"BEARISH_SHORT_REFINED_ENTRIES={bearish['refined_entries']}",
        f"BEARISH_SHORT_EXECUTION_OBSERVED={int(bearish['short_execution_observed'])}",
        f"BEARISH_SHORT_AVG_TRADES_PER_WEEK={bearish['avg_trades_per_selected_bearish_week']:.4f}",
        "COMBINED_NOTE=sum_of_direction_isolated_passes_not_concurrent_portfolio_equity",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    result = analyze(args.run_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.summary)
    print(args.summary.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
